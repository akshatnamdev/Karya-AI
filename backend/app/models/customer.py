"""
Customer Model - Business's customers
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(200), nullable=False, index=True)
    phone = Column(String(15), nullable=True, index=True)
    email = Column(String(120), nullable=True)
    whatsapp_number = Column(String(15), nullable=True)
    
    # Address
    address = Column(Text, nullable=True)
    city = Column(String(50), nullable=True)
    state = Column(String(50), nullable=True)
    pincode = Column(String(10), nullable=True)
    
    # Business Info
    gst_number = Column(String(20), nullable=True)
    customer_type = Column(String(20), default="retail")  # retail, wholesale, distributor
    credit_limit = Column(Numeric(12, 2), default=0)
    outstanding_amount = Column(Numeric(12, 2), default=0)
    
    # Notes
    notes = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # comma-separated tags
    
    # Foreign Key
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_order_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    business = relationship("Business", back_populates="customers")
    orders = relationship("Order", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}')>"