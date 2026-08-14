"""
Karya AI - Order Service
Business logic for order management
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem
from app.models.customer import Customer
from app.models.product import Product
from app.utils.formatters import safe_float, safe_iso

class OrderService:
    """Handles all order-related business logic"""
    
    @staticmethod
    def get_all_orders(db: Session) -> list:
        """
        Get all orders sorted by most recent
        
        Returns:
            list: List of orders with customer info
        """
        orders = db.query(Order).order_by(Order.order_date.desc()).all()
        return [OrderService._format_order_summary(order, db) for order in orders]
    
    @staticmethod
    def get_order_detail(db: Session, order_id: int) -> dict:
        """
        Get detailed order info with items and customer
        
        Args:
            order_id: ID of the order
            
        Returns:
            dict: Complete order details
            
        Raises:
            HTTPException: 404 if order not found
        """
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID {order_id} not found"
            )
        
        return OrderService._format_order_detail(order, db)
    
    @staticmethod
    def get_whatsapp_orders(db: Session) -> dict:
        """
        Get all orders that came from WhatsApp
        Shows the power of WhatsApp integration!
        
        Returns:
            dict: WhatsApp orders with original messages
        """
        orders = db.query(Order).filter(
            Order.source == "whatsapp"
        ).order_by(Order.order_date.desc()).all()
        
        return {
            "count": len(orders),
            "orders": [
                OrderService._format_whatsapp_order(order) 
                for order in orders
            ]
        }
    
    # ==================== PRIVATE HELPER METHODS ====================
    
    @staticmethod
    def _format_order_summary(order: Order, db: Session) -> dict:
        """Format order for list view (summary)"""
        # Get customer info
        customer = db.query(Customer).filter(
            Customer.id == order.customer_id
        ).first()
        
        # Count items
        items_count = db.query(OrderItem).filter(
            OrderItem.order_id == order.id
        ).count()
        
        return {
            "id": order.id,
            "order_number": order.order_number,
            "customer_name": customer.name if customer else "Unknown",
            "customer_phone": customer.phone if customer else None,
            "status": order.status,
            "source": order.source,
            "total": safe_float(order.total_amount),
            "items_count": items_count,
            "order_date": safe_iso(order.order_date),
            "delivery_date": safe_iso(order.delivery_date),
            "whatsapp_message": order.original_message,
        }
    
    @staticmethod
    def _format_order_detail(order: Order, db: Session) -> dict:
        """Format order for detail view (full info)"""
        # Get customer
        customer = db.query(Customer).filter(
            Customer.id == order.customer_id
        ).first()
        
        # Get order items with product info
        items = db.query(OrderItem).filter(
            OrderItem.order_id == order.id
        ).all()
        
        items_detail = [
            OrderService._format_order_item(item, db) 
            for item in items
        ]
        
        return {
            "order": {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "source": order.source,
                "subtotal": safe_float(order.subtotal),
                "tax": safe_float(order.tax_amount),
                "discount": safe_float(order.discount_amount),
                "total": safe_float(order.total_amount),
                "order_date": safe_iso(order.order_date),
                "delivery_date": safe_iso(order.delivery_date),
                "delivered_at": safe_iso(order.delivered_at),
                "original_message": order.original_message,
                "notes": order.notes,
            },
            "customer": {
                "id": customer.id if customer else None,
                "name": customer.name if customer else "Unknown",
                "phone": customer.phone if customer else None,
                "whatsapp": customer.whatsapp_number if customer else None,
                "city": customer.city if customer else None,
                "type": customer.customer_type if customer else None,
            } if customer else None,
            "items": items_detail,
            "items_count": len(items_detail),
        }
    
    @staticmethod
    def _format_order_item(item: OrderItem, db: Session) -> dict:
        """Format single order item with product info"""
        product = db.query(Product).filter(
            Product.id == item.product_id
        ).first()
        
        return {
            "product_id": item.product_id,
            "product_name": product.name if product else "Unknown",
            "sku": product.sku if product else None,
            "quantity": item.quantity,
            "unit_price": safe_float(item.unit_price),
            "discount": safe_float(item.discount),
            "total": safe_float(item.total),
        }
    
    @staticmethod
    def _format_whatsapp_order(order: Order) -> dict:
        """Format WhatsApp order (highlights the message)"""
        return {
            "order_number": order.order_number,
            "customer_id": order.customer_id,
            "original_whatsapp_message": order.original_message,
            "total": safe_float(order.total_amount),
            "status": order.status,
            "date": safe_iso(order.order_date),
        }

    