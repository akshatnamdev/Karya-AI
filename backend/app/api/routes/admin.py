"""
Platform admin routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import require_platform_admin
from app.services.admin_service import AdminService
from app.models.user import User


router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/stats")
def platform_stats(db: Session = Depends(get_db), _: User = Depends(require_platform_admin)):
    return AdminService.platform_stats(db)


@router.get("/businesses")
def list_businesses(db: Session = Depends(get_db), _: User = Depends(require_platform_admin)):
    return AdminService.list_businesses(db)


@router.get("/businesses/{business_id}")
def business_detail(business_id: int, db: Session = Depends(get_db), _: User = Depends(require_platform_admin)):
    data = AdminService.business_detail(db, business_id)
    if not data:
        raise HTTPException(status_code=404, detail="Business not found")
    return data


@router.delete("/businesses/{business_id}")
def delete_business(business_id: int, db: Session = Depends(get_db), _: User = Depends(require_platform_admin)):
    return AdminService.delete_business(db, business_id)


@router.get("/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_platform_admin)):
    return AdminService.list_users(db)


@router.patch("/users/{user_id}/active")
def set_user_active(
    user_id: int,
    active: bool = Query(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin),
):
    return AdminService.toggle_user_active(db, user_id, active)

@router.patch("/businesses/{business_id}/active")
def set_business_active(
    business_id: int,
    active: bool = Query(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_platform_admin),
):
    return AdminService.toggle_business_active(db, business_id, active)