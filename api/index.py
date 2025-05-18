import os
import json
import time
import uuid
import base64
import asyncio
import traceback
import logging
import sys
from typing import Dict, Any, List

from fastapi import FastAPI, Request as FastAPIRequest
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import logger early to ensure it's configured before use
from api.utils.logger import log, error, info, warning, debug, critical

# Only log startup messages using the logger
info("==== STARTUP: Direct from FastAPI entry point ====")

from api.utils.ai_utils import generate_ai_card_details
from api.utils.color_utils import hex_to_rgb
from api.utils.card_utils import generate_card_image_bytes
from api.models.request import GenerateCardsRequest
from api.models.response import CardImageResponseItem, GenerateCardsResponse

# Log app loading
info("==== Loading FastAPI app ====")

# Rate limiting with slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn

load_dotenv(".env.local")

# Log environment variables
info(f"AZURE_OPENAI_API_VERSION: {os.environ.get('AZURE_OPENAI_API_VERSION', '(not set)')}")
info(f"AZURE_OPENAI_DEPLOYMENT: {os.environ.get('AZURE_OPENAI_DEPLOYMENT', '(not set)')}")
info(f"ENABLE_AI_CARD_DETAILS: {os.environ.get('ENABLE_AI_CARD_DETAILS', '(not set)')}")

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

@app.on_event("startup")
async def startup_event():
    # Use logger for startup
    info("===== FastAPI STARTUP EVENT =====")
    
    # Log environment variable configuration (excluding sensitive values)
    debug(f"AZURE_OPENAI_API_VERSION: {os.environ.get('AZURE_OPENAI_API_VERSION', '(not set)')}")
    debug(f"AZURE_OPENAI_DEPLOYMENT: {os.environ.get('AZURE_OPENAI_DEPLOYMENT', '(not set)')}")
    debug(f"ENABLE_AI_CARD_DETAILS: {os.environ.get('ENABLE_AI_CARD_DETAILS', '(not set)')}")
    info("Application startup complete")

@app.exception_handler(Exception)
async def global_exception_handler(request: FastAPIRequest, exc: Exception):
    # Log exceptions properly
    error_msg = f"Unhandled exception: {str(exc)}"
    error(error_msg)
    error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred", "detail": str(exc)}
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

    # Validate that the cropped image is provided
    if not data.croppedImageDataUrl:
        log(f"No cropped image provided in request", level="ERROR", request_id=request_id)
        return JSONResponse(
            status_code=400,
            content=GenerateCardsResponse(
                request_id=request_id, 
                ai_details_used={},
                generated_cards=[],
                error="A cropped image is required to generate a card"
            ).model_dump()
        )

    if not hex_to_rgb(data.hexColor):
        log(f"Invalid hexColor format provided: {data.hexColor}", level="ERROR", request_id=request_id)
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
        log("Proceeding with AI generation based on hex color and cropped image.", request_id=request_id)
        try:
            # Log image size to help diagnose issues
            if data.croppedImageDataUrl:
                img_data_size = len(data.croppedImageDataUrl) / 1024
                debug(f"Cropped image data URL size: {img_data_size:.2f}KB", request_id=request_id)
                
                if img_data_size > 10000:  # If image is larger than ~10MB
                    log(f"Warning: Image size is very large ({img_data_size:.2f}KB)", level="WARNING", request_id=request_id)
            
            try:
                log(f"Starting AI card details generation", request_id=request_id)
                ai_generated_details = await generate_ai_card_details(
                    data.hexColor, 
                    data.croppedImageDataUrl, 
                    request_id
                )
                log(f"Successfully generated AI card details", request_id=request_id)
                final_card_details = ai_generated_details
                final_card_details["cardId"] = data.cardId or default_card_id
            except asyncio.TimeoutError as timeout_err:
                log(f"Timeout while calling Azure OpenAI API: {str(timeout_err)}", level="ERROR", request_id=request_id)
                return JSONResponse(
                    status_code=504,  # Gateway Timeout
                    content=GenerateCardsResponse(
                        request_id=request_id, 
                        ai_details_used={},
                        generated_cards=[],
                        error="AI service timed out. Please try again with a smaller image."
                    ).model_dump()
                )
            except ValueError as ve:
                log(f"AI details generation failed with ValueError: {str(ve)}", level="ERROR", request_id=request_id)
                return JSONResponse(
                    status_code=400,
                    content=GenerateCardsResponse(
                        request_id=request_id, 
                        ai_details_used={},
                        generated_cards=[],
                        error=f"Error: {str(ve)}"
                    ).model_dump()
                )
        except Exception as e:
            log(f"AI details generation failed: {str(e)}", level="ERROR", request_id=request_id)
            import traceback
            log(f"Traceback: {traceback.format_exc()}", level="ERROR", request_id=request_id)
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

    debug(f"Final card details for rendering: {json.dumps(final_card_details, indent=2)}", request_id=request_id)

    generated_cards_response_items: List[CardImageResponseItem] = []
    orientations_to_generate = ["horizontal", "vertical"]

    try:
        for orientation in orientations_to_generate:
            debug(f"Generating {orientation} card image...", request_id=request_id)
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
                    filename=f"card_{final_card_details['colorName'].replace(' ', '_')}_{orientation}_{request_id}.jpg",
                    cardId=final_card_details.get('cardId', "0000000 XX X")
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
    info("===== STARTING UVICORN SERVER =====")
    info(f"Environment: {os.environ.get('NODE_ENV', 'development')}")
    info(f"AZURE_OPENAI_API_VERSION: {os.environ.get('AZURE_OPENAI_API_VERSION', '(not set)')}")
    info(f"AZURE_OPENAI_DEPLOYMENT: {os.environ.get('AZURE_OPENAI_DEPLOYMENT', '(not set)')}")
    
    info("Starting Uvicorn server for local development...")
    
    # Configure Uvicorn logging
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(asctime)s %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.access": {"handlers": ["default"], "level": "INFO"},
        },
    }
    
    uvicorn.run(
        "index:app", 
        app_dir="api", 
        host="0.0.0.0", 
        port=8000, 
        reload=True, 
        reload_dirs=["api"], 
        timeout_keep_alive=120,  # Increased from 75 seconds
        log_level="debug",
        log_config=log_config,
        use_colors=True,
        proxy_headers=True
    )
