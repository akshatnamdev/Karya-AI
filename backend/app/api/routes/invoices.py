"""
Invoice Routes
"""
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.core.dependencies import get_current_user, get_business_scope
from app.models.user import User
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService


router = APIRouter(prefix="/api/invoices", tags=["Invoices"])


class InvoicePaymentRequest(BaseModel):
    amount: float = Field(gt=0)
    payment_method: Optional[str] = "manual"  # manual | cash | upi | razorpay (later)
    note: Optional[str] = None
    reference: Optional[str] = None  # razorpay payment id later

@router.get("")
def get_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    return InvoiceService.get_all_invoices(db, scope)


@router.get("/overdue")
def get_overdue_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    return InvoiceService.get_overdue_invoices(db, scope)

@router.post("/{invoice_id}/payments")
def record_invoice_payment(
    invoice_id: int,
    payload: InvoicePaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    """
    Business records full/partial payment.
    Razorpay can call the same InvoiceService.record_payment later.
    """
    return InvoiceService.record_payment(
        db=db,
        invoice_id=invoice_id,
        amount=payload.amount,
        scope=scope,
        payment_method=payload.payment_method or "manual",
        note=payload.note,
        reference=payload.reference,
    )

@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    return InvoiceService.get_invoice_detail(db, invoice_id, scope)

@router.delete("/{invoice_id}")
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    return InvoiceService.delete_invoice(db, invoice_id, scope)

@router.post("/{invoice_id}/payment-link")
def create_invoice_payment_link(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    from app.services.payment_service import PaymentService
    return PaymentService.create_payment_link(
        db=db,
        invoice_id=invoice_id,
        scope=scope,
        created_by_user_id=getattr(current_user, "id", None),
    )
    