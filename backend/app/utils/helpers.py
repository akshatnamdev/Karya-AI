"""
Karya AI - General Helper Functions
"""
from datetime import datetime


def get_greeting_time() -> str:
    """Get appropriate greeting based on time"""
    hour = datetime.now().hour
    if hour < 12:
        return "Good Morning"
    elif hour < 17:
        return "Good Afternoon"
    else:
        return "Good Evening"


def get_urgency_level(current: int, threshold: int) -> str:
    """Determine urgency level for stock alerts"""
    if current < (threshold * 0.5):
        return "🔴 Critical"
    elif current < threshold:
        return "🟡 Warning"
    else:
        return "🟢 Healthy"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."