"""
Inventory Models - Stock tracking and movements
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Stock Levels
    current_stock = Column(Integer, default=0)
    reserved_stock = Column(Integer, default=0)  # Stock reserved for pending orders
    reorder_level = Column(Integer, default=10)  # Alert when stock drops below this
    reorder_quantity = Column(Integer, default=50)  # Suggested reorder amount
    
    # Location
    warehouse_location = Column(String(100), nullable=True)
    
    # Foreign Key
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_stock_check = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="inventory")
    
    def __repr__(self):
        return f"<Inventory(product_id={self.product_id}, stock={self.current_stock})>"
    
    @property
    def available_stock(self):
        """Actual stock available for new orders"""
        return self.current_stock - self.reserved_stock
    
    @property
    def needs_reorder(self):
        """Check if stock is low"""
        return self.current_stock <= self.reorder_level


class StockMovement(Base):
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Movement Info
    movement_type = Column(String(20), nullable=False)  # in, out, adjustment, return
    quantity = Column(Integer, nullable=False)
    
    # Reason
    reason = Column(String(200), nullable=True)  # sale, purchase, damage, expired, etc.
    reference_type = Column(String(50), nullable=True)  # order, purchase, adjustment
    reference_id = Column(Integer, nullable=True)  # ID of the related record
    
    # Stock levels at time of movement
    stock_before = Column(Integer, nullable=True)
    stock_after = Column(Integer, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Foreign Key
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="stock_movements")
    
    def __repr__(self):
        return f"<StockMovement(type={self.movement_type}, qty={self.quantity})>"