"""
Karya AI - Dashboard Routes
Endpoints: /api/dashboard/*
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.dashboard_service import DashboardService


router = APIRouter(prefix="/api/dashboard", tags=["📊 Dashboard"])


@router.get("")
def get_dashboard(db: Session = Depends(get_db)):
    """
    🎯 Get complete dashboard data
    
    Returns:
        - Business info
        - Summary metrics (revenue, customers, products, orders)
        - Smart alerts (overdue invoices, low stock, etc.)
    """
    return DashboardService.get_dashboard_data(db)