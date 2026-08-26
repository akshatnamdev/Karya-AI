"""
User Model - All types of users (platform admin, business owner, customer)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.database import Base


class UserRole(str, enum.Enum):
    """Three role types in Karya AI"""
    PLATFORM_ADMIN = "platform_admin"
    BUSINESS_OWNER = "business_owner"
    CUSTOMER = "customer"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    phone = Column(String(15), nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Role (using enum for safety)
    role = Column(
        SQLEnum(UserRole, name="user_role_enum"),
        default=UserRole.BUSINESS_OWNER,
        nullable=False,
        index=True
    )
    
    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True, index=True)
    # For CUSTOMER role, this links to the customer record in the business
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    business = relationship("Business", back_populates="users", foreign_keys=[business_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    conversations = relationship("Conversation", back_populates="user")
    ai_actions = relationship("AIAction", back_populates="approved_by_user")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    @property
    def is_platform_admin(self):
        return self.role == UserRole.PLATFORM_ADMIN
    
    @property
    def is_business_owner(self):
        return self.role == UserRole.BUSINESS_OWNER
    
    @property
    def is_customer(self):
        return self.role == UserRole.CUSTOMER