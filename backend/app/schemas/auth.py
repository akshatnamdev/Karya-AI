"""
Karya AI - Authentication Schemas
Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ==================== REQUEST SCHEMAS ====================

class UserRegister(BaseModel):
    """Schema for user registration"""
    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, max_length=100, description="Password (min 6 chars)")
    phone: Optional[str] = Field(None, max_length=15, description="Phone number")
    business_name: Optional[str] = Field(None, max_length=200, description="Business name")
    business_type: Optional[str] = Field("wholesaler", max_length=50, description="Type of business")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Akshat Namdev",
                "email": "akshat@example.com",
                "password": "secure123",
                "phone": "9876543210",
                "business_name": "My Wholesale Business",
                "business_type": "wholesaler"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="Registered email")
    password: str = Field(..., description="Password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "akshat@example.com",
                "password": "secure123"
            }
        }


# ==================== RESPONSE SCHEMAS ====================

class UserResponse(BaseModel):
    """Schema for user information response"""
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    business_id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserResponse
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGc...",
                "token_type": "bearer",
                "expires_in_minutes": 1440,
                "user": {
                    "id": 1,
                    "name": "Akshat Namdev",
                    "email": "akshat@example.com",
                    "role": "owner"
                }
            }
        }