
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.business import Business
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.schemas.auth import UserRegister, UserLogin

class AuthService:
    @staticmethod
    def register_user(db: Session, user_data: UserRegister) -> dict:
        if AuthService._email_exists(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered. Please login instead."
            )
        
        try:
            business = AuthService._create_business_if_needed(db, user_data)
            business_id = business.id if business else None
            new_user = AuthService._create_user(db, user_data, business_id)
            
            if business:
                business.owner_id = new_user.id
                db.commit() 
            
            token = AuthService._generate_token(new_user)
            return {
                "access_token": token,
                "token_type": "bearer",
                "expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
                "user": new_user  # Pydantic will convert this to UserResponse
            }
        
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )
    @staticmethod
    def login_user(db: Session, credentials: UserLogin) -> dict:
        # SQL: SELECT * FROM users WHERE email = 'akshat@karyaai.com';
        user = db.query(User).filter(User.email == credentials.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Contact support."
            )
        
        user.last_login = datetime.utcnow()
        db.commit()  # Save to database
        db.refresh(user)  # Reload from database
        token = AuthService._generate_token(user)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "user": user
        }
    
    # ==================== PRIVATE HELPER METHODS ====================
    # Note the underscore prefix (_) - these are for internal use only
    # Other code should NOT call these directly
    
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
            currency="INR",           # Default for Indian businesses
            timezone="Asia/Kolkata"    # Indian timezone
        )
        
        # Add to database session (but don't commit yet)
        db.add(business)
        
        # Flush = send to database but don't commit
        # This gives us the business.id without saving permanently
        db.flush()
        return business
    
    @staticmethod
    def _create_user(db: Session, user_data: UserRegister, business_id: int = None) -> User:
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            phone=user_data.phone,
            password_hash=hash_password(user_data.password),
            role="owner",           # First user is always the owner
            is_active=True,           # Active by default
            is_verified=False,      # Not verified (email verification comes later)
            business_id=business_id   # Link to business (or None)
        )
        db.add(new_user)
        db.commit()     
        db.refresh(new_user)  
        return new_user
    
    @staticmethod
    def _generate_token(user: User) -> str:
        return create_access_token(
            data={
                "sub": user.email,      # "sub" = subject (standard JWT claim)
                "user_id": user.id      # Custom claim for easy access
            }
        )