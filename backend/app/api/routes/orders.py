"""
Order Routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user, get_business_scope
from app.models.user import User
from app.services.order_service import OrderService


router = APIRouter(prefix="/api/orders", tags=["Orders"])


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


@router.get("/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    return OrderService.get_order_detail(db, order_id, scope)