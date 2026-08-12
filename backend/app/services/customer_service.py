"""
Karya AI - Customer Service
Business logic for customer-related operations
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.order import Order
from app.utils.formatters import safe_float, safe_iso


class CustomerService:
    """Handles all customer-related business logic"""
    
    @staticmethod
    def get_all_customers(db: Session) -> list:
        """
        Get all customers with basic info
        
        Returns:
            list: List of customer dictionaries
        """
        customers = db.query(Customer).all()
        return [CustomerService._format_customer(c) for c in customers]
    
    @staticmethod
    def get_customer_detail(db: Session, customer_id: int) -> dict:
        """
        Get detailed customer info with order history
        
        Args:
            customer_id: ID of the customer
            
        Returns:
            dict: Customer info + orders + stats
            
        Raises:
            HTTPException: 404 if customer not found
        """
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found"
            )
        
        # Get customer's orders
        orders = db.query(Order).filter(
            Order.customer_id == customer_id
        ).order_by(Order.order_date.desc()).all()
        
        # Calculate total business
        total_business = sum(safe_float(o.total_amount) for o in orders)
        
        return {
            "customer": CustomerService._format_customer_full(customer),
            "orders_count": len(orders),
            "total_business": total_business,
            "recent_orders": [
                CustomerService._format_order_summary(o) for o in orders
            ]
        }
    
    # ==================== PRIVATE HELPER METHODS ====================
    
    @staticmethod
    def _format_customer(customer: Customer) -> dict:
        """Format customer for list view (basic info)"""
        return {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "whatsapp": customer.whatsapp_number,
            "email": customer.email,
            "city": customer.city,
            "type": customer.customer_type,
            "credit_limit": safe_float(customer.credit_limit),
            "outstanding": safe_float(customer.outstanding_amount),
            "tags": customer.tags,
            "notes": customer.notes,
            "last_order": safe_iso(customer.last_order_date),
        }
    
    @staticmethod
    def _format_customer_full(customer: Customer) -> dict:
        """Format customer for detail view (full info)"""
        return {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "city": customer.city,
            "type": customer.customer_type,
            "credit_limit": safe_float(customer.credit_limit),
            "outstanding": safe_float(customer.outstanding_amount),
            "notes": customer.notes,
        }
    
    @staticmethod
    def _format_order_summary(order: Order) -> dict:
        """Format order for summary view"""
        return {
            "order_number": order.order_number,
            "date": safe_iso(order.order_date),
            "total": safe_float(order.total_amount),
            "status": order.status,
            "source": order.source,
            "message": order.original_message,
        }