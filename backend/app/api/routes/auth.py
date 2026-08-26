"""
Authentication Routes
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, CustomerRegister, Token, UserResponse
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_business(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new business owner account"""
    return AuthService.register_business_owner(db, user_data)


@router.post("/register-customer", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_customer(data: CustomerRegister, db: Session = Depends(get_db)):
    """Register as a customer of an existing business"""
    return AuthService.register_customer(db, data)


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Universal login. Response includes redirect_to for the frontend."""
    return AuthService.login_user(db, credentials)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Current user info"""
    return current_user