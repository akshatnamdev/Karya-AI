"""
Karya AI - Invoice Routes
Endpoints: /api/invoices/*
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.invoice_service import InvoiceService


router = APIRouter(prefix="/api/invoices", tags=["💰 Invoices & Payments"])


@router.get("")
def get_invoices(db: Session = Depends(get_db)):
    """💰 Get all invoices (sorted by newest first)"""
    return InvoiceService.get_all_invoices(db)


@router.get("/overdue")
def get_overdue_invoices(db: Session = Depends(get_db)):
    """
    🔴 PAYMENT INTELLIGENCE - Get overdue invoices
    
    Returns overdue invoices with:
    - Auto-drafted Hinglish reminder messages
    - Days overdue calculation
    - Urgency levels
    - Ready-to-send WhatsApp reminders
    """
    return InvoiceService.get_overdue_invoices(db)


@router.get("/{invoice_id}")
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """📋 Get single invoice detail"""
    return InvoiceService.get_invoice_detail(db, invoice_id)