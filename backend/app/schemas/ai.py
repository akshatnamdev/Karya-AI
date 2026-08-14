from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==================== REQUEST SCHEMAS ====================

class AIQuery(BaseModel):
    """Schema for user's question to AI"""
    question: str = Field(
        ..., 
        min_length=3, 
        max_length=500,
        description="Your question in Hindi/English/Hinglish"
    )
    language: Optional[str] = Field(
        "auto",
        description="Response language: 'hindi', 'english', 'hinglish', or 'auto'"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Kitne customers hain?",
                "language": "auto"
            }
        }


# ==================== RESPONSE SCHEMAS ====================

class AIResponse(BaseModel):
    """Schema for AI response"""
    question: str
    answer: str
    model_used: str
    response_time_ms: int
    sources: List[str] = Field(default_factory=list)
    detected_language: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Kitne customers hain?",
                "answer": "Aapke paas 3 customers hain: Raj Traders, Sharma Medical Store, aur Gupta Agencies.",
                "model_used": "models/gemini-flash-latest",
                "response_time_ms": 1250,
                "sources": ["customers table", "business data"],
                "detected_language": "hinglish"
            }
        }


class BusinessContext(BaseModel):
    """Schema for business context sent to AI"""
    business_name: str
    total_customers: int
    total_products: int
    total_orders: int
    total_revenue: float
    total_outstanding: float
    low_stock_count: int
    overdue_count: int
    overdue_amount: float

