import time
from sqlalchemy.orm import Session

from app.services.ai_service import ai_service
from app.rag.business_context import BusinessContextBuilder
from app.schemas.ai import AIQuery, AIResponse


class AIAssistantService:
    """AI Business Assistant with RAG-powered responses"""
    
    @staticmethod
    def ask_question(db: Session, query: AIQuery) -> AIResponse:
        """
        Main method - user asks question, AI responds using real business data
        """
        start_time = time.time()
        
        business_context = BusinessContextBuilder.build_full_context(db)
        
        prompt = AIAssistantService._build_prompt(
            business_context=business_context,
            user_question=query.question,
            language=query.language
        )
        
        ai_result = ai_service.generate(
            prompt=prompt,
            model_type="smart"
        )
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        if ai_result.get("status") == "error":
            return AIResponse(
                question=query.question,
                answer=f"Sorry, I encountered an error: {ai_result.get('message', 'Unknown error')}",
                model_used=ai_result.get("model", "unknown"),
                response_time_ms=response_time_ms,
                sources=[],
                detected_language="english"
            )
        
        detected_language = AIAssistantService._detect_language(query.question)
        
        return AIResponse(
            question=query.question,
            answer=ai_result.get("response", "").strip(),
            model_used=ai_result.get("model", "unknown"),
            response_time_ms=response_time_ms,
            sources=AIAssistantService._get_sources(),
            detected_language=detected_language
        )
    
    @staticmethod
    def get_business_summary(db: Session) -> AIResponse:
        """Get an AI-generated business summary"""
        query = AIQuery(
            question="Give me a comprehensive business summary in Hinglish. Include revenue, outstanding payments, low stock alerts, and top customers.",
            language="hinglish"
        )
        return AIAssistantService.ask_question(db, query)
    
    # ==================== PRIVATE HELPERS ====================
    
    @staticmethod
    def _build_prompt(business_context: str, user_question: str, language: str) -> str:
        """Build the prompt for Gemini with context and instructions"""
        
        language_instruction = AIAssistantService._get_language_instruction(language)
        
        prompt = f"""You are Karya AI, an intelligent business assistant for Indian small businesses.

You have access to the following REAL BUSINESS DATA:

{business_context}

USER QUESTION: {user_question}

INSTRUCTIONS:
1. Answer based ONLY on the data provided above.
2. Do NOT make up numbers or information.
3. If the data doesn't have the answer, say so honestly.
4. {language_instruction}
5. Use Indian currency format (₹) with commas (e.g., ₹1,23,456)
6. Be helpful, friendly, and concise.
7. Use emojis where appropriate to make it engaging.
8. Give actionable insights when possible.
9. Format numbers clearly.
10. If asked about specific customer/product/order, use the exact names from data.

ANSWER:"""
        
        return prompt
    
    @staticmethod
    def _get_language_instruction(language: str) -> str:
        """Get language-specific instruction"""
        instructions = {
            "hindi": "Answer in Hindi (Devanagari script). Example: 'आपके पास 3 ग्राहक हैं।'",
            "english": "Answer in English only.",
            "hinglish": "Answer in Hinglish (Hindi words with Roman script). Example: 'Aapke paas 3 customers hain.'",
            "auto": "Detect the language of the user's question and reply in the same language. If Hindi (Devanagari), reply in Hindi. If Hinglish, reply in Hinglish. If English, reply in English."
        }
        return instructions.get(language, instructions["auto"])
    
    @staticmethod
    def _detect_language(text: str) -> str:
        """Simple language detection based on characters"""
        hindi_chars = ['ा', 'ि', 'ी', 'ु', 'ू', 'े', 'ै', 'ो', 'ौ', 'क', 'ख', 'ग', 'घ']
        hinglish_words = ['kitne', 'kitna', 'hai', 'hain', 'kya', 'ka', 'ki', 'ke', 'aur', 'bhi', 'nahi', 'bhej']
        
        text_lower = text.lower()
        
        if any(char in text for char in hindi_chars):
            return "hindi"
        
        if any(word in text_lower for word in hinglish_words):
            return "hinglish"
        
        return "english"
    
    @staticmethod
    def _get_sources() -> list:
        """List data sources used for the response"""
        return [
            "customers table",
            "products table",
            "inventory table",
            "orders table",
            "invoices table",
            "business data"
        ]
    @staticmethod
    def _get_friendly_error_message(error: str) -> str:
        """Convert technical errors to user-friendly messages"""
        error_lower = error.lower()
        
        if "503" in error or "unavailable" in error_lower:
            return "🔄 Karya AI is experiencing high demand right now. Please try again in a few moments."
        
        if "429" in error or "quota" in error_lower:
            return "⏳ We've hit our AI request limit. Please wait a minute and try again."
        
        if "network" in error_lower or "connection" in error_lower:
            return "🌐 Network issue detected. Please check your internet connection."
        
        return f"⚠️ AI temporarily unavailable. Please try again in a moment."