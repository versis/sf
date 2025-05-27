"""
Utility functions for handling ID conversions and extractions.
"""
import re
from typing import Optional
from .logger import log, error

def extract_id_from_extended_id(extended_id: str) -> Optional[int]:
    """
    Extract the numeric database ID from an extended_id string.
    
    Extended ID format: "000000XXX FE F" where XXX is the zero-padded database ID.
    
    Args:
        extended_id: The extended ID string (e.g., "000000057 FE F")
        
    Returns:
        The numeric database ID, or None if extraction fails
        
    Examples:
        >>> extract_id_from_extended_id("000000057 FE F")
        57
        >>> extract_id_from_extended_id("000000001 FE F")
        1
        >>> extract_id_from_extended_id("invalid")
        None
    """
    if not extended_id or not isinstance(extended_id, str):
        return None
    
    try:
        # Split by space and take the first part (the padded ID)
        parts = extended_id.strip().split()
        if len(parts) < 3:  # Should have at least "XXXXXXXXX FE F"
            return None
            
        padded_id = parts[0]
        
        # Validate it's all digits
        if not padded_id.isdigit():
            return None
            
        # Convert to int (this will remove leading zeros)
        db_id = int(padded_id)
        
        log(f"Extracted ID {db_id} from extended_id '{extended_id}'")
        return db_id
        
    except (ValueError, IndexError) as e:
        error(f"Failed to extract ID from extended_id '{extended_id}': {str(e)}")
        return None

def validate_extended_id_format(extended_id: str) -> bool:
    """
    Validate that an extended_id follows the expected format.
    
    Args:
        extended_id: The extended ID string to validate
        
    Returns:
        True if the format is valid, False otherwise
    """
    if not extended_id or not isinstance(extended_id, str):
        return False
    
    # Pattern: 9 digits, space, "FE", space, "F"
    pattern = r'^\d{9} FE F$'
    return bool(re.match(pattern, extended_id.strip()))

def create_extended_id(db_id: int, padding_length: int = 9, suffix: str = "FE F") -> str:
    """
    Create an extended_id from a database ID.
    
    Args:
        db_id: The numeric database ID
        padding_length: Number of digits to pad to (default: 9)
        suffix: The suffix to append (default: "FE F")
        
    Returns:
        The formatted extended_id string
        
    Examples:
        >>> create_extended_id(57)
        "000000057 FE F"
        >>> create_extended_id(1)
        "000000001 FE F"
    """
    padded_id = str(db_id).zfill(padding_length)
    return f"{padded_id} {suffix}" 