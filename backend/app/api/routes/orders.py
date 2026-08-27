"""
Order Routes
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user, get_business_scope
from app.models.user import User
from app.services.order_service import OrderService


router = APIRouter(prefix="/api/orders", tags=["Orders"])


class OrderItemInput(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreateRequest(BaseModel):
    customer_id: Optional[int] = None
    items: List[OrderItemInput]
    notes: Optional[str] = None
    source: Optional[str] = "manual"


@router.get("")
def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    return OrderService.get_all_orders(db, scope)


@router.get("/whatsapp")
def get_whatsapp_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    return OrderService.get_whatsapp_orders(db, scope)


@router.post("")
def create_order(
    payload: OrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    """
    Unified Place Order endpoint (BUSINESS & CUSTOMER).
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must include at least one item")

    role = scope.get("scope")
    business_id = scope.get("business_id")

    if not business_id:
        raise HTTPException(status_code=400, detail="Business context missing")

    if role == "business":
        if not payload.customer_id:
            raise HTTPException(
                status_code=400,
                detail="customer_id is required when placing an order as a business",
            )
        customer_id = payload.customer_id
        source = payload.source or "manual"

    elif role == "customer":
        customer_id = scope.get("customer_id")
        if not customer_id:
            raise HTTPException(status_code=400, detail="Customer context missing")
        source = payload.source or "manual"

    else:
        raise HTTPException(status_code=403, detail="Not allowed to place orders")

    items_data = [
        {"product_id": item.product_id, "quantity": item.quantity}
        for item in payload.items
    ]

    return OrderService.create_unified_order(
        db=db,
        business_id=business_id,
        customer_id=customer_id,
        items_data=items_data,
        source=source,
        notes=payload.notes,
    )


@router.get("/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    return OrderService.get_order_detail(db, order_id, scope)