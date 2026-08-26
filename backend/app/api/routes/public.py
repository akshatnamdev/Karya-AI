"""
Public routes - no auth required
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.business import Business


router = APIRouter(prefix="/api/public", tags=["Public"])


@router.get("/businesses")
def list_businesses(db: Session = Depends(get_db)):
    """List businesses customers can join (minimal public info)"""
    businesses = db.query(Business).order_by(Business.name).all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "city": b.city,
            "business_type": b.business_type,
        }
        for b in businesses
    ]