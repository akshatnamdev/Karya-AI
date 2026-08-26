import time
import os
from sqlalchemy.orm import Session

from app.services.ai_service import ai_service
from app.services.ai_cache_service import AICache
from app.services.demo_mode_service import DemoModeService
from app.rag.business_context import BusinessContextBuilder
from app.schemas.ai import AIQuery, AIResponse


class AIAssistantService:
    """AI Business Assistant with caching, demo mode, and fallback"""
    
    @staticmethod
    def ask_question(db: Session, query: AIQuery, scope: dict, use_demo: bool = False) -> AIResponse:
        """Main method with 4-layer protection and strict RBAC"""
        start_time = time.time()
        
        # ==================== LAYER 1: DEMO MODE ====================
        if use_demo or os.getenv("DEMO_MODE", "false").lower() == "true":
            demo_response = DemoModeService.get_demo_response(query.question)
            if demo_response:
                return AIResponse(**demo_response)
        
        # ==================== LAYER 2: CACHE CHECK ====================
        # Cache key must include the SCOPE (business_id + customer_id) 
        cache_scope_key = f"{scope['scope']}_{scope['business_id']}_{scope['customer_id']}"
        cached = AICache.get(query.question, query.language, cache_scope_key)
        if cached:
            return AIResponse(**cached)
        
        # ==================== LAYER 3: FRESH API CALL ====================
        try:
            business_context = BusinessContextBuilder.build_full_context(db, scope)
        except Exception as e:
            print(f"Error building context: {e}")
            business_context = "Data temporarily unavailable."
        
        prompt = AIAssistantService._build_prompt(
            business_context=business_context,
            user_question=query.question,
            language=query.language,
            role=scope["scope"]
        )
        
        # ==================== LAYER 4: MODEL FALLBACK ====================
        ai_result = ai_service.generate(prompt=prompt, model_type="fast", max_retries=2)
        
        if ai_result.get("status") == "error":
            ai_result = ai_service.generate(prompt=prompt, model_type="smart", max_retries=2)
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        if ai_result.get("status") == "error":
            error_msg = ai_result.get("message", "AI is temporarily unavailable")
            demo_response = DemoModeService.get_demo_response(query.question)
            if demo_response:
                return AIResponse(**demo_response)
            
            return AIResponse(
                question=query.question,
                answer=AIAssistantService._get_friendly_error_message(error_msg),
                model_used=ai_result.get("model", "unknown"),
                response_time_ms=response_time_ms,
                sources=[],
                detected_language="english"
            )
        
        detected_language = AIAssistantService._detect_language(query.question)
        
        response_data = {
            "question": query.question,
            "answer": ai_result.get("response", "").strip(),
            "model_used": ai_result.get("model", "unknown"),
            "response_time_ms": response_time_ms,
            "sources": AIAssistantService._get_sources(),
            "detected_language": detected_language
        }
        
        AICache.set(query.question, query.language, cache_scope_key, response_data)
        
        return AIResponse(**response_data)
    
    @staticmethod
    def get_business_summary(db: Session, scope: dict) -> AIResponse:
        """Get AI business summary"""
        query = AIQuery(
            question="Give me a brief business summary. Include total customers, revenue, outstanding payments, and any critical alerts. Keep it under 150 words.",
            language="hinglish"
        )
        return AIAssistantService.ask_question(db, query, scope)
    
    # ==================== PRIVATE HELPERS ====================
    
    @staticmethod
    def _build_prompt(business_context: str, user_question: str, language: str, role: str) -> str:
        language_instruction = AIAssistantService._get_language_instruction(language)
        
        if role == "customer":
            persona = """You are Karya, a helpful shopping and account assistant for this business. You are talking to a CUSTOMER.
Your job is to help them check their order status, pending invoices, or browse available products in the catalog.
If the customer says hello, asks for help, or asks general questions, be welcoming and let them know you can help them check their orders, pending bills, or product catalog.
If they ask about other customers or business internal data, politely inform them you can only share details related to their own account."""
        elif role == "business":
            persona = """You are Karya, an intelligent business assistant for the BUSINESS OWNER.
You have access to the full business performance data, financials, inventory, and customer account details. Help the owner manage their business effectively."""
        else:
            persona = "You are Karya, a Platform Admin assistant with system-wide visibility."

        prompt = f"""{persona}

BUSINESS & ACCOUNT DATA:
{business_context}

USER QUESTION: {user_question}

INSTRUCTIONS:
1. Answer ONLY from the data above. Never invent numbers .
2. Answer ONLY based on the data above.
3. Be minimal and direct. Prefer short lines over long paragraphs.
4. {language_instruction}
5. Use ₹ with Indian number formatting (e.g. ₹12,320).
6. STATUS DOT RULES (STRICT - ACCORDING TO REAL STATUS):
   - 🔴 = Any OVERDUE invoice/payment, or CRITICAL low stock (stock < 50% of reorder level).
   - 🟡 = Any pending payment that is NOT overdue yet, or WARNING low stock (stock <= reorder level).
   - 🟢 = Fully paid, zero dues, or healthy stock (> reorder level).
   - Rules per section:
     * Overdue customer -> MUST use 🔴
     * Pending customer (no overdue) -> MUST use 🟡
     * No dues customer -> MUST use 🟢
     * Critical stock -> MUST use 🔴
     * Low stock -> MUST use 🟡
     * Healthy stock -> MUST use 🟢
7. Structure:
   - Lead with the answer in 1–2 lines
   - Then short bullet or numbered facts if needed
   - Optional one-line action at the end (no emoji unless status)
8. Labels can be bold Markdown (**Label:**) but keep the message compact.
9. No greetings like "Namaste!" unless the user greeted first.
10. No filler phrases ("Based on our data", "Here is the record").


ANSWER:"""
        return prompt
        
    @staticmethod
    def _get_language_instruction(language: str) -> str:
        instructions = {
            "hindi": "Answer in Hindi (Devanagari script)",
            "english": "Answer in English",
            "hinglish": "Answer in Hinglish (Hindi words in Roman script)",
            "auto": "Match the language of the question"
        }
        return instructions.get(language, instructions["auto"])
    
    @staticmethod
    def _detect_language(text: str) -> str:
        hindi_chars = ['ा', 'ि', 'ी', 'क', 'ख', 'ग', 'च', 'ज', 'त', 'न', 'र', 'स', 'ह']
        hinglish_words = ['kitne', 'kitna', 'hai', 'hain', 'kya', 'ka', 'ki', 'ke', 'aur', 'aaj']
        
        text_lower = text.lower()
        if any(char in text for char in hindi_chars): return "hindi"
        if any(word in text_lower for word in hinglish_words): return "hinglish"
        return "english"
    
    @staticmethod
    def _get_sources() -> list:
        return ["customers table", "products table", "inventory table", "orders table", "invoices table"]
    
    @staticmethod
    def _get_friendly_error_message(error: str) -> str:
        error_lower = error.lower()
        if "503" in error or "unavailable" in error_lower:
            return "Karya AI is experiencing high demand. Please try again in a few moments."
        if "429" in error or "quota" in error_lower:
            return "API quota reached. Please wait a minute and try again."
        return "AI temporarily unavailable. Please try again."