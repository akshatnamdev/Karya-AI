"""
Karya AI - Invoice Service
Business logic for invoices and payment intelligence
"""
from datetime import date
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.order import Order
from app.models.customer import Customer
from app.utils.formatters import safe_float, safe_iso, calculate_days_between


class InvoiceService:
    """Handles all invoice-related business logic and payment intelligence"""
    
    # Status emoji mapping for visual clarity
    STATUS_EMOJIS = {
        "paid": "✅",
        "overdue": "🔴",
        "partially_paid": "🟡",
        "draft": "📝",
        "sent": "📤",
        "cancelled": "❌",
    }
    
    @staticmethod
    def get_all_invoices(db: Session) -> list:
        """
        Get all invoices sorted by most recent
        
        Returns:
            list: List of invoices with customer info and status
        """
        invoices = db.query(Invoice).order_by(Invoice.invoice_date.desc()).all()
        return [InvoiceService._format_invoice(inv, db) for inv in invoices]
    
    @staticmethod
    def get_invoice_detail(db: Session, invoice_id: int) -> dict:
        """
        Get detailed invoice info
        
        Args:
            invoice_id: ID of the invoice
            
        Returns:
            dict: Complete invoice details
            
        Raises:
            HTTPException: 404 if invoice not found
        """
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {invoice_id} not found"
            )
        
        return InvoiceService._format_invoice_detail(invoice, db)
    
    @staticmethod
    def get_overdue_invoices(db: Session) -> dict:
        """
        💰 PAYMENT INTELLIGENCE - Get overdue invoices with auto-drafted Hindi reminders!
        
        This is Karya AI's killer feature - not just showing overdue payments,
        but generating personalized Hinglish reminder messages ready to send.
        
        Returns:
            dict: Overdue invoices with total amount and suggested reminders
        """
        overdue = db.query(Invoice).filter(Invoice.status == "overdue").all()
        
        # Calculate total overdue amount
        total_amount = sum(safe_float(inv.balance_amount) for inv in overdue)
        
        # Format each overdue invoice with reminder message
        invoices_data = [
            InvoiceService._format_overdue_invoice(inv, db) 
            for inv in overdue
        ]
        
        return {
            "count": len(overdue),
            "total_overdue_amount": total_amount,
            "alert": InvoiceService._get_overdue_alert_message(len(overdue), total_amount),
            "invoices": invoices_data
        }
    
    # ==================== PRIVATE HELPER METHODS ====================
    
    @staticmethod
    def _format_invoice(invoice: Invoice, db: Session) -> dict:
        """Format invoice for list view"""
        # Get related order and customer
        order = db.query(Order).filter(Order.id == invoice.order_id).first()
        customer = None
        if order:
            customer = db.query(Customer).filter(
                Customer.id == order.customer_id
            ).first()
        
        return {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "status": invoice.status,
            "status_emoji": InvoiceService.STATUS_EMOJIS.get(invoice.status, "❓"),
            "customer": customer.name if customer else "Unknown",
            "customer_phone": customer.phone if customer else None,
            "total": safe_float(invoice.total_amount),
            "paid": safe_float(invoice.paid_amount),
            "balance": safe_float(invoice.balance_amount),
            "invoice_date": safe_iso(invoice.invoice_date),
            "due_date": safe_iso(invoice.due_date),
            "paid_date": safe_iso(invoice.paid_date),
            "is_overdue": invoice.status == "overdue",
        }
    
    @staticmethod
    def _format_invoice_detail(invoice: Invoice, db: Session) -> dict:
        """Format invoice for detail view"""
        # Get related order and customer
        order = db.query(Order).filter(Order.id == invoice.order_id).first()
        customer = None
        if order:
            customer = db.query(Customer).filter(
                Customer.id == order.customer_id
            ).first()
        
        return {
            "invoice": {
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "status": invoice.status,
                "status_emoji": InvoiceService.STATUS_EMOJIS.get(invoice.status, "❓"),
                "subtotal": safe_float(invoice.subtotal),
                "tax": safe_float(invoice.tax_amount),
                "discount": safe_float(invoice.discount_amount),
                "total": safe_float(invoice.total_amount),
                "paid": safe_float(invoice.paid_amount),
                "balance": safe_float(invoice.balance_amount),
                "invoice_date": safe_iso(invoice.invoice_date),
                "due_date": safe_iso(invoice.due_date),
                "paid_date": safe_iso(invoice.paid_date),
                "terms": invoice.terms,
                "notes": invoice.notes,
            },
            "customer": {
                "id": customer.id if customer else None,
                "name": customer.name if customer else "Unknown",
                "phone": customer.phone if customer else None,
                "whatsapp": customer.whatsapp_number if customer else None,
                "city": customer.city if customer else None,
            } if customer else None,
            "order": {
                "order_number": order.order_number if order else None,
                "order_date": safe_iso(order.order_date) if order else None,
            } if order else None,
        }
    
    @staticmethod
    def _format_overdue_invoice(invoice: Invoice, db: Session) -> dict:
        """
        Format overdue invoice with auto-generated Hinglish reminder
        THE MAGIC OF KARYA AI! ✨
        """
        # Get related order and customer
        order = db.query(Order).filter(Order.id == invoice.order_id).first()
        customer = None
        if order:
            customer = db.query(Customer).filter(
                Customer.id == order.customer_id
            ).first()
        
        # Calculate days overdue
        days_overdue = InvoiceService._calculate_days_overdue(invoice.due_date)
        
        # Get customer name for personalization
        customer_name = customer.name if customer else "Sir"
        
        # Generate personalized Hinglish reminder
        reminder = InvoiceService._generate_reminder_message(
            customer_name=customer_name,
            invoice_number=invoice.invoice_number,
            amount=safe_float(invoice.balance_amount),
            days_overdue=days_overdue
        )
        
        return {
            "invoice_number": invoice.invoice_number,
            "customer": customer_name,
            "phone": customer.phone if customer else None,
            "whatsapp": customer.whatsapp_number if customer else None,
            "amount_pending": safe_float(invoice.balance_amount),
            "due_date": safe_iso(invoice.due_date),
            "days_overdue": days_overdue,
            "urgency": InvoiceService._get_urgency_level(days_overdue),
            "suggested_reminder": reminder,
        }
    
    @staticmethod
    def _calculate_days_overdue(due_date) -> int:
        """Calculate how many days a payment is overdue"""
        if not due_date:
            return 0
        return calculate_days_between(date.today(), due_date)
    
    @staticmethod
    def _get_urgency_level(days_overdue: int) -> str:
        """Determine urgency based on days overdue"""
        if days_overdue > 30:
            return "🔴 Critical (>30 days)"
        elif days_overdue > 14:
            return "🟠 High (>14 days)"
        elif days_overdue > 7:
            return "🟡 Medium (>7 days)"
        else:
            return "🟢 Low (<7 days)"
    
    @staticmethod
    def _generate_reminder_message(
        customer_name: str,
        invoice_number: str,
        amount: float,
        days_overdue: int
    ) -> str:
        """
        Generate personalized Hinglish reminder message
        This is what makes Karya AI special for Indian businesses!
        """
        return (
            f"Namaste {customer_name}, "
            f"aapka payment ₹{amount:,.2f} "
            f"(Invoice {invoice_number}) "
            f"{days_overdue} days se pending hai. "
            f"Kripya payment karein. Dhanyawad! 🙏"
        )
    
    @staticmethod
    def _get_overdue_alert_message(count: int, total_amount: float) -> str:
        """Generate alert message for overdue summary"""
        if count == 0:
            return "✅ All payments received!"
        return f"🔴 ₹{total_amount:,.0f} pending from {count} customer(s)"