"""
Karya AI - Dashboard Service
Business intelligence and dashboard-related queries
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
    """Handles all dashboard-related business logic"""
    
    @staticmethod
    def get_dashboard_data(db: Session) -> dict:
        """
        Get complete dashboard with business info, metrics, and alerts
        
        Returns:
            dict: {
                "business": {...},
                "summary": {...},
                "alerts": [...]
            }
        """
        return {
            "business": DashboardService._get_business_info(db),
            "summary": DashboardService._get_summary_metrics(db),
            "alerts": DashboardService._get_smart_alerts(db)
        }
    
    # ==================== PRIVATE HELPER METHODS ====================
    
    @staticmethod
    def _get_business_info(db: Session) -> dict:
        """Get business information"""
        business = db.query(Business).first()
        
        if not business:
            return {
                "name": "N/A",
                "type": "N/A", 
                "city": "N/A"
            }
        
        return {
            "name": business.name,
            "type": business.business_type,
            "city": business.city,
        }
    
    @staticmethod
    def _get_summary_metrics(db: Session) -> dict:
        """Get financial summary metrics"""
        # Basic counts
        total_customers = db.query(Customer).count()
        total_products = db.query(Product).count()
        total_orders = db.query(Order).count()
        
        # Financial metrics
        total_revenue = db.query(func.sum(Order.total_amount)).scalar()
        total_outstanding = db.query(func.sum(Customer.outstanding_amount)).scalar()
        
        # Stock value
        stock_value = db.query(
            func.sum(Inventory.current_stock * Product.selling_price)
        ).join(Product, Inventory.product_id == Product.id).scalar()
        
        return {
            "total_customers": total_customers,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": format_currency(total_revenue),
            "total_outstanding": format_currency(total_outstanding),
            "total_stock_value": format_currency(stock_value),
        }
    
    @staticmethod
    def _get_smart_alerts(db: Session) -> list:
        """Generate intelligent alerts based on business state"""
        alerts = []
        
        # Check for overdue invoices
        overdue_alert = DashboardService._check_overdue_invoices(db)
        if overdue_alert:
            alerts.append(overdue_alert)
        
        # Check for low stock
        low_stock_alert = DashboardService._check_low_stock(db)
        if low_stock_alert:
            alerts.append(low_stock_alert)
        
        # Add orders processed summary (always shown)
        orders_alert = DashboardService._get_orders_summary(db)
        alerts.append(orders_alert)
        
        return alerts
    
    @staticmethod
    def _check_overdue_invoices(db: Session) -> dict:
        """Check for overdue invoices and generate alert"""
        overdue_count = db.query(Invoice).filter(
            Invoice.status == "overdue"
        ).count()
        
        if overdue_count == 0:
            return None
        
        overdue_amount = db.query(func.sum(Invoice.balance_amount)).filter(
            Invoice.status == "overdue"
        ).scalar()
        
        return {
            "icon": "🔴",
            "type": "danger",
            "message": f"{overdue_count} overdue invoices worth ₹{safe_float(overdue_amount):,.0f}",
            "priority": "high"
        }
    
    @staticmethod
    def _check_low_stock(db: Session) -> dict:
        """Check for low stock products and generate alert"""
        low_stock_count = db.query(Inventory).filter(
            Inventory.current_stock <= Inventory.reorder_level
        ).count()
        
        if low_stock_count == 0:
            return None
        
        return {
            "icon": "🟠",
            "type": "warning",
            "message": f"{low_stock_count} products need reordering",
            "priority": "medium"
        }
    
    @staticmethod
    def _get_orders_summary(db: Session) -> dict:
        """Get orders processed summary alert"""
        total_orders = db.query(Order).count()
        
        return {
            "icon": "🟢",
            "type": "success",
            "message": f"{total_orders} orders processed successfully",
            "priority": "low"
        }