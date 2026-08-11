"""
Conversation Model - AI chat conversations with users
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Content
    user_query = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    
    # AI Metadata
    model_used = Column(String(100), nullable=True)  # e.g., gemini-flash-latest
    tokens_used = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Grounding & Sources
    sources = Column(JSON, nullable=True)  # List of source records used
    confidence_score = Column(Integer, nullable=True)  # 0-100
    
    # Language
    detected_language = Column(String(10), default="en")  # en, hi, hinglish
    
    # Category: query, action, analysis, summary
    conversation_type = Column(String(20), default="query")
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, query='{self.user_query[:50]}...')>"