"""
Product Routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user, get_business_scope
from app.models.user import User
from app.services.product_service import ProductService


router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("")
def get_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    return ProductService.get_all_products(db, scope)


@router.get("/low-stock")
def get_low_stock(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    return ProductService.get_low_stock_products(db, scope)


@router.get("/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    return ProductService.get_product_detail(db, product_id, scope)