"""
Dashboard Routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user, get_business_scope
from app.models.user import User
from app.services.dashboard_service import DashboardService


router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    """Dashboard data scoped to user's role"""
    return DashboardService.get_dashboard_data(db, scope)