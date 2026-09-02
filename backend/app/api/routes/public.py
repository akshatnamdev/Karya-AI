"""
Public routes - no auth required
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.business import Business

from app.db.database import get_db
from app.core.dependencies import get_current_user, get_business_scope
from app.models.user import User
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/public", tags=["Public"])

class CheckoutVerifyBody(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

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

@router.get("/pay/{token}")
def public_pay_session(token: str, db: Session = Depends(get_db)):
    return PaymentService.get_public_pay_session(db, token)


@router.get("/pay/{token}/status")
def public_pay_status(token: str, db: Session = Depends(get_db)):
    return PaymentService.get_link_status(db, token)


@router.post("/pay/{token}/verify")
def public_pay_verify(
    token: str,
    body: CheckoutVerifyBody,
    db: Session = Depends(get_db),
):
    return PaymentService.verify_checkout_payment(
        db=db,
        token=token,
        provider_order_id=body.razorpay_order_id,
        provider_payment_id=body.razorpay_payment_id,
        signature=body.razorpay_signature,
    )
