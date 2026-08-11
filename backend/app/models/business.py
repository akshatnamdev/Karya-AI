"""
Business Model - The actual business using Karya AI
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Business(Base):
    __tablename__ = "businesses"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(200), nullable=False)
    business_type = Column(String(50), nullable=True)  # wholesaler, retailer, pharmacy, manufacturer
    
    # Legal Info
    gst_number = Column(String(20), nullable=True, index=True)
    pan_number = Column(String(15), nullable=True)
    
    # Contact
    email = Column(String(120), nullable=True)
    phone = Column(String(15), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(50), nullable=True)
    state = Column(String(50), nullable=True)
    pincode = Column(String(10), nullable=True)
    
    # Owner
    #owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Business Settings (JSON stored as text for now)
    currency = Column(String(10), default="INR")
    timezone = Column(String(50), default="Asia/Kolkata")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="business", foreign_keys="User.business_id")
    #owner = relationship("User", foreign_keys=[owner_id])
    customers = relationship("Customer", back_populates="business")
    products = relationship("Product", back_populates="business")
    orders = relationship("Order", back_populates="business")
    
    def __repr__(self):
        return f"<Business(id={self.id}, name='{self.name}')>"