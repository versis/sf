import re
from typing import Tuple, Optional, List, Dict
import colorsys # Added for HLS conversions

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

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Converts an RGB tuple to a HEX color string."""
    return f"#{r:02x}{g:02x}{b:02x}"

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

# --- HLS based color manipulations ---

def _rgb_to_hls(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Converts RGB (0-255) to HLS (0-1 for all components)."""
    return colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)

def _hls_to_rgb(h: float, l: float, s: float) -> Tuple[int, int, int]:
    """Converts HLS (0-1 for all components) to RGB (0-255)."""
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (round(r * 255), round(g * 255), round(b * 255))

def adjust_hls(rgb: Tuple[int, int, int], h_offset_deg: float = 0, l_factor: float = 1.0, s_factor: float = 1.0) -> Tuple[int, int, int]:
    """
    Adjusts Hue, Lightness, and Saturation of an RGB color.
    h_offset_deg: Hue offset in degrees (-360 to 360).
    l_factor: Multiplier for lightness (e.g., 1.1 for 10% brighter, 0.9 for 10% darker).
    s_factor: Multiplier for saturation (e.g., 0.5 for 50% less saturated, 1.5 for 50% more saturated).
    """
    r, g, b = rgb
    h, l, s = _rgb_to_hls(r, g, b)

    # Adjust Hue (degrees to 0-1 range, then add offset)
    h = (h + (h_offset_deg / 360.0)) % 1.0
    if h < 0: h += 1.0

    # Adjust Lightness
    l = max(0.0, min(1.0, l * l_factor))

    # Adjust Saturation
    s = max(0.0, min(1.0, s * s_factor))

    return _hls_to_rgb(h, l, s)

COLOR_VARIATION_PROPOSALS: List[Dict[str, any]] = [
    # Pure Lightness Increases
    {"name": "Lighter (10%)", "l_factor": 1.1, "s_factor": 1.0},
    {"name": "Lighter (20%)", "l_factor": 1.2, "s_factor": 1.0},
    {"name": "Lighter (30%)", "l_factor": 1.3, "s_factor": 1.0},
    {"name": "Lighter (40%)", "l_factor": 1.4, "s_factor": 1.0},
    {"name": "Lighter (50%)", "l_factor": 1.5, "s_factor": 1.0},

    # Pure Desaturation
    {"name": "Desaturated (15%)", "l_factor": 1.0, "s_factor": 0.85},
    {"name": "Desaturated (30%)", "l_factor": 1.0, "s_factor": 0.70},
    {"name": "Desaturated (45%)", "l_factor": 1.0, "s_factor": 0.55},
    {"name": "Desaturated (60%)", "l_factor": 1.0, "s_factor": 0.40},
    {"name": "Desaturated (75%)", "l_factor": 1.0, "s_factor": 0.25},

    # Combined Lightness Increase & Desaturation
    {"name": "Lighter (10%) & Desat. (15%)", "l_factor": 1.1, "s_factor": 0.85},
    {"name": "Lighter (20%) & Desat. (30%)", "l_factor": 1.2, "s_factor": 0.70},
    {"name": "Lighter (30%) & Desat. (45%)", "l_factor": 1.3, "s_factor": 0.55},
    {"name": "Lighter (40%) & Desat. (60%)", "l_factor": 1.4, "s_factor": 0.40},
    
    {"name": "Lighter (15%) & Desat. (10%)", "l_factor": 1.15, "s_factor": 0.90},
    {"name": "Lighter (25%) & Desat. (20%)", "l_factor": 1.25, "s_factor": 0.80},
    {"name": "Lighter (35%) & Desat. (30%)", "l_factor": 1.35, "s_factor": 0.70},

    # Stronger Lightness/Desaturation
    {"name": "Lighter (25%) & Desat. (50%)", "l_factor": 1.25, "s_factor": 0.50},
    {"name": "Lighter (50%) & Desat. (25%)", "l_factor": 1.5, "s_factor": 0.75},
]

def generate_color_variations(hex_color: str, request_id: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Generates a list of 20 color variations, focusing on less bright and more desaturated options,
    based on an input hex color.
    """
    original_rgb = hex_to_rgb(hex_color, request_id=request_id)
    if not original_rgb:
        log(f"Invalid hex color for variations: {hex_color}", level="ERROR", request_id=request_id)
        return []

    variations = []
    
    # Add original color as the first option
    variations.append({"name": "Original", "hex": rgb_to_hex(*original_rgb)})

    # Generate variations from the proposals, ensuring we get up to 19 more to make 20 total
    # (or fewer if proposals list is shorter)
    for proposal in COLOR_VARIATION_PROPOSALS[:19]: # Ensure we don't exceed 20 total with Original
        name = proposal["name"]
        h_offset_deg = proposal.get("h_offset_deg", 0)
        l_factor = proposal.get("l_factor", 1.0)
        s_factor = proposal.get("s_factor", 1.0)
        
        try:
            adjusted_rgb = adjust_hls(original_rgb, h_offset_deg=h_offset_deg, l_factor=l_factor, s_factor=s_factor)
            variations.append({"name": name, "hex": rgb_to_hex(*adjusted_rgb)})
        except Exception as e:
            log(f"Error generating variation '{name}' for {hex_color}: {e}", level="WARNING", request_id=request_id)
            # Optionally, add a placeholder or skip this variation
            # variations.append({"name": f"{name} (Error)", "hex": "#000000"})
            
    return variations 