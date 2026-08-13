from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/api/auth", 
    tags=["🔐 Authentication"]
)


# ==================== REGISTER ====================

@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED
)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """🆕 Register a new user account"""
    return AuthService.register_user(db, user_data)


# ==================== LOGIN ====================

@router.post(
    "/login",
    response_model=Token
)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """🔑 Login with email and password"""
    return AuthService.login_user(db, credentials)


# ==================== GET CURRENT USER ====================

@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(current_user: User = Depends(get_current_user)):
    """👤 Get currently authenticated user"""
    return current_user


# ==================== PROTECTED TEST ====================

@router.get("/protected-test")
def protected_test(current_user: User = Depends(get_current_user)):
    """🛡️ Test protected endpoint"""
    return {
        "message": f"🎉 Hello {current_user.name}! You're authenticated!",
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "business_id": current_user.business_id,
        "authenticated": True
    }