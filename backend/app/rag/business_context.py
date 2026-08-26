from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime

from app.models.business import Business
from app.models.customer import Customer
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.invoice import Invoice
from app.utils.formatters import safe_float, safe_int


class BusinessContextBuilder:
    """Gathers real business data for AI context - STRICTLY SCOPED BY AUTHENTICATED ROLE"""
    
    @staticmethod
    def build_full_context(db: Session, scope: dict) -> str:
        # Trust ONLY the authenticated scope derived from the JWT token
        scope_type = scope.get("scope", "business")
        business_id = scope.get("business_id")
        customer_id = scope.get("customer_id")
        
        context_parts = []
        
        # 1. Business Info
        context_parts.append("BUSINESS INFORMATION:\n" + BusinessContextBuilder._safe_get_business(db, business_id, scope_type))
        
        # 2. Product Catalog (Scoped)
        context_parts.append("\nPRODUCTS & CATALOG:\n" + BusinessContextBuilder._safe_get_products(db, business_id, scope_type))
        
        # 3. Orders (Strictly Scoped)
        context_parts.append("\nORDERS DATA:\n" + BusinessContextBuilder._safe_get_orders(db, business_id, customer_id, scope_type))
        
        # 4. Invoices (Strictly Scoped)
        context_parts.append("\nINVOICES & FINANCIALS:\n" + BusinessContextBuilder._safe_get_invoices(db, business_id, customer_id, scope_type))

        # 5. Role-Specific Extensions
        if scope_type in ["business", "all"]:
            context_parts.append("\nCUSTOMERS DATA:\n" + BusinessContextBuilder._safe_get_customers(db, business_id, scope_type))
            context_parts.append("\nFINANCIAL OVERVIEW:\n" + BusinessContextBuilder._safe_get_financial_summary(db, business_id, scope_type))
            context_parts.append("\nCURRENT ALERTS:\n" + BusinessContextBuilder._safe_get_alerts(db, business_id, scope_type))
        elif scope_type == "customer":
            context_parts.append("\nMY ACCOUNT PROFILE:\n" + BusinessContextBuilder._safe_get_my_profile(db, customer_id))

        return "\n".join(context_parts).strip()

    # ==================== PRIVATE SECURE HELPERS ====================
    
    @staticmethod
    def _safe_get_business(db: Session, business_id: int, scope_type: str) -> str:
        try:
            if scope_type == "all": return "Platform Admin View: System-wide access."
            if not business_id: return "No specific business linked."
            business = db.query(Business).filter(Business.id == business_id).first()
            if not business: return "Business information not found."
            return f"- Business Name: {business.name or 'Unnamed'}\n- Type: {business.business_type or 'General'}\n- Location: {business.city or 'India'}"
        except Exception as e: return f"Error loading business info: {e}"

    @staticmethod
    def _safe_get_my_profile(db: Session, customer_id: int) -> str:
        try:
            if not customer_id: return "No customer profile linked."
            c = db.query(Customer).filter(Customer.id == customer_id).first()
            if not c: return "Profile not found."
            return f"- Name: {c.name}\n- Phone: {c.phone}\n- Credit Limit: ₹{safe_float(c.credit_limit):,.0f}\n- Outstanding Dues: ₹{safe_float(c.outstanding_amount):,.0f}"
        except Exception as e: return f"Error loading profile: {e}"
    
    @staticmethod
    def _safe_get_customers(db: Session, business_id: int, scope_type: str) -> str:
        try:
            if scope_type == "customer": return "" # Hard block
            q = db.query(Customer)
            if scope_type == "business" and business_id:
                q = q.filter(Customer.business_id == business_id)
            customers = q.all()
            if not customers: return "No customers registered yet."
            
            lines = []
            for cust in customers:
                out = safe_float(cust.outstanding_amount)
                out_str = f"₹{out:,.0f} outstanding" if out > 0 else "no dues"
                lines.append(f"- {cust.name or 'Unnamed'} ({cust.customer_type or 'retail'}): Phone {cust.phone or 'N/A'}, {out_str}, Credit limit ₹{safe_float(cust.credit_limit):,.0f}")
            return "\n".join(lines)
        except Exception as e: return f"Error loading customers: {e}"
    
    @staticmethod
    def _safe_get_products(db: Session, business_id: int, scope_type: str) -> str:
        try:
            q = db.query(Product)
            if scope_type in ["business", "customer"] and business_id:
                q = q.filter(Product.business_id == business_id)
            if scope_type == "customer":
                q = q.filter(Product.is_active == True)
                
            products = q.all()
            if not products: return "No products listed in catalog."
            
            lines = []
            for prod in products:
                price = f"Price ₹{safe_float(prod.selling_price):,.0f}"
                if scope_type in ["business", "all"]:
                    inv = db.query(Inventory).filter(Inventory.product_id == prod.id).first()
                    stock = safe_int(inv.current_stock) if inv else 0
                    reorder = safe_int(inv.reorder_level) if inv else 0
                    status = "CRITICAL" if stock < (reorder * 0.5) else "LOW" if stock <= reorder else "OK"
                    lines.append(f"- {prod.name} (SKU: {prod.sku}): Stock {stock}/{reorder}, {price}, Status: {status}")
                else:
                    lines.append(f"- {prod.name}: {price} (Available)")
            return "\n".join(lines)
        except Exception as e: return f"Error loading products: {e}"
    
    @staticmethod
    def _safe_get_orders(db: Session, business_id: int, customer_id: int, scope_type: str) -> str:
        try:
            q = db.query(Order).order_by(Order.order_date.desc()).limit(15)
            # STRICT SCOPING
            if scope_type == "business" and business_id:
                q = q.filter(Order.business_id == business_id)
            elif scope_type == "customer" and customer_id:
                q = q.filter(Order.customer_id == customer_id)
                
            orders = q.all()
            if not orders: return "No order history found."
            
            lines = []
            for o in orders:
                o_date = o.order_date.strftime('%Y-%m-%d') if isinstance(o.order_date, (date, datetime)) else "Recent"
                lines.append(f"- Order {o.order_number or f'#{o.id}'}: ₹{safe_float(o.total_amount):,.0f}, Status: {o.status or 'pending'}, Date: {o_date}")
            return "\n".join(lines)
        except Exception as e: return f"Error loading orders: {e}"
        
    @staticmethod
    def _safe_get_invoices(db: Session, business_id: int, customer_id: int, scope_type: str) -> str:
        try:
            q = db.query(Invoice).order_by(Invoice.due_date.asc())
            # STRICT SCOPING
            if scope_type == "business" and business_id:
                q = q.join(Order).filter(Order.business_id == business_id)
            elif scope_type == "customer" and customer_id:
                q = q.join(Order).filter(Order.customer_id == customer_id)
                
            invoices = q.all()
            if not invoices: return "No invoice or billing records."
                
            lines = []
            for i in invoices:
                d_date = i.due_date.strftime('%Y-%m-%d') if isinstance(i.due_date, (date, datetime)) else "N/A"
                lines.append(f"- Invoice {i.invoice_number}: Total ₹{safe_float(i.total_amount):,.0f}, Pending: ₹{safe_float(i.balance_amount):,.0f}, Status: {i.status}, Due: {d_date}")
            return "\n".join(lines)
        except Exception as e: return f"Error loading invoices: {e}"

    @staticmethod
    def _safe_get_financial_summary(db: Session, business_id: int, scope_type: str) -> str:
        try:
            if scope_type == "customer": return ""
            order_q = db.query(func.sum(Order.total_amount))
            cust_q = db.query(func.sum(Customer.outstanding_amount))
            if scope_type == "business" and business_id:
                order_q = order_q.filter(Order.business_id == business_id)
                cust_q = cust_q.filter(Customer.business_id == business_id)
            rev = order_q.scalar() or 0
            out = cust_q.scalar() or 0
            return f"- Total Revenue: ₹{safe_float(rev):,.0f}\n- Total Outstanding: ₹{safe_float(out):,.0f}"
        except Exception: return ""

    @staticmethod
    def _safe_get_alerts(db: Session, business_id: int, scope_type: str) -> str:
        try:
            if scope_type == "customer": return ""
            alerts = []
            inv_q = db.query(Invoice).filter(Invoice.status == "overdue")
            if scope_type == "business" and business_id:
                inv_q = inv_q.join(Order).filter(Order.business_id == business_id)
            overdue = inv_q.all()
            if overdue:
                amt = sum(safe_float(i.balance_amount) for i in overdue)
                alerts.append(f"OVERDUE: {len(overdue)} invoices worth ₹{amt:,.0f}")
            return "\n".join(alerts) if alerts else "No active alerts."
        except Exception: return ""