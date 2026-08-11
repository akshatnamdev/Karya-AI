"""
Audit Log Model - Track all important actions in the system
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Action
    action = Column(String(100), nullable=False, index=True)  
    # create_order, update_customer, delete_product, etc.
    
    entity_type = Column(String(50), nullable=True)  # order, customer, etc.
    entity_id = Column(Integer, nullable=True)
    
    # Changes
    changes = Column(JSON, nullable=True)  # {"before": {...}, "after": {...}}
    
    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(action='{self.action}', user_id={self.user_id})>"