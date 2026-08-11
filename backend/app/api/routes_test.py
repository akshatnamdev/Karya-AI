"""
Karya AI - Test API Routes (Bulletproof Version)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from typing import Optional

from app.db.database import get_db
from app.models.user import User
from app.models.business import Business
from app.models.customer import Customer
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem
from app.models.invoice import Invoice
from app.models.payment import Payment


router = APIRouter(prefix="/api/test", tags=["Test Endpoints"])


def safe_float(value) -> float:
    """Safely convert Decimal/None to float"""
    if value is None:
        return 0.0
    return float(value)


def safe_iso(dt) -> Optional[str]:
    """Safely convert datetime to ISO string"""
    if dt is None:
        return None
    return dt.isoformat()


# ==================== HEALTH CHECK ====================

@router.get("/ping")
def ping():
    """Simple ping to check if routes are loaded"""
    return {"status": "ok", "message": "Test routes are working!"}


# ==================== DASHBOARD ====================

@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    """🎯 Main Dashboard - Everything at a glance"""
    try:
        # Get business
        business = db.query(Business).first()
        
        # Basic counts
        total_customers = db.query(Customer).count()
        total_products = db.query(Product).count()
        total_orders = db.query(Order).count()
        
        # Financial metrics
        total_revenue = db.query(func.sum(Order.total_amount)).scalar()
        total_outstanding = db.query(func.sum(Customer.outstanding_amount)).scalar()
        
        # Stock value
        stock_value_result = db.query(
            func.sum(Inventory.current_stock * Product.selling_price)
        ).join(Product, Inventory.product_id == Product.id).scalar()
        
        # Alerts
        low_stock_count = db.query(Inventory).filter(
            Inventory.current_stock <= Inventory.reorder_level
        ).count()
        
        overdue_count = db.query(Invoice).filter(Invoice.status == "overdue").count()
        overdue_amount = db.query(func.sum(Invoice.balance_amount)).filter(
            Invoice.status == "overdue"
        ).scalar()
        
        # Build alerts list
        alerts = []
        if overdue_count > 0:
            alerts.append({
                "icon": "🔴",
                "type": "danger",
                "message": f"{overdue_count} overdue invoices worth ₹{safe_float(overdue_amount):,.0f}",
                "priority": "high"
            })
        if low_stock_count > 0:
            alerts.append({
                "icon": "🟠",
                "type": "warning",
                "message": f"{low_stock_count} products need reordering",
                "priority": "medium"
            })
        alerts.append({
            "icon": "🟢",
            "type": "success",
            "message": f"{total_orders} orders processed successfully",
            "priority": "low"
        })
        
        return {
            "business": {
                "name": business.name if business else "N/A",
                "type": business.business_type if business else "N/A",
                "city": business.city if business else "N/A",
            },
            "summary": {
                "total_customers": total_customers,
                "total_products": total_products,
                "total_orders": total_orders,
                "total_revenue": f"₹{safe_float(total_revenue):,.2f}",
                "total_outstanding": f"₹{safe_float(total_outstanding):,.2f}",
                "total_stock_value": f"₹{safe_float(stock_value_result):,.2f}",
            },
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")


# ==================== STATS ====================

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get count of records in each table"""
    try:
        return {
            "users": db.query(User).count(),
            "businesses": db.query(Business).count(),
            "customers": db.query(Customer).count(),
            "products": db.query(Product).count(),
            "inventory": db.query(Inventory).count(),
            "orders": db.query(Order).count(),
            "order_items": db.query(OrderItem).count(),
            "invoices": db.query(Invoice).count(),
            "payments": db.query(Payment).count(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")


# ==================== CUSTOMERS ====================

@router.get("/customers")
def get_customers(db: Session = Depends(get_db)):
    """Get all customers"""
    try:
        customers = db.query(Customer).all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "whatsapp": c.whatsapp_number,
                "email": c.email,
                "city": c.city,
                "type": c.customer_type,
                "credit_limit": safe_float(c.credit_limit),
                "outstanding": safe_float(c.outstanding_amount),
                "tags": c.tags,
                "notes": c.notes,
                "last_order": safe_iso(c.last_order_date),
            }
            for c in customers
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Customers error: {str(e)}")


@router.get("/customers/{customer_id}")
def get_customer_detail(customer_id: int, db: Session = Depends(get_db)):
    """Get customer detail with order history"""
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        orders = db.query(Order).filter(Order.customer_id == customer_id).all()
        
        return {
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "city": customer.city,
                "type": customer.customer_type,
                "credit_limit": safe_float(customer.credit_limit),
                "outstanding": safe_float(customer.outstanding_amount),
                "notes": customer.notes,
            },
            "orders_count": len(orders),
            "total_business": sum(safe_float(o.total_amount) for o in orders),
            "recent_orders": [
                {
                    "order_number": o.order_number,
                    "date": safe_iso(o.order_date),
                    "total": safe_float(o.total_amount),
                    "status": o.status,
                    "source": o.source,
                    "message": o.original_message,
                }
                for o in orders
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Customer detail error: {str(e)}")


# ==================== PRODUCTS ====================

@router.get("/products")
def get_products(db: Session = Depends(get_db)):
    """Get all products with stock info"""
    try:
        products = db.query(Product).all()
        result = []
        for p in products:
            inv = db.query(Inventory).filter(Inventory.product_id == p.id).first()
            result.append({
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "category": p.category,
                "cost_price": safe_float(p.cost_price),
                "selling_price": safe_float(p.selling_price),
                "mrp": safe_float(p.mrp),
                "gst_rate": safe_float(p.gst_rate),
                "unit": p.unit,
                "stock": inv.current_stock if inv else 0,
                "reorder_level": inv.reorder_level if inv else 0,
                "needs_reorder": (inv.current_stock <= inv.reorder_level) if inv else False,
                "location": inv.warehouse_location if inv else None,
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Products error: {str(e)}")


@router.get("/low-stock")
def get_low_stock(db: Session = Depends(get_db)):
    """⚠️ Products needing reorder"""
    try:
        low_stock = db.query(Inventory, Product).join(
            Product, Inventory.product_id == Product.id
        ).filter(Inventory.current_stock <= Inventory.reorder_level).all()
        
        return {
            "count": len(low_stock),
            "alert": f"⚠️ {len(low_stock)} products need reordering" if low_stock else "✅ All stock healthy",
            "products": [
                {
                    "product_name": product.name,
                    "sku": product.sku,
                    "category": product.category,
                    "current_stock": inv.current_stock,
                    "reorder_level": inv.reorder_level,
                    "recommended_order": inv.reorder_quantity,
                    "urgency": "🔴 Critical" if inv.current_stock < (inv.reorder_level * 0.5) else "🟡 Warning",
                    "estimated_cost": f"₹{safe_float(product.cost_price) * inv.reorder_quantity:,.2f}"
                }
                for inv, product in low_stock
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Low stock error: {str(e)}")


# ==================== ORDERS ====================

@router.get("/orders")
def get_orders(db: Session = Depends(get_db)):
    """Get all orders"""
    try:
        orders = db.query(Order).order_by(Order.order_date.desc()).all()
        result = []
        for o in orders:
            customer = db.query(Customer).filter(Customer.id == o.customer_id).first()
            items_count = db.query(OrderItem).filter(OrderItem.order_id == o.id).count()
            
            result.append({
                "id": o.id,
                "order_number": o.order_number,
                "customer_name": customer.name if customer else "Unknown",
                "status": o.status,
                "source": o.source,
                "total": safe_float(o.total_amount),
                "items_count": items_count,
                "order_date": safe_iso(o.order_date),
                "delivery_date": safe_iso(o.delivery_date),
                "whatsapp_message": o.original_message,
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orders error: {str(e)}")


@router.get("/whatsapp-orders")
def get_whatsapp_orders(db: Session = Depends(get_db)):
    """📱 Orders from WhatsApp"""
    try:
        orders = db.query(Order).filter(Order.source == "whatsapp").all()
        return {
            "count": len(orders),
            "orders": [
                {
                    "order_number": o.order_number,
                    "customer_id": o.customer_id,
                    "original_whatsapp_message": o.original_message,
                    "total": safe_float(o.total_amount),
                    "status": o.status,
                    "date": safe_iso(o.order_date),
                }
                for o in orders
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WhatsApp orders error: {str(e)}")


# ==================== INVOICES ====================

@router.get("/invoices")
def get_invoices(db: Session = Depends(get_db)):
    """Get all invoices"""
    try:
        invoices = db.query(Invoice).order_by(Invoice.invoice_date.desc()).all()
        result = []
        for inv in invoices:
            order = db.query(Order).filter(Order.id == inv.order_id).first()
            customer = db.query(Customer).filter(Customer.id == order.customer_id).first() if order else None
            
            status_emoji = {
                "paid": "✅",
                "overdue": "🔴",
                "partially_paid": "🟡",
                "draft": "📝",
                "sent": "📤",
            }.get(inv.status, "❓")
            
            result.append({
                "invoice_number": inv.invoice_number,
                "customer": customer.name if customer else "Unknown",
                "status": inv.status,
                "status_emoji": status_emoji,
                "total": safe_float(inv.total_amount),
                "paid": safe_float(inv.paid_amount),
                "balance": safe_float(inv.balance_amount),
                "invoice_date": safe_iso(inv.invoice_date),
                "due_date": safe_iso(inv.due_date),
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invoices error: {str(e)}")


@router.get("/overdue-invoices")
def get_overdue_invoices(db: Session = Depends(get_db)):
    """💰 PAYMENT INTELLIGENCE - Overdue invoices with Hindi reminders!"""
    try:
        overdue = db.query(Invoice).filter(Invoice.status == "overdue").all()
        total_amount = sum(safe_float(inv.balance_amount) for inv in overdue)
        
        result = []
        today = date.today()
        
        for inv in overdue:
            order = db.query(Order).filter(Order.id == inv.order_id).first()
            customer = db.query(Customer).filter(Customer.id == order.customer_id).first() if order else None
            
            # Calculate days overdue safely
            days_overdue = 0
            if inv.due_date:
                # Handle both date and datetime objects
                due_date = inv.due_date if isinstance(inv.due_date, date) else inv.due_date.date()
                days_overdue = (today - due_date).days
            
            # Auto-draft Hindi reminder
            customer_name = customer.name if customer else "Sir"
            reminder = (
                f"Namaste {customer_name}, "
                f"aapka payment ₹{safe_float(inv.balance_amount):,.2f} "
                f"(Invoice {inv.invoice_number}) "
                f"{days_overdue} days se pending hai. "
                f"Kripya payment karein. Dhanyawad! 🙏"
            )
            
            result.append({
                "invoice_number": inv.invoice_number,
                "customer": customer_name,
                "phone": customer.phone if customer else None,
                "whatsapp": customer.whatsapp_number if customer else None,
                "amount_pending": safe_float(inv.balance_amount),
                "due_date": safe_iso(inv.due_date),
                "days_overdue": days_overdue,
                "suggested_reminder": reminder,
            })
        
        return {
            "count": len(overdue),
            "total_overdue_amount": total_amount,
            "alert": f"🔴 ₹{total_amount:,.0f} pending from {len(overdue)} customers",
            "invoices": result
        }
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Overdue error: {str(e)}\n{traceback.format_exc()}")