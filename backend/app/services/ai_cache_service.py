"""
In-memory cache for AI responses
"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional


class AICache:
    """In-memory cache for AI responses to save API calls"""
    
    _cache: dict = {}
    _stats = {
        "hits": 0,
        "misses": 0,
        "total_requests": 0
    }
    
    CACHE_DURATION_MINUTES = 30
    
    @staticmethod
    def _generate_key(question: str, language: str, scope_key: str = "") -> str:
        """Generate unique cache key from question and role scope"""
        normalized = f"{question.lower().strip()}|{language}|{scope_key}"
        return hashlib.md5(normalized.encode()).hexdigest()
    
    @staticmethod
    def get(question: str, language: str, scope_key: str = "") -> Optional[dict]:
        """Get cached response if exists and not expired"""
        AICache._stats["total_requests"] += 1
        
        key = AICache._generate_key(question, language, scope_key)
        
        if key not in AICache._cache:
            AICache._stats["misses"] += 1
            return None
        
        cached = AICache._cache[key]
        expiry_time = cached["cached_at"] + timedelta(minutes=AICache.CACHE_DURATION_MINUTES)
        
        if datetime.now() > expiry_time:
            del AICache._cache[key]
            AICache._stats["misses"] += 1
            return None
        
        AICache._stats["hits"] += 1
        response = cached["response"].copy()
        response["from_cache"] = True
        return response
    
    @staticmethod
    def set(question: str, language: str, scope_key: str, response: dict) -> None:
        """Save response to cache"""
        key = AICache._generate_key(question, language, scope_key)
        AICache._cache[key] = {
            "response": response,
            "cached_at": datetime.now(),
            "question": question
        }
    
    @staticmethod
    def clear() -> dict:
        count = len(AICache._cache)
        AICache._cache.clear()
        return {"cleared": count, "message": f"Cleared {count} cached responses"}
    
    @staticmethod
    def get_stats() -> dict:
        total = AICache._stats["total_requests"]
        hit_rate = (AICache._stats["hits"] / total * 100) if total > 0 else 0
        return {
            "total_requests": total,
            "cache_hits": AICache._stats["hits"],
            "cache_misses": AICache._stats["misses"],
            "hit_rate_percent": round(hit_rate, 2),
            "currently_cached": len(AICache._cache),
        }