"""
Order Service - role-aware
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import datetime
from app.models.order import Order, OrderItem
from app.models.customer import Customer
from app.models.product import Product
from app.utils.formatters import safe_float, safe_iso
from app.models.inventory import Inventory 



class OrderService:
    
    @staticmethod
    def get_all_orders(db: Session, scope: dict) -> list:
        q = db.query(Order).order_by(Order.order_date.desc())
        
        if scope["scope"] == "business":
            q = q.filter(Order.business_id == scope["business_id"])
        elif scope["scope"] == "customer":
            q = q.filter(Order.customer_id == scope["customer_id"])
        
        orders = q.all()
        return [OrderService._format_order_summary(o, db) for o in orders]
    
    @staticmethod
    def get_order_detail(db: Session, order_id: int, scope: dict) -> dict:
        q = db.query(Order).filter(Order.id == order_id)
        
        if scope["scope"] == "business":
            q = q.filter(Order.business_id == scope["business_id"])
        elif scope["scope"] == "customer":
            q = q.filter(Order.customer_id == scope["customer_id"])
        
        order = q.first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return OrderService._format_order_detail(order, db)
    
    @staticmethod
    def get_whatsapp_orders(db: Session, scope: dict) -> dict:
        # Customers don't need this view
        if scope["scope"] == "customer":
            return {"count": 0, "orders": []}
        
        q = db.query(Order).filter(
            Order.source == "whatsapp"
        ).order_by(Order.order_date.desc())
        
        if scope["scope"] == "business":
            q = q.filter(Order.business_id == scope["business_id"])
        
        orders = q.all()
        
        return {
            "count": len(orders),
            "orders": [OrderService._format_whatsapp_order(o) for o in orders]
        }
    @staticmethod
    def create_unified_order(
        db: Session, 
        business_id: int, 
        customer_id: int, 
        items_data: list, 
        source: str = "manual", 
        notes: str = None
    ) -> dict:
        """
        Unified order placement for Business UI, Customer UI, and AI Assistant.
        Validates stock, calculates totals, deducts inventory, and saves order.
        """
        # 1. Generate Unique Order Number
        timestamp = int(datetime.datetime.now().timestamp())
        order_number = f"ORD-{timestamp}"

        # 2. Initialize Order
        new_order = Order(
            order_number=order_number,
            business_id=business_id,
            customer_id=customer_id,
            status="pending",
            source=source,
            notes=notes,
            subtotal=0,
            tax_amount=0,
            total_amount=0
        )
        db.add(new_order)
        db.flush() # Get the new_order.id

        subtotal = 0

        # 3. Process Items and Deduct Stock
        for item in items_data:
            product_id = item["product_id"]
            qty = item["quantity"]

            # Validate Product
            product = db.query(Product).filter(
                Product.id == product_id, 
                Product.business_id == business_id,
                Product.is_active == True
            ).first()
            
            if not product:
                db.rollback()
                raise HTTPException(status_code=404, detail=f"Product ID {product_id} not found or inactive")

            # Validate & Deduct Stock
            inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
            if not inventory or inventory.current_stock < qty:
                db.rollback()
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient stock for '{product.name}'. Available: {inventory.current_stock if inventory else 0}"
                )

            # Calculate Item Total
            unit_price = product.selling_price
            item_total = unit_price * qty
            subtotal += item_total

            # Create Order Item
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                quantity=qty,
                unit_price=unit_price,
                total=item_total
            )
            db.add(order_item)

            # Deduct Inventory
            inventory.current_stock -= qty

        # 4. Finalize Order Totals
        new_order.subtotal = subtotal
        new_order.total_amount = subtotal # Assuming no tax logic yet as per simple flow

        # 5. Commit Transaction
        try:
            db.commit()
            db.refresh(new_order)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error during order creation")

        # Return formatted order using your existing helper
        return OrderService._format_order_detail(new_order, db)


    
    # ==================== PRIVATE HELPERS ====================
    
    @staticmethod
    def _format_order_summary(order, db):
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        items_count = db.query(OrderItem).filter(OrderItem.order_id == order.id).count()
        
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
    def _format_order_detail(order, db):
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        
        items_detail = [OrderService._format_order_item(item, db) for item in items]
        
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
    def _format_order_item(item, db):
        product = db.query(Product).filter(Product.id == item.product_id).first()
        
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
    def _format_whatsapp_order(order):
        return {
            "order_number": order.order_number,
            "customer_id": order.customer_id,
            "original_whatsapp_message": order.original_message,
            "total": safe_float(order.total_amount),
            "status": order.status,
            "date": safe_iso(order.order_date),
        }