"""
Karya AI - Data Formatters
Reusable helper functions for safe data conversion
"""
from typing import Optional, Any
from datetime import datetime, date


def safe_float(value: Any) -> float:
    """Convert Decimal/None to float safely"""
    if value is None:
        return 0.0
    return float(value)


def safe_int(value: Any) -> int:
    """Convert to int safely"""
    if value is None:
        return 0
    return int(value)


def safe_iso(dt: Any) -> Optional[str]:
    """Convert datetime to ISO string safely"""
    if dt is None:
        return None
    if isinstance(dt, (datetime, date)):
        return dt.isoformat()
    return str(dt)


def format_currency(amount: Any, currency: str = "₹") -> str:
    """Format amount as Indian currency"""
    value = safe_float(amount)
    return f"{currency}{value:,.2f}"


def calculate_days_between(later_date: Any, earlier_date: Any) -> int:
    """Calculate days between two dates safely"""
    if not later_date or not earlier_date:
        return 0
    
    if isinstance(later_date, datetime):
        later_date = later_date.date()
    if isinstance(earlier_date, datetime):
        earlier_date = earlier_date.date()
    
    return (later_date - earlier_date).days
