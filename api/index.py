import os
import json
import time
import uuid
import base64
import re
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Request as FastAPIRequest
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from api.utils.logger import log
from api.utils.ai_utils import generate_ai_card_details
from api.utils.card_utils import generate_card_image_bytes, hex_to_rgb

# Rate limiting with slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn

load_dotenv(".env.local")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sf.tinker.institute", "https://sf-livid.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

# --- Color Conversion Utilities (from shadefreude) ---
def hex_to_rgb(hex_color: str) -> tuple[int, int, int] | None:
    """Converts a HEX color string to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if not re.match(r"^[0-9a-fA-F]{6}$", hex_color) and not re.match(r"^[0-9a-fA-F]{3}$", hex_color):
        print(f"Invalid HEX format: {hex_color}")
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

def rgb_to_cmyk(r: int, g: int, b: int) -> tuple[int, int, int, int]:
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
# --- End Color Conversion Utilities ---

# --- Pydantic Models ---
class GenerateCardsRequest(BaseModel):
    croppedImageDataUrl: str
    hexColor: str
    colorName: str

class CardImageResponseItem(BaseModel):
    orientation: str
    image_base64: str
    filename: str

class GenerateCardsResponse(BaseModel):
    request_id: str
    ai_details_used: Dict[str, Any]
    generated_cards: List[CardImageResponseItem]
    error: Optional[str] = None

# --- Unified API Endpoint ---
@app.post("/api/generate-cards", response_model=GenerateCardsResponse)
@limiter.limit("5/minute")
async def generate_cards_route(data: GenerateCardsRequest, request: FastAPIRequest):
    request_id = str(uuid.uuid4())[:8]
    log(f"Unified /api/generate-cards request received", request_id=request_id)
    request_start_time = time.time()

    # Validate hex color format
    rgb_color = hex_to_rgb(data.hexColor)
    if not rgb_color:
        log(f"Invalid hexColor format provided: {data.hexColor}", request_id=request_id)
        return JSONResponse(
            status_code=400,
            content=GenerateCardsResponse(
                request_id=request_id, 
                ai_details_used={},
                generated_cards=[],
                error=f"Invalid hexColor format: {data.hexColor}"
            ).model_dump()
        )

    # Check if AI is enabled from environment variable
    enable_ai_env = os.environ.get("ENABLE_AI_CARD_DETAILS", "true").lower()
    use_ai = enable_ai_env != "false"

    # Initialize card details with default values
    default_card_id = "0000023 FE T"
    
    if use_ai:
        log("AI is enabled. Generating card details using AI.", request_id=request_id)
        try:
            # Generate card details using AI
            ai_generated_details = await generate_ai_card_details(data.colorName, data.hexColor, request_id)
            final_card_details = ai_generated_details
            final_card_details["cardId"] = default_card_id
            log(f"AI successfully generated card details", request_id=request_id)
        except Exception as e:
            # If AI fails, use fallback but return error in the response
            log(f"AI generation failed: {str(e)}. Using fallback details.", request_id=request_id)
            final_card_details = {
                "cardName": "PLACEHOLDER COLOR", 
                "phoneticName": "['pleɪs.hoʊl.dər]",
                "article": "[placeholder]",
                "description": f"This is a placeholder for {data.colorName.strip()}. (AI generation failed)",
                "cardId": default_card_id,
                "ai_error": str(e)  # Include the error message
            }
            # We continue with card generation using fallback details
    else:
        # AI is disabled, use fallback text
        log(f"AI is disabled. Using fallback text details.", request_id=request_id)
        final_card_details = {
            "cardName": "EXAMPLE COLOR", 
            "phoneticName": "['ɛɡ.zæm.pəl]", # Phonetic for "example"
            "article": "[AI disabled]",
            "description": f"This is a placeholder color. AI-generated details are currently disabled.",
            "cardId": default_card_id
        }

    log(f"Final card details for rendering: {json.dumps(final_card_details, indent=2)}", request_id=request_id)

    # Add color metrics to the card details
    r, g, b = rgb_color
    c, m, y, k = rgb_to_cmyk(r, g, b)
    final_card_details["metrics"] = {
        "hex": data.hexColor.upper(),
        "rgb": f"{r} {g} {b}",
        "cmyk": f"{c} {m} {y} {k}"
    }

    # Generate cards for both orientations
    generated_cards_response_items: List[CardImageResponseItem] = []
    orientations_to_generate = ["horizontal", "vertical"]

    try:
        for orientation in orientations_to_generate:
            log(f"Generating {orientation} card image...", request_id=request_id)
            image_bytes = await generate_card_image_bytes(
                cropped_image_data_url=data.croppedImageDataUrl,
                card_details=final_card_details,
                hex_color_input=data.hexColor,
                orientation=orientation,
                request_id=request_id
            )
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            generated_cards_response_items.append(
                CardImageResponseItem(
                    orientation=orientation,
                    image_base64=image_base64,
                    filename=f"card_{final_card_details['cardName'].replace(' ', '_')}_{orientation}_{request_id}.png"
                )
            )
            log(f"Successfully generated {orientation} card image.", request_id=request_id)
        
        total_duration = time.time() - request_start_time
        log(f"All cards generated successfully in {total_duration:.2f} seconds.", request_id=request_id)
        
        # Clean up the ai_error field if it exists before returning
        if "ai_error" in final_card_details:
            del final_card_details["ai_error"]
        
        return GenerateCardsResponse(
            request_id=request_id,
            ai_details_used=final_card_details,
            generated_cards=generated_cards_response_items
        )

    except ValueError as ve:
        log(f"ValueError during card generation: {str(ve)}", request_id=request_id)
        return JSONResponse(
            status_code=400,
            content=GenerateCardsResponse(
                request_id=request_id, 
                ai_details_used=final_card_details, 
                generated_cards=[], 
                error=str(ve)
            ).model_dump()
        )
    except Exception as e:
        log(f"General error during card generation processing: {str(e)}", request_id=request_id)
        return JSONResponse(
            status_code=500,
            content=GenerateCardsResponse(
                request_id=request_id, 
                ai_details_used=final_card_details, 
                generated_cards=[], 
                error="Internal server error during image processing."
            ).model_dump()
        )

class CardDetailsRequest(BaseModel):
    hexColor: str
    colorName: str

@app.post("/api/generate-card-details")
@limiter.limit("10/minute")
async def generate_card_details_route(data: CardDetailsRequest, request: FastAPIRequest):
    """
    Generate AI-based card details using Azure OpenAI.
    This endpoint can be called separately before image generation.
    """
    try:
        hex_color = data.hexColor
        color_name = data.colorName
        
        if not hex_color or not color_name:
            raise HTTPException(status_code=400, detail="Missing required data: hexColor or colorName")
            
        # Validate hex color format
        rgb_color = hex_to_rgb(hex_color)
        if rgb_color is None:
            raise HTTPException(status_code=400, detail=f"Invalid HEX color format: {hex_color}")
            
        # Generate the card details
        card_details = await generate_ai_card_details(color_name, hex_color)
        
        return {
            "success": True,
            "cardDetails": card_details
        }
        
    except HTTPException as e:
        # Re-raise HTTPException
        raise e
    except Exception as e:
        print(f"Error generating card details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate card details: {str(e)}")

# To run locally (ensure uvicorn is installed: pip install uvicorn)
if __name__ == "__main__":
    # Ensure ASSETS_BASE_PATH in card_utils.py is correct for local running
    # If index.py is in /api, and assets are in /assets, card_utils.ASSETS_BASE_PATH might need to be "../assets"
    # Or, ensure the CWD is the project root when running uvicorn.
    # For uvicorn from project root: uvicorn api.index:app --reload
    log("Starting Uvicorn server for local development...")
    uvicorn.run("index:app", app_dir="api", host="0.0.0.0", port=8000, reload=True, reload_dirs=["api"], timeout_keep_alive=75)
