"""
Karya AI - Common/Shared Schemas
Used across multiple features
"""
from pydantic import BaseModel
from typing import List, Any


class MessageResponse(BaseModel):
    """Generic success/error message"""
    message: str
    status: str = "success"


class AlertItem(BaseModel):
    """Alert item for dashboards"""
    icon: str
    type: str  # danger, warning, success, info
    message: str
    priority: str  # high, medium, low


class PaginatedResponse(BaseModel):
    """Standard pagination response"""
    total: int
    page: int
    per_page: int
    items: List[Any]