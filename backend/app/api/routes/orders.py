"""
Karya AI - Order Routes
Endpoints: /api/orders/*
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.order_service import OrderService


router = APIRouter(prefix="/api/orders", tags=["🛒 Orders"])


@router.get("")
def get_orders(db: Session = Depends(get_db)):
    """🛒 Get all orders (sorted by newest first)"""
    return OrderService.get_all_orders(db)


@router.get("/whatsapp")
def get_whatsapp_orders(db: Session = Depends(get_db)):
    """📱 Get orders that came from WhatsApp"""
    return OrderService.get_whatsapp_orders(db)


@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    """📋 Get single order detail with items"""
    return OrderService.get_order_detail(db, order_id)