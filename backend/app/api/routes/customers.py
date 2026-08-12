"""
Karya AI - Customer Routes
Endpoints: /api/customers/*
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.customer_service import CustomerService


router = APIRouter(prefix="/api/customers", tags=["👥 Customers"])


@router.get("")
def get_customers(db: Session = Depends(get_db)):
    """👥 Get all customers"""
    return CustomerService.get_all_customers(db)


@router.get("/{customer_id}")
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """👤 Get customer detail with order history"""
    return CustomerService.get_customer_detail(db, customer_id)