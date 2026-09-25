"""
Public routes - no auth required
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.business import Business
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/api/public", tags=["Public"])


class CheckoutVerifyBody(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.get("/businesses")
@router.get("/businesses/public")
def list_businesses(db: Session = Depends(get_db)):
    """
    Public endpoint for customer signup page dropdown.
    Returns all registered businesses with Name and City.
    """
    try:
        businesses = db.query(Business).order_by(Business.name.asc()).all()
        return [
            {
                "id": b.id,
                "name": b.name,
                "city": getattr(b, "city", None) or "India",
                "business_type": getattr(b, "business_type", None) or "General",
            }
            for b in businesses
        ]
    except Exception as e:
        print(f"[list_businesses error] {e}")
        return []


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