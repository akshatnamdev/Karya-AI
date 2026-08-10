"""
Karya AI - AI Service
Handles all interactions with Gemini API
"""
import os
import time
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class AIService:
    """Central AI service for Karya - handles Gemini API calls"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        
        genai.configure(api_key=self.api_key)
        
        # Model selection based on task
        self.models = {
            "fast": "models/gemini-flash-lite-latest",   # Simple tasks - always latest lite
            "smart": "models/gemini-flash-latest",        # Main model - always latest
            "advanced": "models/gemini-flash-latest"      # Same as smart for free tier
        }
        
        # Default model
        self.default_model = "smart"
    
    def generate(
        self, 
        prompt: str, 
        model_type: str = "smart",
        max_retries: int = 3
    ) -> dict:
        """
        Generate content using Gemini
        
        Args:
            prompt: The input prompt
            model_type: 'fast', 'smart', or 'advanced'
            max_retries: Number of retries on rate limit
        
        Returns:
            dict with status, response, and metadata
        """
        model_name = self.models.get(model_type, self.models[self.default_model])
        
        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                
                return {
                    "status": "success",
                    "model": model_name,
                    "response": response.text,
                    "attempts": attempt + 1
                }
            
            except Exception as e:
                error_msg = str(e)
                
                # Handle rate limit
                if "429" in error_msg or "quota" in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = 15 * (attempt + 1)  # Exponential backoff
                        print(f"⏳ Rate limited. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                
                # Other errors
                return {
                    "status": "error",
                    "model": model_name,
                    "message": error_msg,
                    "attempts": attempt + 1
                }
        
        return {
            "status": "error",
            "message": "Max retries exceeded",
            "attempts": max_retries
        }
    
    def list_available_models(self) -> list:
        """List all models available with free tier"""
        try:
            models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    models.append({
                        "name": model.name,
                        "display_name": model.display_name
                    })
            return models
        except Exception as e:
            return [{"error": str(e)}]


# Singleton instance
ai_service = AIService()