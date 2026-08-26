"""
Authentication Service
Handles registration + login for all three role types
"""
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.business import Business
from app.models.customer import Customer
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.schemas.auth import UserRegister, UserLogin, CustomerRegister


class AuthService:
    """Handles authentication for all role types"""
    
    # Redirect paths per role
    REDIRECT_MAP = {
        UserRole.PLATFORM_ADMIN: "/admin",
        UserRole.BUSINESS_OWNER: "/dashboard",
        UserRole.CUSTOMER: "/portal",
    }
    
    # ==================== BUSINESS OWNER REGISTRATION ====================
    
    @staticmethod
    def register_business_owner(db: Session, user_data: UserRegister) -> dict:
        """Register a new business owner + their business"""
        
        if AuthService._email_exists(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered."
            )
        
        try:
            business = AuthService._create_business_if_needed(db, user_data)
            business_id = business.id if business else None
            
            new_user = User(
                name=user_data.name,
                email=user_data.email,
                phone=user_data.phone,
                password_hash=hash_password(user_data.password),
                role=UserRole.BUSINESS_OWNER,
                is_active=True,
                is_verified=False,
                business_id=business_id
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            if business:
                business.owner_id = new_user.id
                db.commit()
            
            return AuthService._build_token_response(new_user)
        
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )
    
    # ==================== CUSTOMER REGISTRATION ====================
    
    @staticmethod
    def register_customer(db: Session, data: CustomerRegister) -> dict:
        """Register a new customer to a specific business"""
        
        if AuthService._email_exists(db, data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered."
            )
        
        business = db.query(Business).filter(Business.id == data.business_id).first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )
        
        try:
            customer = Customer(
                name=data.name,
                phone=data.phone,
                whatsapp_number=data.phone,
                email=data.email,
                customer_type="retail",
                business_id=data.business_id,
            )
            db.add(customer)
            db.flush()
            
            new_user = User(
                name=data.name,
                email=data.email,
                phone=data.phone,
                password_hash=hash_password(data.password),
                role=UserRole.CUSTOMER,
                is_active=True,
                is_verified=False,
                business_id=data.business_id,
                customer_id=customer.id,
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            return AuthService._build_token_response(new_user)
        
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Customer registration failed: {str(e)}"
            )
    
    # ==================== LOGIN (all roles use same endpoint) ====================
    
    @staticmethod
    def login_user(db: Session, credentials: UserLogin) -> dict:
        """Universal login - routes to correct dashboard based on role"""
        
        user = db.query(User).filter(User.email == credentials.email).first()
        
        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        return AuthService._build_token_response(user)
    
    # ==================== PLATFORM ADMIN CREATION (special) ====================
    
    @staticmethod
    def create_platform_admin(db: Session, name: str, email: str, password: str) -> User:
        """
        Create a platform admin. Only called from CLI/seed script.
        Not exposed via public API.
        """
        if AuthService._email_exists(db, email):
            raise ValueError("Email already exists")
        
        admin = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.PLATFORM_ADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
    
    # ==================== PRIVATE HELPERS ====================
    
    @staticmethod
    def _email_exists(db: Session, email: str) -> bool:
        return db.query(User).filter(User.email == email).first() is not None
    
    @staticmethod
    def _create_business_if_needed(db: Session, user_data: UserRegister):
        if not user_data.business_name:
            return None
        
        business = Business(
            name=user_data.business_name,
            business_type=user_data.business_type or "wholesaler",
            phone=user_data.phone,
            city=getattr(user_data, 'city', None) or None   , # Added city handling
            currency="INR",
            timezone="Asia/Kolkata"
        )
        db.add(business)
        db.flush()
        return business

        
    @staticmethod
    def _build_token_response(user: User) -> dict:
        """Build standard token response with role-based redirect"""
        token = create_access_token(data={
            "sub": user.email,
            "user_id": user.id,
            "role": user.role.value if hasattr(user.role, 'value') else user.role,
            "business_id": user.business_id,
            "customer_id": user.customer_id,
        })
        
        role_value = user.role.value if hasattr(user.role, 'value') else user.role
        redirect_to = AuthService.REDIRECT_MAP.get(user.role, "/dashboard")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "user": user,
            "redirect_to": redirect_to,
        }