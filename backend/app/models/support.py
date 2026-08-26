"""
Support Ticket + Message models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.database import Base


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    PENDING_ADMIN = "pending_admin"
    RESOLVED = "resolved"


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(200), nullable=False)
    status = Column(
        SQLEnum(TicketStatus, name="support_ticket_status"),
        default=TicketStatus.OPEN,
        nullable=False,
        index=True,
    )

    # who opened
    opened_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # scope
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True, index=True)
    # who it's addressed to right now
    assigned_to_role = Column(String(30), nullable=False, default="business_owner")
    # business_owner | platform_admin

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    messages = relationship(
        "SupportMessage", back_populates="ticket", cascade="all, delete-orphan"
    )


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sender_role = Column(String(30), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ticket = relationship("SupportTicket", back_populates="messages")