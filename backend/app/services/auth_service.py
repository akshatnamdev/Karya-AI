"""
Authentication Service
Handles registration + login for all three role types
"""
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserRole
from app.models.business import Business
from app.models.customer import Customer
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.schemas.auth import UserRegister, UserLogin, CustomerRegister


class AuthService:
    """Handles authentication for all role types"""

    REDIRECT_MAP = {
        UserRole.PLATFORM_ADMIN: "/admin",
        UserRole.BUSINESS_OWNER: "/dashboard",
        UserRole.CUSTOMER: "/portal",
    }

    # ==================== BUSINESS OWNER REGISTRATION ====================

    @staticmethod
    def register_business_owner(db: Session, user_data: UserRegister) -> dict:
        if AuthService._email_exists(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered.",
            )

        try:
            business = AuthService._create_business_if_needed(db, user_data)
            business_id = business.id if business else None

            new_user = User(
                name=user_data.name,
                email=str(user_data.email).lower().strip(),
                phone=getattr(user_data, "phone", None),
                password_hash=hash_password(user_data.password),
                role=UserRole.BUSINESS_OWNER,
                is_active=True,
                is_verified=False,
                business_id=business_id,
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            if business is not None and hasattr(business, "owner_id"):
                business.owner_id = new_user.id
                db.commit()

            return AuthService._build_token_response(new_user)
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}",
            )

    # ==================== CUSTOMER REGISTER / JOIN (MULTI-BUSINESS) ====================

    @staticmethod
    def register_customer(db: Session, data: CustomerRegister) -> dict:
        """
        - New email → create User + Customer for selected business
        - Existing customer email + correct password → join NEW business
        - Already linked to that business → clear message to log in
        """
        if hasattr(data, "model_dump"):
            payload = data.model_dump()
        elif hasattr(data, "dict"):
            payload = data.dict()
        else:
            payload = dict(data)

        email = str(payload.get("email") or "").lower().strip()
        password = payload.get("password") or ""
        name = str(payload.get("name") or "").strip()
        phone = str(payload.get("phone") or "").strip() or None
        business_id = payload.get("business_id")

        if not email or not password or not name or business_id in (None, ""):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name, email, password, and business selection are required.",
            )

        try:
            business_id = int(business_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid business selected.",
            )

        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business not found.",
            )

        existing_user = db.query(User).filter(User.email == email).first()

        # ---------- EXISTING USER: join another business ----------
        if existing_user:
            role_val = (
                existing_user.role.value
                if hasattr(existing_user.role, "value")
                else str(existing_user.role)
            )
            if role_val not in (UserRole.CUSTOMER.value, "customer"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This email is registered as a business/admin account.",
                )

            if not verify_password(password, existing_user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "An account with this email already exists. "
                        "Enter your correct account password to join this business."
                    ),
                )

            already = (
                db.query(Customer)
                .filter(
                    Customer.user_id == existing_user.id,
                    Customer.business_id == business_id,
                )
                .first()
            )
            if already:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You are already registered with this business. Please log in.",
                )

            try:
                new_customer = Customer(
                    name=name or existing_user.name,
                    email=email,
                    phone=phone,
                    business_id=business_id,
                    user_id=existing_user.id,
                )
                db.add(new_customer)
                db.flush()

                existing_user.customer_id = new_customer.id
                existing_user.business_id = business_id
                db.commit()
                db.refresh(existing_user)
                return AuthService._build_token_response(existing_user)
            except IntegrityError:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Could not link to this business due to a database constraint. "
                        "Contact support if this continues."
                    ),
                )
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Could not link to new business: {str(e)}",
                )

        # ---------- NEW USER ----------
        try:
            new_user = User(
                name=name,
                email=email,
                phone=phone,
                password_hash=hash_password(password),
                role=UserRole.CUSTOMER,
                is_active=True,
                is_verified=False,
                business_id=business_id,
            )
            db.add(new_user)
            db.flush()

            new_customer = Customer(
                name=name,
                email=email,
                phone=phone,
                business_id=business_id,
                user_id=new_user.id,
            )
            db.add(new_customer)
            db.flush()

            new_user.customer_id = new_customer.id
            db.commit()
            db.refresh(new_user)
            return AuthService._build_token_response(new_user)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered.",
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}",
            )

    # ==================== LOGIN ====================

    @staticmethod
    def login_user(db: Session, credentials: UserLogin) -> dict:
        email = str(getattr(credentials, "email", "") or "").lower().strip()
        password = getattr(credentials, "password", "") or ""

        user = db.query(User).filter(User.email == email).first()

        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )

        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return AuthService._build_token_response(user)

    login = login_user

    # ==================== PLATFORM ADMIN ====================

    @staticmethod
    def create_platform_admin(db: Session, name: str, email: str, password: str) -> User:
        if AuthService._email_exists(db, email):
            raise ValueError("Email already exists")
        admin = User(
            name=name,
            email=email.lower().strip(),
            password_hash=hash_password(password),
            role=UserRole.PLATFORM_ADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin

    # ==================== HELPERS ====================

    @staticmethod
    def _email_exists(db: Session, email: str) -> bool:
        return (
            db.query(User)
            .filter(User.email == str(email).lower().strip())
            .first()
            is not None
        )

    @staticmethod
    def _create_business_if_needed(db: Session, user_data: UserRegister):
        if not getattr(user_data, "business_name", None):
            return None
        business = Business(
            name=user_data.business_name,
            business_type=getattr(user_data, "business_type", None) or "wholesaler",
            phone=getattr(user_data, "phone", None),
            city=getattr(user_data, "city", None) or None,
            currency="INR",
            timezone="Asia/Kolkata",
        )
        db.add(business)
        db.flush()
        return business

    @staticmethod
    def _build_token_response(user: User) -> dict:
        role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
        token = create_access_token(
            data={
                "sub": user.email,
                "user_id": user.id,
                "role": role_value,
                "business_id": user.business_id,
                "customer_id": user.customer_id,
            }
        )

        if role_value == "customer":
            redirect_to = "/portal"
        elif role_value == "platform_admin":
            redirect_to = "/admin"
        else:
            redirect_to = "/dashboard"

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in_minutes": getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60),
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": role_value,
                "is_active": getattr(user, "is_active", True),
                "is_verified": getattr(user, "is_verified", False),
                "business_id": user.business_id,
                "customer_id": user.customer_id,
            },
            "redirect_to": redirect_to,
        }