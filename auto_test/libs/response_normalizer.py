"""
Response normalization helpers for handling different auth modes.

When backend auth is disabled, some endpoints return wrapped responses
like {"strategies": [...]} instead of direct lists [...].

These helpers normalize responses to work with both formats.
"""


def normalize_list_response(data, key=None):
    """
    Normalize list responses that may be wrapped in a dict.
    
    Args:
        data: Response data (can be list or dict)
        key: Optional key to extract from dict (e.g., 'strategies', 'versions')
    
    Returns:
        List data, extracted from dict if needed
    
    Examples:
        >>> normalize_list_response([1, 2, 3])
        [1, 2, 3]
        >>> normalize_list_response({"strategies": [1, 2, 3]}, "strategies")
        [1, 2, 3]
        >>> normalize_list_response({"strategies": [1, 2, 3]})  # auto-detect
        [1, 2, 3]
    """
    # If already a list, return as-is
    if isinstance(data, list):
        return data
    
    # If dict, try to extract the list
    if isinstance(data, dict):
        # If key provided, use it
        if key and key in data:
            return data[key]
        
        # Auto-detect: find first list value
        for value in data.values():
            if isinstance(value, list):
                return value
    
    # Return as-is if can't normalize
    return data


def normalize_dict_response(data):
    """
    Normalize dict responses (most responses stay the same).
    
    Args:
        data: Response data
    
    Returns:
        Dict data as-is
    """
    return data
