from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict
import re
from pydantic import BaseModel

from api.utils.color_utils import generate_color_variations, hex_to_rgb
from api.utils.logger import log

router = APIRouter()

class ColorVariation(BaseModel):
    name: str
    hex: str

class ColorVariationsResponse(BaseModel):
    variations: List[ColorVariation]

@router.get(
    "/color-variations",
    response_model=ColorVariationsResponse,
    summary="Generate Color Variations",
    description="Generates a list of 20 color variations (mostly darker and desaturated) based on an input hex color."
)
async def get_color_variations(
    hex_color: str = Query(..., description="Input hex color string (e.g., '#RRGGBB' or 'RRGGBB').")
):
    request_id = "color-variations-request"
    log(f"Received request for color variations for hex: {hex_color}", request_id=request_id)

    cleaned_hex = hex_color.lstrip('#')
    if not re.match(r"^[0-9a-fA-F]{6}$", cleaned_hex) and not re.match(r"^[0-9a-fA-F]{3}$", cleaned_hex):
        log(f"Invalid hex format provided: {hex_color}", request_id=request_id, level="ERROR")
        raise HTTPException(status_code=400, detail=f"Invalid hex color format: {hex_color}. Please use RRGGBB or #RRGGBB.")

    if hex_to_rgb(cleaned_hex, request_id) is None:
        log(f"hex_to_rgb failed for cleaned hex: {cleaned_hex}", request_id=request_id, level="ERROR")
        raise HTTPException(status_code=400, detail=f"Invalid hex color value: {hex_color}.")

    try:
        variations_data = generate_color_variations(cleaned_hex, request_id=request_id)
        log(f"Successfully generated {len(variations_data)} color variations for {cleaned_hex}", request_id=request_id)
        return ColorVariationsResponse(variations=[ColorVariation(**var) for var in variations_data])
    except Exception as e:
        log(f"Error generating color variations for {cleaned_hex}: {str(e)}", request_id=request_id, level="CRITICAL")
        raise HTTPException(status_code=500, detail="Internal server error while generating color variations.")

# Ensure any trailing comments or unused imports are cleaned up if necessary. 