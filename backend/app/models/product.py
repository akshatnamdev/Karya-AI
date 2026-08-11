"""
Product Model - Products/items sold by the business
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(200), nullable=False, index=True)
    sku = Column(String(50), unique=True, nullable=True, index=True)  # Stock Keeping Unit
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    
    # Pricing
    cost_price = Column(Numeric(12, 2), nullable=True)  # What we bought for
    selling_price = Column(Numeric(12, 2), nullable=False)  # What we sell for
    mrp = Column(Numeric(12, 2), nullable=True)  # Maximum Retail Price
    
    # Tax
    gst_rate = Column(Numeric(5, 2), default=18)  # GST percentage
    hsn_code = Column(String(20), nullable=True)  # HSN/SAC code
    
    # Units
    unit = Column(String(20), default="pcs")  # pcs, kg, ltr, box, etc.
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Image
    image_url = Column(String(500), nullable=True)
    
    # Foreign Key
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    business = relationship("Business", back_populates="products")
    inventory = relationship("Inventory", back_populates="product", uselist=False)
    order_items = relationship("OrderItem", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}')>"