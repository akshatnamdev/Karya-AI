"""
Product Service - role-aware
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.inventory import Inventory, StockMovement
from datetime import datetime  # if not already
from app.utils.formatters import safe_float, format_currency
from datetime import datetime
from fastapi import HTTPException


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

    @staticmethod
    def create_product(db: Session, business_id: int, product_data: dict) -> dict:
        """
        Creates a product and its associated inventory record simultaneously.
        Used by both Manual UI and AI Assistant.
        """
        # 1. Create the Product
        new_product = Product(
            business_id=business_id,
            name=product_data["name"],
            sku=product_data.get("sku"),
            category=product_data.get("category"),
            description=product_data.get("description"),
            cost_price=product_data.get("cost_price", 0),
            selling_price=product_data["selling_price"],
            mrp=product_data.get("mrp"),
            unit=product_data.get("unit", "pcs"),
            is_active=True
        )
        db.add(new_product)
        db.flush() # Flush to get the new_product.id

        # 2. Create the Inventory tracking record
        new_inventory = Inventory(
            product_id=new_product.id,
            current_stock=product_data.get("initial_stock", 0),
            reorder_level=product_data.get("reorder_level", 10),
            reorder_quantity=product_data.get("reorder_quantity", 50)
        )
        db.add(new_inventory)
        
        # 3. Commit transaction
        db.commit()
        db.refresh(new_product)
        
        return ProductService._format_product_with_stock(new_product, db)    
    
    @staticmethod
    def delete_product(db: Session, business_id: int, product_id: int) -> dict:
        """
        Soft-delete: is_active=False so past orders still resolve product names.
        """
        product = (
            db.query(Product)
            .filter(Product.id == product_id, Product.business_id == business_id)
            .first()
        )
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        product.is_active = False
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to delete product")

        return {
            "ok": True,
            "id": product.id,
            "name": product.name,
            "message": f"Product '{product.name}' deactivated (hidden from catalog)",
        }

    @staticmethod
    def delete_product(db: Session, business_id: int, product_id: int) -> dict:
        product = (
            db.query(Product)
            .filter(Product.id == product_id, Product.business_id == business_id)
            .first()
        )
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        product.is_active = False
        try:
            db.commit()
            db.refresh(product)
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to deactivate product")

        return {
            "ok": True,
            "id": product.id,
            "name": product.name,
            "is_active": False,
            "message": f"Product '{product.name}' deactivated (hidden from customer catalog)",
        }

    @staticmethod
    def activate_product(db: Session, business_id: int, product_id: int) -> dict:
        """Restore product to customer catalog."""
        product = (
            db.query(Product)
            .filter(Product.id == product_id, Product.business_id == business_id)
            .first()
        )
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        product.is_active = True
        try:
            db.commit()
            db.refresh(product)
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to activate product")

        return ProductService._format_product_with_stock(product, db)

    @staticmethod
    def update_stock(
        db: Session,
        business_id: int,
        product_id: int,
        mode: str,
        quantity: int,
        reason: str = None,
    ) -> dict:
        """
        Unified stock update for Business UI + AI Assistant.
        mode: "set" | "add" | "remove"
        """
        mode = (mode or "").lower().strip()
        if mode not in ("set", "add", "remove"):
            raise HTTPException(
                status_code=400,
                detail="mode must be one of: set, add, remove",
            )

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="quantity must be an integer")

        if quantity < 0:
            raise HTTPException(status_code=400, detail="quantity cannot be negative")

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id,
                Product.business_id == business_id,
            )
            .first()
        )
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        inventory = (
            db.query(Inventory)
            .filter(Inventory.product_id == product_id)
            .first()
        )
        if not inventory:
            # Create inventory row if missing (safe for older products)
            inventory = Inventory(
                product_id=product_id,
                current_stock=0,
                reorder_level=10,
                reorder_quantity=50,
            )
            db.add(inventory)
            db.flush()

        stock_before = int(inventory.current_stock or 0)

        if mode == "set":
            stock_after = quantity
            movement_type = "adjustment"
            movement_qty = abs(stock_after - stock_before)
        elif mode == "add":
            stock_after = stock_before + quantity
            movement_type = "in"
            movement_qty = quantity
        else:  # remove
            if quantity > stock_before:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot remove {quantity}. Current stock is {stock_before}",
                )
            stock_after = stock_before - quantity
            movement_type = "out"
            movement_qty = quantity

        inventory.current_stock = stock_after
        try:
            inventory.last_stock_check = datetime.utcnow()
        except Exception:
            pass

        db.add(
            StockMovement(
                product_id=product_id,
                movement_type=movement_type,
                quantity=movement_qty,
                reason=reason or f"stock_{mode}",
                reference_type="manual_or_ai",
                reference_id=None,
                stock_before=stock_before,
                stock_after=stock_after,
                notes=reason,
            )
        )

        try:
            db.commit()
            db.refresh(product)
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to update stock")

        return ProductService._format_product_with_stock(product, db)


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

    @staticmethod
    def find_by_name(db: Session, business_id: int, name: str, active_only: bool = False):
        q = db.query(Product).filter(Product.business_id == business_id)
        if active_only:
            q = q.filter(Product.is_active == True)
        p = q.filter(Product.name.ilike(name.strip())).first()
        if p:
            return p
        return q.filter(Product.name.ilike(f"%{name.strip()}%")).first()