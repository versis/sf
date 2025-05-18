import os
import json
import time
import uuid
import base64
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Request as FastAPIRequest
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.utils.logger import log
from api.utils.ai_utils import generate_ai_card_details
from api.utils.card_utils import generate_card_image_bytes, hex_to_rgb, rgb_to_cmyk
from api.models import GenerateCardsRequest, CardImageResponseItem, GenerateCardsResponse

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

# --- Unified API Endpoint ---
@app.post("/api/generate-cards", response_model=GenerateCardsResponse)
@limiter.limit("5/minute")
async def generate_cards_route(data: GenerateCardsRequest, request: FastAPIRequest):
    request_id = str(uuid.uuid4())[:8]
    log(f"Unified /api/generate-cards request received", request_id=request_id)
    request_start_time = time.time()

    final_card_details: Dict[str, Any] = {}
    default_card_id = "0000023 FE T"

    if not hex_to_rgb(data.hexColor):
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

    # Check environment variable to decide on AI generation first
    # Defaults to True (use AI) if variable is not set or not explicitly "false"
    enable_ai_env = os.environ.get("ENABLE_AI_CARD_DETAILS", "true").lower()
    use_ai = enable_ai_env != "false"

    if use_ai:
        log("Proceeding with AI generation based solely on hex color.", request_id=request_id)
        try:
            ai_generated_details = await generate_ai_card_details(data.hexColor, request_id)
            final_card_details = ai_generated_details
            final_card_details["cardId"] = data.cardId or default_card_id
        except Exception as e:
            log(f"AI details generation failed: {str(e)}. Returning error to client.", request_id=request_id)
            # Don't generate fallback - return error since AI was enabled but failed
            return JSONResponse(
                status_code=500,
                content=GenerateCardsResponse(
                    request_id=request_id, 
                    ai_details_used={},
                    generated_cards=[],
                    error=f"AI generation failed: {str(e)}"
                ).model_dump()
            )
    else:
        log(f"ENABLE_AI_CARD_DETAILS is '{enable_ai_env}'. Using fallback text details.", request_id=request_id)
        # Use fixed "DUMMY COLOR NAME" when AI is disabled
        final_card_details = {
            "colorName": "DUMMY COLOR NAME",
            "phoneticName": "['dʌmi 'kʌlər neɪm]", # Phonetic for "dummy color name"
            "article": "[AI disabled]",
            "description": f"A color with hex value {data.hexColor}. AI-generated details are disabled.",
            "cardId": data.cardId or default_card_id
        }

    log(f"Final card details for rendering: {json.dumps(final_card_details, indent=2)}", request_id=request_id)

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
                    filename=f"card_{final_card_details['colorName'].replace(' ', '_')}_{orientation}_{request_id}.jpg"
                )
            )
            log(f"Successfully generated {orientation} card image.", request_id=request_id)
        
        total_duration = time.time() - request_start_time
        log(f"All cards generated successfully in {total_duration:.2f} seconds.", request_id=request_id)
        
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

# To run locally (ensure uvicorn is installed: pip install uvicorn)
if __name__ == "__main__":
    # Ensure ASSETS_BASE_PATH in card_utils.py is correct for local running
    # If index.py is in /api, and assets are in /assets, card_utils.ASSETS_BASE_PATH might need to be "../assets"
    # Or, ensure the CWD is the project root when running uvicorn.
    # For uvicorn from project root: uvicorn api.index:app --reload
    log("Starting Uvicorn server for local development...")
    uvicorn.run("index:app", app_dir="api", host="0.0.0.0", port=8000, reload=True, reload_dirs=["api"], timeout_keep_alive=75)
