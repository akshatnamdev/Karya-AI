"""
Invoice Routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user, get_business_scope
from app.models.user import User
from app.services.invoice_service import InvoiceService


router = APIRouter(prefix="/api/invoices", tags=["Invoices"])


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


@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope),
):
    return InvoiceService.get_invoice_detail(db, invoice_id, scope)