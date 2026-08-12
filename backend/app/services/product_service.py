"""
Karya AI - Product Service
Business logic for products and inventory
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.inventory import Inventory
from app.utils.formatters import safe_float, format_currency


class ProductService:
    """Handles all product and inventory-related business logic"""
    
    @staticmethod
    def get_all_products(db: Session) -> list:
        """
        Get all products with their inventory info
        
        Returns:
            list: List of product dictionaries with stock info
        """
        products = db.query(Product).all()
        return [
            ProductService._format_product_with_stock(product, db) 
            for product in products
        ]
    
    @staticmethod
    def get_product_detail(db: Session, product_id: int) -> dict:
        """
        Get single product detail with inventory
        
        Args:
            product_id: ID of the product
            
        Returns:
            dict: Product info with inventory
            
        Raises:
            HTTPException: 404 if product not found
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        
        return ProductService._format_product_with_stock(product, db)
    
    @staticmethod
    def get_low_stock_products(db: Session) -> dict:
        """
        Get products that need reordering (inventory intelligence!)
        
        Returns:
            dict: Alert with low-stock products list
        """
        # Join Inventory and Product where stock is low
        low_stock = db.query(Inventory, Product).join(
            Product, Inventory.product_id == Product.id
        ).filter(
            Inventory.current_stock <= Inventory.reorder_level
        ).all()
        
        return {
            "count": len(low_stock),
            "alert": ProductService._get_low_stock_message(len(low_stock)),
            "products": [
                ProductService._format_low_stock_product(inv, product)
                for inv, product in low_stock
            ]
        }
    
    # ==================== PRIVATE HELPER METHODS ====================
    
    @staticmethod
    def _format_product_with_stock(product: Product, db: Session) -> dict:
        """Format product with inventory data"""
        inv = db.query(Inventory).filter(
            Inventory.product_id == product.id
        ).first()
        
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
    def _format_low_stock_product(inv: Inventory, product: Product) -> dict:
        """Format low-stock product with urgency info"""
        # Calculate urgency level
        urgency = ProductService._calculate_urgency(
            inv.current_stock, 
            inv.reorder_level
        )
        
        # Calculate estimated reorder cost
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
    def _calculate_urgency(current_stock: int, reorder_level: int) -> str:
        """Calculate urgency level based on stock levels"""
        if current_stock < (reorder_level * 0.5):
            return "🔴 Critical"
        elif current_stock < reorder_level:
            return "🟡 Warning"
        else:
            return "🟢 Healthy"
    
    @staticmethod
    def _get_low_stock_message(count: int) -> str:
        """Generate low stock alert message"""
        if count == 0:
            return "✅ All stock levels healthy"
        return f"⚠️ {count} products need reordering"