"""
Invoice Model - Bills generated for orders
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Status: draft, sent, paid, partially_paid, overdue, cancelled
    status = Column(String(20), default="draft", index=True)
    
    # Amounts
    subtotal = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(12, 2), nullable=False)
    paid_amount = Column(Numeric(12, 2), default=0)
    balance_amount = Column(Numeric(12, 2), nullable=False)
    
    # Dates
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    paid_date = Column(Date, nullable=True)
    
    # File
    pdf_url = Column(String(500), nullable=True)
    
    # Notes
    terms = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Foreign Key
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="invoice")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Invoice(number='{self.invoice_number}', total={self.total_amount})>"