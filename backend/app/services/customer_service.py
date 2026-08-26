"""Customer Service"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.order import Order
from app.utils.formatters import safe_float, safe_iso


class CustomerService:
    
    @staticmethod
    def get_all_customers(db: Session, scope: dict) -> list:
        q = db.query(Customer)
        if scope["scope"] == "business":
            q = q.filter(Customer.business_id == scope["business_id"])
        elif scope["scope"] == "customer":
            q = q.filter(Customer.id == scope["customer_id"])
        
        customers = q.all()
        return [CustomerService._format_customer(c) for c in customers]
    
    @staticmethod
    def get_customer_detail(db: Session, customer_id: int, scope: dict) -> dict:
        q = db.query(Customer).filter(Customer.id == customer_id)
        if scope["scope"] == "business":
            q = q.filter(Customer.business_id == scope["business_id"])
        elif scope["scope"] == "customer":
            q = q.filter(Customer.id == scope["customer_id"])
        
        customer = q.first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        orders = db.query(Order).filter(
            Order.customer_id == customer_id
        ).order_by(Order.order_date.desc()).all()
        
        total_business = sum(safe_float(o.total_amount) for o in orders)
        
        return {
            "customer": CustomerService._format_customer_full(customer),
            "orders_count": len(orders),
            "total_business": total_business,
            "recent_orders": [CustomerService._format_order_summary(o) for o in orders]
        }
    
    @staticmethod
    def _format_customer(c):
        return {
            "id": c.id, "name": c.name, "phone": c.phone,
            "whatsapp": c.whatsapp_number, "email": c.email,
            "city": c.city, "type": c.customer_type,
            "credit_limit": safe_float(c.credit_limit),
            "outstanding": safe_float(c.outstanding_amount),
            "tags": c.tags, "notes": c.notes,
            "last_order": safe_iso(c.last_order_date),
        }
    
    @staticmethod
    def _format_customer_full(c):
        return {
            "id": c.id, "name": c.name, "phone": c.phone,
            "city": c.city, "type": c.customer_type,
            "credit_limit": safe_float(c.credit_limit),
            "outstanding": safe_float(c.outstanding_amount),
            "notes": c.notes,
        }
    
    @staticmethod
    def _format_order_summary(o):
        return {
            "order_number": o.order_number,
            "date": safe_iso(o.order_date),
            "total": safe_float(o.total_amount),
            "status": o.status,
            "source": o.source,
            "message": o.original_message,
        }