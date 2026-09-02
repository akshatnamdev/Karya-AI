"""
Payment routes — auth link create + public pay + Razorpay webhook
"""
from typing import Optional

from fastapi import APIRouter, Depends, Request, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user, get_business_scope
from app.models.user import User
from app.services.payment_service import PaymentService

router = APIRouter(tags=["Payments"])


class CheckoutVerifyBody(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.get("/api/payments/status")
def payments_config_status(current_user: User = Depends(get_current_user)):
    return PaymentService.provider_status()



@router.post("/api/webhooks/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
):
    body = await request.body()
    if not x_razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing X-Razorpay-Signature")
    return PaymentService.handle_razorpay_webhook(
        db=db,
        body=body,
        signature_header=x_razorpay_signature,
    )