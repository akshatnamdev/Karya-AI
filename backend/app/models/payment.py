"""
Payment Model - Payments received against invoices
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Amount
    amount = Column(Numeric(12, 2), nullable=False)
    
    # Method: cash, upi, bank_transfer, cheque, card, other
    payment_method = Column(String(20), nullable=False)
    
    # Transaction details
    transaction_id = Column(String(100), nullable=True)
    reference_number = Column(String(100), nullable=True)  # Cheque number, UPI ref, etc.
    
    # Date
    payment_date = Column(Date, nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Foreign Key
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(number='{self.payment_number}', amount={self.amount})>"