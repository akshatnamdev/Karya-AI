"""
Karya AI - Shared Dependencies
Common dependencies used across API routes
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.core.security import decode_access_token


# OAuth2 scheme - tells FastAPI where the login endpoint is
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the currently authenticated user from JWT token
    
    Usage:
        @router.get("/protected")
        def route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.name}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # Extract email
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    # Check if active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user