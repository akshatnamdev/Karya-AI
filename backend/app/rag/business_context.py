from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta


from app.models.business import Business
from app.models.customer import Customer
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.invoice import Invoice
from app.utils.formatters import safe_float

class BusinessContextBuilder:
    @staticmethod
    def build_full_context(db: Session) -> str:
        """Build complete business context string for AI"""
        
        business_info = BusinessContextBuilder._get_business_info(db)
        customers_info = BusinessContextBuilder._get_customers_info(db)
        products_info = BusinessContextBuilder._get_products_info(db)
        orders_info = BusinessContextBuilder._get_orders_info(db)
        financial_info = BusinessContextBuilder._get_financial_info(db)
        alerts_info = BusinessContextBuilder._get_alerts_info(db)
        
        context = f"""
BUSINESS INFORMATION:
{business_info}

CUSTOMERS DATA:
{customers_info}

PRODUCTS & INVENTORY:
{products_info}

ORDERS DATA:
{orders_info}

FINANCIAL OVERVIEW:
{financial_info}

CURRENT ALERTS:
{alerts_info}
"""
        return context.strip()

    # =================== PRITAVE HELPERS====================    
    @staticmethod
    def _get_business_info(db: Session) -> str:
        business = db.query(Business).first()
        
        if not business:
            return "No business registered."
        
        return f"""- Business Name: {business.name}
- Type: {business.business_type}
- City: {business.city}, {business.state}
- GST: {business.gst_number}"""
    
    @staticmethod
    def _get_customers_info(db: Session) -> str:
        customers = db.query(Customer).all()
        
        if not customers:
            return "No customers yet."
        
        customer_lines = []
        for cust in customers:
            outstanding = safe_float(cust.outstanding_amount)
            outstanding_str = f"₹{outstanding:,.0f} outstanding" if outstanding > 0 else "no dues"
            
            customer_lines.append(
                f"- {cust.name} ({cust.customer_type}): "
                f"Phone {cust.phone}, "
                f"{outstanding_str}, "
                f"Credit limit ₹{safe_float(cust.credit_limit):,.0f}"
            )
        
        return "\n".join(customer_lines)
    
    @staticmethod
    def _get_products_info(db: Session) -> str:
        products = db.query(Product).all()
        
        if not products:
            return "No products yet."
        
        product_lines = []
        for prod in products:
            inv = db.query(Inventory).filter(Inventory.product_id == prod.id).first()
            stock = inv.current_stock if inv else 0
            reorder = inv.reorder_level if inv else 0
            
            status = "🔴 CRITICAL" if stock < (reorder * 0.5) else "🟡 LOW" if stock <= reorder else "🟢 OK"
            
            product_lines.append(
                f"- {prod.name} (SKU: {prod.sku}): "
                f"Stock {stock}/{reorder}, "
                f"Price ₹{safe_float(prod.selling_price):,.0f}, "
                f"Category: {prod.category}, "
                f"Status: {status}"
            )
        
        return "\n".join(product_lines)
    
    @staticmethod
    def _get_orders_info(db: Session) -> str:
        orders = db.query(Order).order_by(Order.order_date.desc()).limit(5).all()
        
        if not orders:
            return "No orders yet."
        
        order_lines = ["Recent 5 orders:"]
        for order in orders:
            customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
            customer_name = customer.name if customer else "Unknown"
            
            order_lines.append(
                f"- {order.order_number}: "
                f"{customer_name}, "
                f"₹{safe_float(order.total_amount):,.0f}, "
                f"{order.status}, "
                f"Date: {order.order_date.strftime('%Y-%m-%d')}"
            )
        
        return "\n".join(order_lines)
    
    @staticmethod
    def _get_financial_info(db: Session) -> str:
        total_revenue = db.query(func.sum(Order.total_amount)).scalar() or 0
        total_outstanding = db.query(func.sum(Customer.outstanding_amount)).scalar() or 0
        total_paid = db.query(func.sum(Invoice.paid_amount)).scalar() or 0
        
        stock_value = db.query(
            func.sum(Inventory.current_stock * Product.selling_price)
        ).join(Product, Inventory.product_id == Product.id).scalar() or 0
        
        return f"""- Total Revenue: ₹{safe_float(total_revenue):,.0f}
- Total Received: ₹{safe_float(total_paid):,.0f}
- Total Outstanding: ₹{safe_float(total_outstanding):,.0f}
- Stock Value: ₹{safe_float(stock_value):,.0f}"""
    
    @staticmethod
    def _get_alerts_info(db: Session) -> str:
        alerts = []
        
        overdue = db.query(Invoice).filter(Invoice.status == "overdue").all()
        if overdue:
            overdue_amount = sum(safe_float(inv.balance_amount) for inv in overdue)
            alerts.append(f"⚠️ {len(overdue)} overdue invoices worth ₹{overdue_amount:,.0f}")
            for inv in overdue:
                order = db.query(Order).filter(Order.id == inv.order_id).first()
                customer = db.query(Customer).filter(Customer.id == order.customer_id).first() if order else None
                customer_name = customer.name if customer else "Unknown"
                days_overdue = (date.today() - inv.due_date).days if inv.due_date else 0
                alerts.append(f"  - {customer_name}: ₹{safe_float(inv.balance_amount):,.0f} ({days_overdue} days overdue)")
        
        low_stock = db.query(Inventory, Product).join(
            Product, Inventory.product_id == Product.id
        ).filter(Inventory.current_stock <= Inventory.reorder_level).all()
        
        if low_stock:
            alerts.append(f"⚠️ {len(low_stock)} products low on stock")
            for inv, product in low_stock:
                alerts.append(f"  - {product.name}: {inv.current_stock}/{inv.reorder_level} units")
        
        if not alerts:
            return "✅ No alerts - everything looks good!"
        
        return "\n".join(alerts)