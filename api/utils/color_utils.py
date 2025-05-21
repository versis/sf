import re
from typing import Tuple, Optional

from api.utils.logger import log

def hex_to_rgb(hex_color: str, request_id: Optional[str] = None) -> Optional[Tuple[int, int, int]]:
    """Converts a HEX color string to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if not re.match(r"^[0-9a-fA-F]{6}$", hex_color) and not re.match(r"^[0-9a-fA-F]{3}$", hex_color):
        log(f"Invalid HEX format: {hex_color}", request_id=request_id)
        return None 
    
    if len(hex_color) == 3:
        r = int(hex_color[0]*2, 16)
        g = int(hex_color[1]*2, 16)
        b = int(hex_color[2]*2, 16)
    else: # len == 6
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    return (r, g, b)

def rgb_to_cmyk(r: int, g: int, b: int) -> Tuple[int, int, int, int]:
    """Converts an RGB color (0-255) to CMYK (0-100)."""
    if (r, g, b) == (0, 0, 0):
        return 0, 0, 0, 100

    c = 1 - (r / 255.0)
    m = 1 - (g / 255.0)
    y = 1 - (b / 255.0)

    min_cmy = min(c, m, y)
    # Handle case for white to avoid division by zero if 1 - min_cmy is 0
    if min_cmy == 1.0: # This means c, m, y were all 0 (white)
        return 0, 0, 0, 0

    c = (c - min_cmy) / (1 - min_cmy)
    m = (m - min_cmy) / (1 - min_cmy)
    y = (y - min_cmy) / (1 - min_cmy)
    k = min_cmy

    return round(c * 100), round(m * 100), round(y * 100), round(k * 100) 

# --- New utility for desaturation ---
def desaturate_hex_color(hex_str: str, amount: float = 0.7, request_id: Optional[str] = None) -> Optional[tuple[int, int, int]]:
    """
    Desaturates a hex color by a specified amount towards grey.

    Args:
        hex_str: The hex color string (e.g., "#RRGGBB").
        amount: The desaturation amount (0.0 to 1.0). 
                0.0 means no change, 1.0 means fully desaturated (grey).
        request_id: Optional request ID for logging.

    Returns:
        A tuple of (R, G, B) for the desaturated color, or None if input is invalid.
    """
    rgb = hex_to_rgb(hex_str, request_id)
    if not rgb:
        return None

    r, g, b = rgb
    
    # Luminosity for grey value (standard formula)
    # Using a common approximation for perceived luminance
    luminance = int(0.299 * r + 0.587 * g + 0.114 * b)
    
    # Interpolate towards the grey value
    r_desat = int(r + (luminance - r) * amount)
    g_desat = int(g + (luminance - g) * amount)
    b_desat = int(b + (luminance - b) * amount)
    
    # Ensure values are within 0-255 range
    r_desat = max(0, min(255, r_desat))
    g_desat = max(0, min(255, g_desat))
    b_desat = max(0, min(255, b_desat))
    
    return (r_desat, g_desat, b_desat) 