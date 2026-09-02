"""
Karya AI - Application Configuration
Loads environment variables and provides settings
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App
    APP_NAME: str = "Karya AI"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # Gemini API
    GEMINI_API_KEY: str
    
    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Payments
    PAYMENT_PROVIDER: str = "razorpay"  # razorpay | none
    PAYMENT_PUBLIC_BASE_URL: str = "http://localhost:5173"  # prod: https://pay.karyaai.com
    PAYMENT_LINK_EXPIRY_HOURS: int = 72

    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
        
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()