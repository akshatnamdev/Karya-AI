"""
User Model - Business owner/manager who uses Karya AI
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    phone = Column(String(15), nullable=True)
    password_hash = Column(String(255), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Role: owner, manager, employee, accountant
    role = Column(String(20), default="owner")
    
    # Foreign Key
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    business = relationship("Business", back_populates="users", foreign_keys=[business_id])
    conversations = relationship("Conversation", back_populates="user")
    ai_actions = relationship("AIAction", back_populates="approved_by_user")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"