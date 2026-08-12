"""
Karya AI - Product Routes
Endpoints: /api/products/*
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.product_service import ProductService


router = APIRouter(prefix="/api/products", tags=["📦 Products & Inventory"])


@router.get("")
def get_products(db: Session = Depends(get_db)):
    """📦 Get all products with stock info"""
    return ProductService.get_all_products(db)


@router.get("/low-stock")
def get_low_stock(db: Session = Depends(get_db)):
    """⚠️ Get products that need reordering (Inventory Intelligence)"""
    return ProductService.get_low_stock_products(db)


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    """📦 Get single product detail"""
    return ProductService.get_product_detail(db, product_id)