"""
Customer Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.core.dependencies import get_current_user, get_business_scope
from app.models.user import User
from app.models.customer import Customer
from app.models.business import Business
from app.services.customer_service import CustomerService


router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.get("")
def get_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    return CustomerService.get_all_customers(db, scope)


# ==================== Customer Joined Businesses ====================
# (Must be ABOVE /{customer_id} so FastAPI does not confuse it with an integer ID)
@router.get("/my-businesses")
def get_my_joined_businesses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all businesses that the logged-in customer is registered with.
    """
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != "customer":
        raise HTTPException(status_code=403, detail="Only customer accounts have joined businesses")

    user_email = (current_user.email or "").lower().strip()

    # Find all profiles matching user_id OR case-insensitive email
    profiles = db.query(Customer).filter(
        (Customer.user_id == current_user.id) |
        ((Customer.user_id == None) & (func.lower(Customer.email) == user_email))
    ).all()

    result = []
    updated_any = False

    for p in profiles:
        # Auto-link legacy records to user_id if missing
        if p.user_id is None:
            p.user_id = current_user.id
            updated_any = True

        b = db.query(Business).filter(Business.id == p.business_id).first()
        if b:
            result.append({
                "business_id": b.id,
                "business_name": b.name,
                "city": getattr(b, "city", None) or "India",
                "customer_id": p.id
            })

    if updated_any:
        try:
            db.commit()
        except Exception:
            db.rollback()

    return result


@router.get("/{customer_id}")
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    return CustomerService.get_customer_detail(db, customer_id, scope)