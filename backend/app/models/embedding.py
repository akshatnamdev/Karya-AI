"""
Embedding Model - Vector embeddings for RAG
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.db.database import Base


class Embedding(Base):
    __tablename__ = "embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Source Info
    source_type = Column(String(50), nullable=False, index=True)  
    # customer, product, order, invoice, conversation, document
    source_id = Column(Integer, nullable=False, index=True)
    
    # Content
    content = Column(Text, nullable=False)  # Original text
    
    # Vector (384 dimensions for all-MiniLM-L6-v2 model)
    embedding = Column(Vector(384), nullable=False)
    
    # Metadata
    meta_data = Column(Text, nullable=True)  # JSON metadata
    
    # Foreign Key
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Embedding(source={self.source_type}:{self.source_id})>"