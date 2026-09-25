"""
Shared API Dependencies
Role-based access control and scope resolution
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.business import Business
from app.models.customer import Customer
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
    role_str = str(current_user.role.value if hasattr(current_user.role, 'value') else current_user.role)
    
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_business_id: Optional[str] = Header(None, alias="X-Business-Id")
) -> dict:
    role = current_user.role
    role_str = role.value if hasattr(role, "value") else str(role)

    if role_str == "business_owner":
        # Direct lookup using business_id stored on the User record
        biz_id = current_user.business_id
        if not biz_id:
            b = db.query(Business).filter(Business.owner_id == current_user.id).first()
            biz_id = b.id if b else None

        return {
            "scope": "business",
            "business_id": biz_id,
            "customer_id": None
        }

    elif role_str == "customer":
        user_email = (current_user.email or "").lower().strip()
        
        q = db.query(Customer).filter(
            (Customer.user_id == current_user.id) |
            ((Customer.user_id == None) & (func.lower(Customer.email) == user_email))
        )

        # 1. If active business header passed, target that business profile
        if x_business_id and str(x_business_id).isdigit():
            target_id = int(x_business_id)
            cust = q.filter(Customer.business_id == target_id).first()
            if cust:
                return {
                    "scope": "customer",
                    "business_id": cust.business_id,
                    "customer_id": cust.id
                }

        # 2. Fallback to first joined business
        cust = q.first()
        if not cust:
            raise HTTPException(
                status_code=404, 
                detail="No business profiles found for this customer account."
            )

        return {
            "scope": "customer",
            "business_id": cust.business_id,
            "customer_id": cust.id
        }

    elif role_str == "platform_admin":
        return {"scope": "all", "business_id": None, "customer_id": None}

    raise HTTPException(status_code=403, detail="Invalid role scope")