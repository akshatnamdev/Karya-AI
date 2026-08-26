"""
Product Service - role-aware
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.inventory import Inventory
from app.utils.formatters import safe_float, format_currency


class ProductService:
    
    @staticmethod
    def get_all_products(db: Session, scope: dict) -> list:
        q = db.query(Product)
        if scope["scope"] in ("business", "customer"):
            q = q.filter(Product.business_id == scope["business_id"])
        # For customers, only show active products
        if scope["scope"] == "customer":
            q = q.filter(Product.is_active == True)
        
        products = q.all()
        return [ProductService._format_product_with_stock(p, db) for p in products]
    
    @staticmethod
    def get_product_detail(db: Session, product_id: int, scope: dict) -> dict:
        q = db.query(Product).filter(Product.id == product_id)
        if scope["scope"] in ("business", "customer"):
            q = q.filter(Product.business_id == scope["business_id"])
        
        product = q.first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return ProductService._format_product_with_stock(product, db)
    
    @staticmethod
    def get_low_stock_products(db: Session, scope: dict) -> dict:
        # Customers don't need low stock info
        if scope["scope"] == "customer":
            return {"count": 0, "alert": "", "products": []}
        
        q = db.query(Inventory, Product).join(
            Product, Inventory.product_id == Product.id
        ).filter(Inventory.current_stock <= Inventory.reorder_level)
        
        if scope["scope"] == "business":
            q = q.filter(Product.business_id == scope["business_id"])
        
        low_stock = q.all()
        
        return {
            "count": len(low_stock),
            "alert": ProductService._get_low_stock_message(len(low_stock)),
            "products": [
                ProductService._format_low_stock_product(inv, product)
                for inv, product in low_stock
            ]
        }
    
    # ==================== PRIVATE HELPERS ====================
    
    @staticmethod
    def _format_product_with_stock(product, db):
        inv = db.query(Inventory).filter(Inventory.product_id == product.id).first()
        
        return {
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "description": product.description,
            "category": product.category,
            "cost_price": safe_float(product.cost_price),
            "selling_price": safe_float(product.selling_price),
            "mrp": safe_float(product.mrp),
            "gst_rate": safe_float(product.gst_rate),
            "hsn_code": product.hsn_code,
            "unit": product.unit,
            "is_active": product.is_active,
            "stock": inv.current_stock if inv else 0,
            "reorder_level": inv.reorder_level if inv else 0,
            "reorder_quantity": inv.reorder_quantity if inv else 0,
            "needs_reorder": (inv.current_stock <= inv.reorder_level) if inv else False,
            "warehouse_location": inv.warehouse_location if inv else None,
        }
    
    @staticmethod
    def _format_low_stock_product(inv, product):
        urgency = ProductService._calculate_urgency(inv.current_stock, inv.reorder_level)
        estimated_cost = safe_float(product.cost_price) * inv.reorder_quantity
        
        return {
            "product_id": product.id,
            "product_name": product.name,
            "sku": product.sku,
            "category": product.category,
            "current_stock": inv.current_stock,
            "reorder_level": inv.reorder_level,
            "recommended_order": inv.reorder_quantity,
            "urgency": urgency,
            "estimated_cost": format_currency(estimated_cost),
        }
    
    @staticmethod
    def _calculate_urgency(current, reorder):
        if current < (reorder * 0.5):
            return "Critical"
        elif current < reorder:
            return "Warning"
        return "Healthy"
    
    @staticmethod
    def _get_low_stock_message(count):
        if count == 0:
            return "All stock levels healthy"
        return f"{count} products need reordering"