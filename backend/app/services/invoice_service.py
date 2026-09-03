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
    def get_all_invoices(db: Session, scope: dict) -> list:
        try:
            q = db.query(Invoice).order_by(Invoice.invoice_date.desc())

            if scope["scope"] == "business":
                q = q.join(Order, Invoice.order_id == Order.id).filter(
                    Order.business_id == scope["business_id"]
                )
            elif scope["scope"] == "customer":
                q = q.join(Order, Invoice.order_id == Order.id).filter(
                    Order.customer_id == scope["customer_id"]
                )

            invoices = q.all()
            for inv in invoices:
                InvoiceService._refresh_overdue_status(inv)
            try:
                db.commit()
            except Exception:
                db.rollback()
            return [InvoiceService._format_invoice(inv, db) for inv in invoices]   
        except Exception as e:
            print(f"[invoice_service.get_all_invoices] {e}")
            
            return []
    
    @staticmethod
    def get_invoice_detail(db: Session, invoice_id: int, scope: dict = None) -> dict:
        """Get detailed invoice info (scoped)."""
        q = db.query(Invoice).filter(Invoice.id == invoice_id)

        if scope:
            role = scope.get("scope")
            if role == "business" and scope.get("business_id"):
                q = q.join(Order, Invoice.order_id == Order.id).filter(
                    Order.business_id == scope["business_id"]
                )
            elif role == "customer" and scope.get("customer_id"):
                q = q.join(Order, Invoice.order_id == Order.id).filter(
                    Order.customer_id == scope["customer_id"]
                )

        invoice = q.first()
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {invoice_id} not found",
            )

        # Auto-mark overdue on read (no separate cron needed)
        InvoiceService._refresh_overdue_status(invoice)
        try:
            db.commit()
        except Exception:
            db.rollback()

        return InvoiceService._format_invoice_detail(invoice, db)
    
    @staticmethod
    def get_overdue_invoices(db: Session, scope: dict) -> dict:
        try:
            q = db.query(Invoice).filter(Invoice.status == "overdue")

            if scope["scope"] == "business":
                q = q.join(Order, Invoice.order_id == Order.id).filter(
                    Order.business_id == scope["business_id"]
                )
            elif scope["scope"] == "customer":
                q = q.join(Order, Invoice.order_id == Order.id).filter(
                    Order.customer_id == scope["customer_id"]
                )

            overdue = q.all()
            total_amount = sum(safe_float(inv.balance_amount) for inv in overdue)

            invoices_data = [
                InvoiceService._format_overdue_invoice(inv, db) for inv in overdue
            ]

            return {
                "count": len(overdue),
                "total_overdue_amount": total_amount,
                "alert": InvoiceService._get_overdue_alert_message(len(overdue), total_amount),
                "invoices": invoices_data,
            }
        except Exception as e:
            print(f"[invoice_service.get_overdue_invoices] {e}")
            return {
                "count": 0,
                "total_overdue_amount": 0,
                "alert": "",
                "invoices": [],
            }

    @staticmethod
    def _refresh_overdue_status(invoice: Invoice) -> None:
        """If unpaid/partial and past due_date => overdue."""
        st = (invoice.status or "").lower()
        if st in ("paid", "cancelled", "draft"):
            return
        bal = safe_float(invoice.balance_amount)
        if bal <= 0:
            return
        if invoice.due_date and invoice.due_date < date.today():
            invoice.status = "overdue"

    @staticmethod
    def record_payment(
        db: Session,
        invoice_id: int,
        amount: float,
        scope: dict,
        payment_method: str = "manual",
        note: str = None,
        reference: str = None,
    ) -> dict:
        """
        Business records a payment against an invoice.
        - Updates paid_amount / balance_amount / status
        - Reduces customer.outstanding_amount
        - Razorpay-ready: pass payment_method='razorpay' + reference=payment_id later

        Used by UI + AI. Same function for all callers.
        """
        if scope.get("scope") != "business":
            raise HTTPException(status_code=403, detail="Only business can record payments")

        business_id = scope.get("business_id")
        if not business_id:
            raise HTTPException(status_code=400, detail="Business context missing")

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid payment amount")

        if amount <= 0:
            raise HTTPException(status_code=400, detail="Payment amount must be > 0")

        q = (
            db.query(Invoice)
            .join(Order, Invoice.order_id == Order.id)
            .filter(Invoice.id == invoice_id, Order.business_id == business_id)
        )
        invoice = q.first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        st = (invoice.status or "").lower()
        if st == "cancelled":
            raise HTTPException(status_code=400, detail="Cannot pay a cancelled invoice")
        if st == "paid" or safe_float(invoice.balance_amount) <= 0:
            raise HTTPException(status_code=400, detail="Invoice is already fully paid")

        balance = safe_float(invoice.balance_amount)
        if amount > balance + 0.001:
            raise HTTPException(
                status_code=400,
                detail=f"Amount ₹{amount} exceeds balance ₹{balance}",
            )

        paid = safe_float(invoice.paid_amount) + amount
        new_balance = round(safe_float(invoice.total_amount) - paid, 2)
        if new_balance < 0:
            new_balance = 0

        invoice.paid_amount = paid
        invoice.balance_amount = new_balance

        if new_balance <= 0:
            invoice.status = "paid"
            invoice.paid_date = date.today()
        else:
            # keep overdue if still past due, else partially_paid
            if invoice.due_date and invoice.due_date < date.today():
                invoice.status = "overdue"
            else:
                invoice.status = "partially_paid"

        # Append note (no Payment table required yet; Razorpay can add later)
        extra = f"[payment] method={payment_method or 'manual'} amount={amount}"
        if reference:
            extra += f" ref={reference}"
        if note:
            extra += f" note={note}"
        invoice.notes = ((invoice.notes or "") + "\n" + extra).strip()

        # Reduce customer outstanding
        order = db.query(Order).filter(Order.id == invoice.order_id).first()
        if order:
            customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
            if customer:
                out = safe_float(customer.outstanding_amount) - amount
                customer.outstanding_amount = out if out > 0 else 0

        try:
            db.commit()
            db.refresh(invoice)
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to record payment")

        return InvoiceService._format_invoice_detail(invoice, db)

    @staticmethod
    def delete_invoice(db: Session, invoice_id: int, scope: dict) -> dict:
        if scope.get("scope") != "business":
            raise HTTPException(status_code=403, detail="Only business can delete invoices")

        business_id = scope.get("business_id")
        if not business_id:
            raise HTTPException(status_code=400, detail="Business context missing")

        inv = (
            db.query(Invoice)
            .join(Order, Invoice.order_id == Order.id)
            .filter(Invoice.id == invoice_id, Order.business_id == business_id)
            .first()
        )
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")

        st = (inv.status or "").lower()
        paid = safe_float(inv.paid_amount)
        if st == "paid" or paid > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete an invoice with payments. Refund/adjust first.",
            )

        # Optional: block if payment_links paid
        try:
            from app.models.payment import PaymentLink, Payment
            paid_link = (
                db.query(PaymentLink)
                .filter(PaymentLink.invoice_id == inv.id, PaymentLink.status == "paid")
                .first()
            )
            if paid_link:
                raise HTTPException(status_code=400, detail="Invoice has a completed payment link")
        except ImportError:
            pass

        order = db.query(Order).filter(Order.id == inv.order_id).first()
        # Reverse outstanding if invoice was sent and raised dues
        if order and st not in ("cancelled", "draft"):
            bal = safe_float(inv.balance_amount)
            if bal > 0:
                customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
                if customer:
                    out = safe_float(customer.outstanding_amount) - bal
                    customer.outstanding_amount = out if out > 0 else 0

        inv_no = inv.invoice_number
        iid = inv.id

        # Delete dependent payment rows / links if any (unpaid drafts)
        try:
            from app.models.payment import Payment, PaymentLink
            db.query(Payment).filter(Payment.invoice_id == inv.id).delete()
            db.query(PaymentLink).filter(PaymentLink.invoice_id == inv.id).delete()
        except Exception:
            pass

        db.delete(inv)

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete invoice: {e}")

        return {
            "ok": True,
            "id": iid,
            "invoice_number": inv_no,
            "message": f"Invoice {inv_no} deleted",
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