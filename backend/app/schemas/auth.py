"""
Authentication Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    phone: Optional[str] = Field(None, max_length=15)
    business_name: Optional[str] = Field(None, max_length=200)
    business_type: Optional[str] = Field("wholesaler", max_length=50)
    city: Optional[str] = Field(None, max_length=50) # Added city


class CustomerRegister(BaseModel):
    """Customer signs up to a specific business's portal"""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    phone: str = Field(..., max_length=15)
    business_id: int = Field(..., description="Business they want to order from")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    business_id: Optional[int] = None
    customer_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserResponse
    redirect_to: str  # Where frontend should navigate after login