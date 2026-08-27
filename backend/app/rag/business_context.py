from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime

from app.models.business import Business
from app.models.customer import Customer
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem
from app.models.invoice import Invoice
from app.utils.formatters import safe_float, safe_int


class BusinessContextBuilder:
    """Gathers real business data for AI context - STRICTLY SCOPED BY AUTHENTICATED ROLE"""

    @staticmethod
    def build_full_context(db: Session, scope: dict) -> str:
        scope_type = scope.get("scope", "business")
        business_id = scope.get("business_id")
        customer_id = scope.get("customer_id")

        context_parts = []

        context_parts.append(
            "BUSINESS INFORMATION:\n"
            + BusinessContextBuilder._safe_get_business(db, business_id, scope_type)
        )
        context_parts.append(
            "\nPRODUCTS & CATALOG:\n"
            + BusinessContextBuilder._safe_get_products(db, business_id, scope_type)
        )
        context_parts.append(
            "\nORDERS DATA:\n"
            + BusinessContextBuilder._safe_get_orders(db, business_id, customer_id, scope_type)
        )
        context_parts.append(
            "\nINVOICES & FINANCIALS:\n"
            + BusinessContextBuilder._safe_get_invoices(db, business_id, customer_id, scope_type)
        )

        if scope_type in ["business", "all"]:
            context_parts.append(
                "\nCUSTOMERS DATA:\n"
                + BusinessContextBuilder._safe_get_customers(db, business_id, scope_type)
            )
            context_parts.append(
                "\nFINANCIAL OVERVIEW:\n"
                + BusinessContextBuilder._safe_get_financial_summary(db, business_id, scope_type)
            )
            context_parts.append(
                "\nCURRENT ALERTS:\n"
                + BusinessContextBuilder._safe_get_alerts(db, business_id, scope_type)
            )
        elif scope_type == "customer":
            context_parts.append(
                "\nMY ACCOUNT PROFILE:\n"
                + BusinessContextBuilder._safe_get_my_profile(db, customer_id)
            )

        return "\n".join(context_parts).strip()

    # ==================== PRIVATE SECURE HELPERS ====================

    @staticmethod
    def _safe_get_business(db: Session, business_id: int, scope_type: str) -> str:
        try:
            if scope_type == "all":
                return "Platform Admin View: System-wide access."
            if not business_id:
                return "No specific business linked."
            business = db.query(Business).filter(Business.id == business_id).first()
            if not business:
                return "Business information not found."
            return (
                f"- Business Name: {business.name or 'Unnamed'}\n"
                f"- Type: {getattr(business, 'business_type', None) or 'General'}\n"
                f"- Location: {getattr(business, 'city', None) or 'India'}"
            )
        except Exception as e:
            return f"Error loading business info: {e}"

    @staticmethod
    def _safe_get_my_profile(db: Session, customer_id: int) -> str:
        try:
            if not customer_id:
                return "No customer profile linked."
            c = db.query(Customer).filter(Customer.id == customer_id).first()
            if not c:
                return "Profile not found."

            credit = safe_float(getattr(c, "credit_limit", 0) or 0)
            outstanding = safe_float(getattr(c, "outstanding_amount", 0) or 0)
            phone = getattr(c, "phone", None) or "N/A"

            return (
                f"- Name: {c.name or 'Unnamed'}\n"
                f"- Phone: {phone}\n"
                f"- Credit Limit: ₹{credit:,.0f}\n"
                f"- Outstanding Dues: ₹{outstanding:,.0f}"
            )
        except Exception as e:
            return f"Error loading profile: {e}"

    @staticmethod
    def _safe_get_customers(db: Session, business_id: int, scope_type: str) -> str:
        try:
            if scope_type == "customer":
                return ""
            q = db.query(Customer)
            if scope_type == "business" and business_id:
                q = q.filter(Customer.business_id == business_id)
            customers = q.all()
            if not customers:
                return "No customers registered yet."

            lines = []
            for cust in customers:
                out = safe_float(getattr(cust, "outstanding_amount", 0) or 0)
                out_str = f"₹{out:,.0f} outstanding" if out > 0 else "no dues"
                lines.append(
                    f"- {cust.name or 'Unnamed'} ({getattr(cust, 'customer_type', None) or 'retail'}): "
                    f"Phone {getattr(cust, 'phone', None) or 'N/A'}, {out_str}, "
                    f"Credit limit ₹{safe_float(getattr(cust, 'credit_limit', 0) or 0):,.0f}"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"Error loading customers: {e}"

    @staticmethod
    def _safe_get_products(db: Session, business_id: int, scope_type: str) -> str:
        try:
            q = db.query(Product)
            if scope_type in ["business", "customer"] and business_id:
                q = q.filter(Product.business_id == business_id)
            if scope_type == "customer":
                q = q.filter(Product.is_active == True)

            products = q.all()
            if not products:
                return "No products listed in catalog."

            lines = []
            for prod in products:
                price = f"Price ₹{safe_float(prod.selling_price):,.0f}"
                if scope_type in ["business", "all"]:
                    inv = db.query(Inventory).filter(Inventory.product_id == prod.id).first()
                    stock = safe_int(inv.current_stock) if inv else 0
                    reorder = safe_int(inv.reorder_level) if inv else 0
                    status = (
                        "CRITICAL"
                        if stock < (reorder * 0.5)
                        else "LOW"
                        if stock <= reorder
                        else "OK"
                    )
                    lines.append(
                        f"- {prod.name} (SKU: {prod.sku}): Stock {stock}/{reorder}, {price}, Status: {status}"
                    )
                else:
                    lines.append(f"- {prod.name}: {price} (Available)")
            return "\n".join(lines)
        except Exception as e:
            return f"Error loading products: {e}"

    @staticmethod
    def _format_date(value) -> str:
        try:
            if isinstance(value, (date, datetime)):
                return value.strftime("%Y-%m-%d")
            if value is None:
                return "N/A"
            return str(value)[:10]
        except Exception:
            return "N/A"

    @staticmethod
    def _safe_get_orders(db: Session, business_id: int, customer_id: int, scope_type: str) -> str:
        """
        FIXED for customer order history.
        - Scope filters applied BEFORE limit
        - Customer filtered by customer_id (+ business_id when present)
        - Defensive formatting
        - Includes line items so AI can answer "show my orders"
        """
        try:
            q = db.query(Order)

            if scope_type == "business" and business_id:
                q = q.filter(Order.business_id == business_id)
            elif scope_type == "customer":
                if not customer_id:
                    return "No customer linked to this account. Cannot load order history."
                q = q.filter(Order.customer_id == customer_id)
                if business_id:
                    q = q.filter(Order.business_id == business_id)
            elif scope_type == "all":
                pass
            else:
                return "No order access for this role."

            orders = q.order_by(Order.order_date.desc()).limit(20).all()
            if not orders:
                return "No order history found."

            lines = []
            for o in orders:
                o_date = BusinessContextBuilder._format_date(getattr(o, "order_date", None))
                total = safe_float(getattr(o, "total_amount", 0) or 0)
                number = getattr(o, "order_number", None) or f"#{o.id}"
                status = getattr(o, "status", None) or "pending"

                item_bits = []
                try:
                    items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
                    for it in items:
                        prod = db.query(Product).filter(Product.id == it.product_id).first()
                        pname = prod.name if prod else f"Product #{it.product_id}"
                        qty = safe_int(it.quantity)
                        item_bits.append(f"{pname} x {qty}")
                except Exception:
                    item_bits = []

                items_str = ", ".join(item_bits) if item_bits else "N/A"
                lines.append(
                    f"- Order {number}: ₹{total:,.0f}, Status: {status}, Date: {o_date}, Items: {items_str}"
                )

            return "\n".join(lines)
        except Exception as e:
            return f"Error loading orders: {e}"

    @staticmethod
    def _safe_get_invoices(db: Session, business_id: int, customer_id: int, scope_type: str) -> str:
        """
        FIXED customer invoice scoping.
        Prefer Invoice.customer_id when available; fallback to join via Order.
        """
        try:
            q = db.query(Invoice)

            if scope_type == "business" and business_id:
                # Prefer direct business_id on invoice if present; else join orders
                if hasattr(Invoice, "business_id"):
                    q = q.filter(Invoice.business_id == business_id)
                else:
                    q = q.join(Order, Invoice.order_id == Order.id).filter(
                        Order.business_id == business_id
                    )

            elif scope_type == "customer":
                if not customer_id:
                    return "No customer linked. Cannot load invoices."
                if hasattr(Invoice, "customer_id"):
                    q = q.filter(Invoice.customer_id == customer_id)
                    if business_id and hasattr(Invoice, "business_id"):
                        q = q.filter(Invoice.business_id == business_id)
                else:
                    q = q.join(Order, Invoice.order_id == Order.id).filter(
                        Order.customer_id == customer_id
                    )
                    if business_id:
                        q = q.filter(Order.business_id == business_id)
            elif scope_type != "all":
                return "No invoice access for this role."

            # due_date may be null — don't crash sort
            try:
                invoices = q.order_by(Invoice.due_date.asc.nullslast()).limit(30).all()  # type: ignore
            except Exception:
                invoices = q.limit(30).all()

            if not invoices:
                return "No invoice or billing records."

            lines = []
            for i in invoices:
                d_date = BusinessContextBuilder._format_date(getattr(i, "due_date", None))
                inv_no = getattr(i, "invoice_number", None) or f"#{i.id}"
                total = safe_float(getattr(i, "total_amount", 0) or 0)
                # balance_amount OR amount_due OR pending_amount fallbacks
                pending = getattr(i, "balance_amount", None)
                if pending is None:
                    pending = getattr(i, "amount_due", None)
                if pending is None:
                    pending = getattr(i, "pending_amount", None)
                pending = safe_float(pending or 0)
                status = getattr(i, "status", None) or "unknown"
                lines.append(
                    f"- Invoice {inv_no}: Total ₹{total:,.2f}, Pending: ₹{pending:,.2f}, "
                    f"Status: {status}, Due: {d_date}"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"Error loading invoices: {e}"

    @staticmethod
    def _safe_get_financial_summary(db: Session, business_id: int, scope_type: str) -> str:
        try:
            if scope_type == "customer":
                return ""
            order_q = db.query(func.sum(Order.total_amount))
            cust_q = db.query(func.sum(Customer.outstanding_amount))
            if scope_type == "business" and business_id:
                order_q = order_q.filter(Order.business_id == business_id)
                cust_q = cust_q.filter(Customer.business_id == business_id)
            rev = order_q.scalar() or 0
            out = cust_q.scalar() or 0
            return (
                f"- Total Revenue: ₹{safe_float(rev):,.0f}\n"
                f"- Total Outstanding: ₹{safe_float(out):,.0f}"
            )
        except Exception:
            return ""

    @staticmethod
    def _safe_get_alerts(db: Session, business_id: int, scope_type: str) -> str:
        try:
            if scope_type == "customer":
                return ""
            alerts = []
            inv_q = db.query(Invoice).filter(Invoice.status == "overdue")
            if scope_type == "business" and business_id:
                if hasattr(Invoice, "business_id"):
                    inv_q = inv_q.filter(Invoice.business_id == business_id)
                else:
                    inv_q = inv_q.join(Order, Invoice.order_id == Order.id).filter(
                        Order.business_id == business_id
                    )
            overdue = inv_q.all()
            if overdue:
                amt = 0.0
                for i in overdue:
                    bal = getattr(i, "balance_amount", None)
                    if bal is None:
                        bal = getattr(i, "amount_due", 0)
                    amt += safe_float(bal or 0)
                alerts.append(f"OVERDUE: {len(overdue)} invoices worth ₹{amt:,.0f}")
            return "\n".join(alerts) if alerts else "No active alerts."
        except Exception:
            return ""