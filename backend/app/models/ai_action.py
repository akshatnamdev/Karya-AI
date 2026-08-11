"""
AI Action Model - Actions proposed by AI awaiting approval
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class AIAction(Base):
    __tablename__ = "ai_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Action Info
    action_type = Column(String(50), nullable=False, index=True)  
    # create_order, send_reminder, update_stock, generate_invoice, etc.
    
    # Status: pending, approved, rejected, executed, failed
    status = Column(String(20), default="pending", index=True)
    
    # Data
    proposed_data = Column(JSON, nullable=False)  # What AI wants to do
    final_data = Column(JSON, nullable=True)      # What was actually done (after edits)
    result_data = Column(JSON, nullable=True)     # Execution result
    
    # Source
    source_message = Column(Text, nullable=True)  # Original message that triggered this
    ai_reasoning = Column(Text, nullable=True)    # Why AI suggested this
    
    # Approval
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Execution
    executed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Foreign Keys
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    approved_by_user = relationship("User", back_populates="ai_actions")
    
    def __repr__(self):
        return f"<AIAction(type='{self.action_type}', status='{self.status}')>"