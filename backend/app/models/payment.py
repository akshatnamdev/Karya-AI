"""
Payment Model - Payments received against invoices
+ PaymentLink for secure public gateway checkout (Razorpay, etc.)
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Numeric,
    Date,
    Boolean,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String(50), unique=True, nullable=False, index=True)

    # Amount
    amount = Column(Numeric(12, 2), nullable=False)

    # Method: cash, upi, bank_transfer, cheque, card, other, razorpay
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

    # =========================================================================
    # NEW (gateway / payment-link) — all additive, nullable, safe for old rows
    # =========================================================================

    # Optional link to secure public checkout
    payment_link_id = Column(
        Integer, ForeignKey("payment_links.id"), nullable=True, index=True
    )

    # Tenant / party context (optional for legacy cash rows)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)

    currency = Column(String(10), default="INR", nullable=True)

    # created | authorized | captured | failed | refunded | manual
    # Legacy cash/UPI rows can use "manual" or leave default
    status = Column(String(20), default="manual", nullable=True, index=True)

    # razorpay | payu | manual | null
    provider = Column(String(30), nullable=True, index=True)
    provider_order_id = Column(String(100), nullable=True, index=True)
    provider_payment_id = Column(String(100), nullable=True, unique=True, index=True)

    # True ONLY after webhook/signature verification (never from frontend alone)
    signature_verified = Column(Boolean, default=False, nullable=True)

    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Minimal audit payload from gateway (no secrets)
    raw_event = Column(JSON, nullable=True)

    # Relationship to payment link (optional)
    payment_link = relationship(
        "PaymentLink",
        back_populates="payments",
        foreign_keys=[payment_link_id],
    )

    def __repr__(self):
        return f"<Payment(number='{self.payment_number}', amount={self.amount})>"


class PaymentLink(Base):
    """
    NEW model — secure public payment URL: /pay/{token}
    Full remaining invoice balance only (v1).
    """
    __tablename__ = "payment_links"

    id = Column(Integer, primary_key=True, index=True)

    # Public token in URL
    token = Column(String(64), unique=True, nullable=False, index=True)

    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)

    # Locked amount at creation = full remaining balance
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR")

    # created | opened | paid | expired | cancelled
    status = Column(String(20), default="created", index=True)

    provider = Column(String(30), default="razorpay")
    provider_order_id = Column(String(100), nullable=True, index=True)

    expires_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    invoice = relationship("Invoice", backref="payment_links")
    payments = relationship(
        "Payment",
        back_populates="payment_link",
        foreign_keys="Payment.payment_link_id",
    )

    def __repr__(self):
        return f"<PaymentLink(token={self.token[:8]}..., invoice_id={self.invoice_id})>"