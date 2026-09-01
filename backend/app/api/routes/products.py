"""
Product Routes
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user, get_business_scope
from app.models.user import User
from app.services.product_service import ProductService


router = APIRouter(prefix="/api/products", tags=["Products"])


class ProductCreateRequest(BaseModel):
    name: str
    selling_price: float
    sku: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    cost_price: Optional[float] = 0
    mrp: Optional[float] = None
    gst_rate: Optional[float] = 18
    hsn_code: Optional[str] = None
    unit: Optional[str] = "pcs"
    initial_stock: Optional[int] = 0
    reorder_level: Optional[int] = 10
    reorder_quantity: Optional[int] = 50
    warehouse_location: Optional[str] = None
    is_active: Optional[bool] = True


class StockUpdateRequest(BaseModel):
    mode: str = "add"          # set | add | remove
    quantity: int
    reason: Optional[str] = None

@router.patch("/{product_id}/stock")
def update_product_stock(
    product_id: int,
    payload: StockUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    """
    BUSINESS: Update stock (set / add / remove)
    """
    if scope.get("scope") != "business":
        raise HTTPException(status_code=403, detail="Only business users can update stock")

    business_id = scope.get("business_id")
    if not business_id:
        raise HTTPException(status_code=400, detail="Business context missing")

    return ProductService.update_stock(
        db=db,
        business_id=business_id,
        product_id=product_id,
        mode=payload.mode,
        quantity=payload.quantity,
        reason=payload.reason,
    )

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


@router.post("")
def create_product(
    payload: ProductCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    """
    BUSINESS: Add Product Manually
    """
    if scope.get("scope") != "business":
        raise HTTPException(status_code=403, detail="Only business users can create products")

    business_id = scope.get("business_id")
    if not business_id:
        raise HTTPException(status_code=400, detail="Business context missing")

    # Supports both Pydantic v1 & v2
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()

    return ProductService.create_product(
        db=db,
        business_id=business_id,
        product_data=data,
    )


@router.get("/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    return ProductService.get_product_detail(db, product_id, scope)