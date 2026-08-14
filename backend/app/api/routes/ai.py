from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.ai import AIQuery, AIResponse
from app.services.ai_assistant_service import AIAssistantService
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/api/ai", 
    tags=["🧠 AI Business Assistant"]
)


# ==================== ASK QUESTION ====================

@router.post("/ask", response_model=AIResponse)
def ask_ai(
    query: AIQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🧠 Ask Karya AI anything about your business
    
    Supports Hindi, English, and Hinglish!
    
    Example questions:
    - "Kitne customers hain?"
    - "Which products are low on stock?"
    - "Aaj kitna sale hua?"
    - "Raj Traders ka status kya hai?"
    - "Show me overdue payments"
    """
    return AIAssistantService.ask_question(db, query)


# ==================== BUSINESS SUMMARY ====================

@router.get("/summary", response_model=AIResponse)
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📊 Get AI-generated business summary in Hinglish
    """
    return AIAssistantService.get_business_summary(db)


# ==================== TEST WITHOUT AUTH (for quick testing) ====================

@router.post("/ask-public", response_model=AIResponse)
def ask_ai_public(
    query: AIQuery,
    db: Session = Depends(get_db)
):
    """
    🧠 Ask AI without authentication (for testing only)
    """
    return AIAssistantService.ask_question(db, query)