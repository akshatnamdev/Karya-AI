"""
Shared API Dependencies
Role-based access control
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, UserRole
from app.core.security import decode_access_token


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate JWT, return User object"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user

# ==================== ROLE GUARDS ====================



def _get_role_value(role) -> str:
    """Helper to safely extract string value from Enum or string"""
    return role.value if hasattr(role, 'value') else str(role)


def require_platform_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Only platform admins can access"""
    # Force convert to string and handle Enum values safely
    role_str = str(current_user.role.value if hasattr(current_user.role, 'value') else current_user.role)
    
    # We must check against the exact string value
    if role_str != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Platform admin access required. Found role: {role_str}"
        )
    return current_user


def require_business_owner(
    current_user: User = Depends(get_current_user)
) -> User:
    """Only business owners can access"""
    if _get_role_value(current_user.role) != UserRole.BUSINESS_OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business owner access required"
        )
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No business associated with account"
        )
    return current_user


def require_customer(
    current_user: User = Depends(get_current_user)
) -> User:
    """Only customer accounts can access"""
    if _get_role_value(current_user.role) != UserRole.CUSTOMER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer access required"
        )
    if not current_user.customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No customer profile associated"
        )
    return current_user


def get_business_scope(
    current_user: User = Depends(get_current_user)
) -> dict:
    """Returns query scope based on role."""
    role_val = _get_role_value(current_user.role)
    
    if role_val == UserRole.PLATFORM_ADMIN.value:
        return {"scope": "all", "business_id": None, "customer_id": None}
    
    if role_val == UserRole.BUSINESS_OWNER.value:
        return {
            "scope": "business",
            "business_id": current_user.business_id,
            "customer_id": None
        }
    
    if role_val == UserRole.CUSTOMER.value:
        return {
            "scope": "customer",
            "business_id": current_user.business_id,
            "customer_id": current_user.customer_id
        }
    
    raise HTTPException(status_code=403, detail="Invalid role scope")