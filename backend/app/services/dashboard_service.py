"""
Dashboard Service - now role-aware
"""
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.business import Business
from app.models.customer import Customer
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.invoice import Invoice
from app.utils.formatters import safe_float, format_currency


class DashboardService:
    
    @staticmethod
    def get_dashboard_data(db: Session, scope: dict) -> dict:
        """Get dashboard data scoped to user's role"""
        return {
            "business": DashboardService._get_business_info(db, scope),
            "summary": DashboardService._get_summary_metrics(db, scope),
            "alerts": DashboardService._get_smart_alerts(db, scope),
        }
    
    @staticmethod
    def _get_business_info(db: Session, scope: dict) -> dict:
        if scope["scope"] == "all":
            count = db.query(Business).count()
            return {"name": f"Platform ({count} businesses)", "type": "platform", "city": "—"}
        
        business = db.query(Business).filter(Business.id == scope["business_id"]).first()
        if not business:
            return {"name": "N/A", "type": "N/A", "city": "N/A"}
        
        return {
            "name": business.name,
            "type": business.business_type,
            "city": business.city,
        }
    
    @staticmethod
    def _get_summary_metrics(db: Session, scope: dict) -> dict:
        # Base queries
        customer_q = db.query(Customer)
        product_q = db.query(Product)
        order_q = db.query(Order)
        
        if scope["scope"] == "business":
            customer_q = customer_q.filter(Customer.business_id == scope["business_id"])
            product_q = product_q.filter(Product.business_id == scope["business_id"])
            order_q = order_q.filter(Order.business_id == scope["business_id"])
        elif scope["scope"] == "customer":
            customer_q = customer_q.filter(Customer.id == scope["customer_id"])
            product_q = product_q.filter(Product.business_id == scope["business_id"])
            order_q = order_q.filter(Order.customer_id == scope["customer_id"])
        
        total_customers = customer_q.count()
        total_products = product_q.count()
        total_orders = order_q.count()
        
        total_revenue = order_q.with_entities(func.sum(Order.total_amount)).scalar()
        total_outstanding = customer_q.with_entities(func.sum(Customer.outstanding_amount)).scalar()
        
        stock_q = db.query(func.sum(Inventory.current_stock * Product.selling_price)).join(
            Product, Inventory.product_id == Product.id
        )
        if scope["scope"] in ("business", "customer"):
            stock_q = stock_q.filter(Product.business_id == scope["business_id"])
        stock_value = stock_q.scalar()
        
        return {
            "total_customers": total_customers,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": format_currency(total_revenue),
            "total_outstanding": format_currency(total_outstanding),
            "total_stock_value": format_currency(stock_value),
        }
    
    @staticmethod
    def _get_smart_alerts(db: Session, scope: dict) -> list:
        alerts = []
        
        overdue_alert = DashboardService._check_overdue_invoices(db, scope)
        if overdue_alert:
            alerts.append(overdue_alert)
        
        low_stock_alert = DashboardService._check_low_stock(db, scope)
        if low_stock_alert:
            alerts.append(low_stock_alert)
        
        orders_alert = DashboardService._get_orders_summary(db, scope)
        alerts.append(orders_alert)
        
        return alerts
    
    @staticmethod
    def _check_overdue_invoices(db: Session, scope: dict) -> dict:
        q = db.query(Invoice).filter(Invoice.status == "overdue")
        
        if scope["scope"] == "business":
            q = q.join(Order, Invoice.order_id == Order.id).filter(
                Order.business_id == scope["business_id"]
            )
        elif scope["scope"] == "customer":
            q = q.join(Order, Invoice.order_id == Order.id).filter(
                Order.customer_id == scope["customer_id"]
            )
        
        count = q.count()
        if count == 0:
            return None
        
        amount = q.with_entities(func.sum(Invoice.balance_amount)).scalar() or 0
        
        return {
            "icon": "🔴",
            "type": "danger",
            "message": f"{count} overdue invoices worth ₹{safe_float(amount):,.0f}",
            "priority": "high"
        }
    
    @staticmethod
    def _check_low_stock(db: Session, scope: dict) -> dict:
        q = db.query(Inventory).filter(Inventory.current_stock <= Inventory.reorder_level)
        
        if scope["scope"] in ("business", "customer"):
            q = q.join(Product, Inventory.product_id == Product.id).filter(
                Product.business_id == scope["business_id"]
            )
        
        count = q.count()
        if count == 0:
            return None
        
        return {
            "icon": "🟠",
            "type": "warning",
            "message": f"{count} products need reordering",
            "priority": "medium"
        }
    
    @staticmethod
    def _get_orders_summary(db: Session, scope: dict) -> dict:
        q = db.query(Order)
        
        if scope["scope"] == "business":
            q = q.filter(Order.business_id == scope["business_id"])
        elif scope["scope"] == "customer":
            q = q.filter(Order.customer_id == scope["customer_id"])
        
        count = q.count()
        return {
            "icon": "🟢",
            "type": "success",
            "message": f"{count} orders processed",
            "priority": "low"
        }