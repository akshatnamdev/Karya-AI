"""
Order Models - Customer orders and line items
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Status: draft, pending, confirmed, processing, shipped, delivered, cancelled
    status = Column(String(20), default="pending", index=True)
    
    # Source: whatsapp, manual, api, phone
    source = Column(String(20), default="manual")
    
    # Financial
    subtotal = Column(Numeric(12, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(12, 2), default=0)
    
    # Dates
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    delivery_date = Column(Date, nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)  # Not shown to customer
    
    # Original message (if from WhatsApp)
    original_message = Column(Text, nullable=True)
    
    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    business = relationship("Business", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    invoice = relationship("Invoice", back_populates="order", uselist=False)
    
    def __repr__(self):
        return f"<Order(number='{self.order_number}', total={self.total_amount})>"


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Item Details
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    discount = Column(Numeric(12, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), nullable=False)
    
    # Foreign Keys
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem(product_id={self.product_id}, qty={self.quantity})>"