"""Common route error handling utilities."""
from typing import Optional
from src.utils.exception_handlers import ValidationError


def require_filter(
    before_date: Optional[str],
    tickers: Optional[str],
    older_than_days: Optional[int],
    message: str = "At least one filter parameter is required"
):
    """
    Validate that at least one filter parameter is provided.
    
    Args:
        before_date: Optional date filter
        tickers: Optional ticker filter
        older_than_days: Optional days filter
        message: Custom error message
        
    Raises:
        ValidationError: If no filter is provided
    """
    if not any([before_date, tickers, older_than_days]):
        raise ValidationError(message)


def validate_not_empty(value: str, field_name: str):
    """
    Validate field is not empty.
    
    Args:
        value: Field value to validate
        field_name: Name of field for error message
        
    Raises:
        ValidationError: If value is empty or whitespace
    """
    if not value or not value.strip():
        raise ValidationError(f"{field_name} cannot be empty")


def validate_list_not_empty(items: list, field_name: str):
    """
    Validate list is not empty.
    
    Args:
        items: List to validate
        field_name: Name of field for error message
        
    Raises:
        ValidationError: If list is empty or None
    """
    if not items or len(items) == 0:
        raise ValidationError(f"{field_name} cannot be empty")
