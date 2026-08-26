from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.ai import AIQuery, AIResponse
from app.services.ai_assistant_service import AIAssistantService
from app.services.ai_cache_service import AICache
from app.services.demo_mode_service import DemoModeService
from app.core.dependencies import get_current_user, get_business_scope 



router = APIRouter(
    prefix="/api/ai", 
    tags=[" AI Business Assistant"]
)

# ==================== ASK QUESTION ====================

@router.post("/ask", response_model=AIResponse)
def ask_ai(
    query: AIQuery,
    demo_mode: bool = Query(False, description="Use pre-cached demo responses (saves API calls)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope) # Inject the scope here!
):
   
    # Pass scope to the service
    return AIAssistantService.ask_question(db, query, scope, use_demo=demo_mode)


@router.post("/ask-public", response_model=AIResponse)
def ask_ai_public(
    query: AIQuery,
    demo_mode: bool = Query(False, description="Use pre-cached demo responses (saves API calls)"),
    db: Session = Depends(get_db)
):
    """
     Ask AI without auth (for testing)
    
    Set demo_mode=true to save API quota during testing!
    """
    return AIAssistantService.ask_question(db, query, use_demo=demo_mode)


# ==================== BUSINESS SUMMARY ====================

@router.get("/summary", response_model=AIResponse)
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: dict = Depends(get_business_scope)
):
    return AIAssistantService.get_business_summary(db, scope)

# ==================== CACHE MANAGEMENT ====================

@router.get("/cache/stats")
def get_cache_stats():
    """
     View cache statistics
    
    Shows how many API calls you've saved!
    """
    return AICache.get_stats()


@router.delete("/cache/clear")
def clear_cache():
    """
     Clear all cached responses
    
    Use when data changes significantly
    """
    return AICache.clear()


# ==================== DEMO MODE ====================

@router.get("/demo/questions")
def list_demo_questions():
    """
     List all pre-cached demo questions
    
    Use these for guaranteed responses during demos!
    """
    return {
        "message": "These questions have pre-cached responses (no API calls needed)",
        "count": len(DemoModeService.list_demo_questions()),
        "questions": DemoModeService.list_demo_questions(),
        "tip": "Add ?demo_mode=true to any /ask endpoint to force demo mode"
    }