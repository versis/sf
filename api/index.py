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
from api.utils.logger import log, error, info, warning, debug

# Import configuration, including CARD_ID_SUFFIX
from .config import (
    CARD_ID_SUFFIX, 
    SUPABASE_URL, 
    SUPABASE_SERVICE_KEY, 
    AZURE_OPENAI_API_VERSION, 
    AZURE_OPENAI_DEPLOYMENT, 
    ENABLE_AI_CARD_DETAILS,
    ALLOWED_ORIGINS,
    UVICORN_TIMEOUT_KEEP_ALIVE,
)

# Supabase Client Initialization
from supabase import create_client, Client as SupabaseClient

# Vercel Blob import
from vercel_blob import put as vercel_blob_put

supabase_client: SupabaseClient | None = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        info("Successfully initialized Supabase client.")
    except Exception as e:
        error(f"Failed to initialize Supabase client: {e}")
        supabase_client = None # Ensure it's None if initialization fails
else:
    warning("Supabase URL or Service Key not found in environment variables. Supabase client not initialized. API will likely fail DB operations.")

# Only log startup messages using the logger
info("==== STARTUP: Direct from FastAPI entry point ====")

from api.utils.ai_utils import generate_ai_card_details
from api.utils.color_utils import hex_to_rgb
from api.utils.card_utils import generate_card_image_bytes
from api.services.supabase_service import create_card_generation_record, update_card_generation_status
from api.models.card_generation_models import CardGenerationCreateRequest, CardGenerationUpdateRequest

# Log app loading
info("==== Loading FastAPI app ====")

# load_dotenv(".env.local") # Removed, as it's handled in api.core.config.py

# Log environment variables
info(f"AZURE_OPENAI_API_VERSION: {AZURE_OPENAI_API_VERSION if AZURE_OPENAI_API_VERSION else '(not set)'}")
info(f"AZURE_OPENAI_DEPLOYMENT: {AZURE_OPENAI_DEPLOYMENT if AZURE_OPENAI_DEPLOYMENT else '(not set)'}")
info(f"ENABLE_AI_CARD_DETAILS: {ENABLE_AI_CARD_DETAILS}")

app = FastAPI()

# Import the new card generation router
from api.routers import card_generation as card_generation_router # Added
from api.routers import card_retrieval as card_retrieval_router # New router for card retrieval
from api.routers import color_suggestions as color_suggestions_router # New router for color suggestions

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS, # Use from config
    allow_credentials=True,
    allow_methods=["GET", "POST"], # Added GET for card retrieval endpoints
    allow_headers=["Content-Type", "X-Internal-API-Key"], # Added X-Internal-API-Key as noted in comment
)

@app.on_event("startup")
async def startup_event():
    # Use logger for startup
    info("===== FastAPI STARTUP EVENT =====")
    
    # Log environment variable configuration (excluding sensitive values)
    debug(f"AZURE_OPENAI_API_VERSION: {AZURE_OPENAI_API_VERSION if AZURE_OPENAI_API_VERSION else '(not set)'}")
    debug(f"AZURE_OPENAI_DEPLOYMENT: {AZURE_OPENAI_DEPLOYMENT if AZURE_OPENAI_DEPLOYMENT else '(not set)'}")
    debug(f"ENABLE_AI_CARD_DETAILS: {ENABLE_AI_CARD_DETAILS}")
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

# Include the new card generation router
app.include_router(card_generation_router.router, prefix="/api", tags=["Card Generation"]) # Added, assuming /api prefix for all
app.include_router(card_retrieval_router.router, prefix="/api", tags=["Card Retrieval"]) # Include the new router
app.include_router(color_suggestions_router.router, prefix="/api", tags=["Color Suggestions"]) # Include the new color suggestions router

# --- Unified API Endpoint --- # This entire block will be removed
# @app.post("/api/generate-cards", response_model=GenerateCardsResponse)
# @limiter.limit("5/minute")
# async def generate_cards_route(data: GenerateCardsRequest, request: FastAPIRequest):
    # ... (entire content of generate_cards_route) ...
# --- End Step 5 ---

        # return GenerateCardsResponse(
        #     request_id=request_id,
        #     ai_details_used=final_card_details,
        #     generated_cards=generated_cards_response_items
        # )

    # except ValueError as ve:
    #     log(f"ValueError during card generation: {str(ve)}", request_id=request_id)
    #     return JSONResponse(
    #         status_code=400,
    #         content=GenerateCardsResponse(
    #             request_id=request_id, 
    #             ai_details_used=final_card_details, 
    #             generated_cards=[], 
    #             error=str(ve)
    #         ).model_dump()
    #     )
    # except Exception as e:
    #     log(f"General error during card generation processing: {str(e)}", request_id=request_id)
    #     error(f"Traceback: {traceback.format_exc()}")
    #     return JSONResponse(
    #         status_code=500,
    #         content=GenerateCardsResponse(
    #             request_id=request_id, 
    #             ai_details_used=final_card_details, 
    #             generated_cards=[], 
    #             error="Internal server error during image processing."
    #         ).model_dump()
    #     )

# To run locally (ensure uvicorn is installed: pip install uvicorn)
if __name__ == "__main__":
    # Ensure ASSETS_BASE_PATH in card_utils.py is correct for local running
    # If index.py is in /api, and assets are in /assets, card_utils.ASSETS_BASE_PATH might need to be "../assets"
    # Or, ensure the CWD is the project root when running uvicorn.
    # For uvicorn from project root: uvicorn api.index:app --reload
    info("===== STARTING UVICORN SERVER =====")
    # Use imported config values for logging here as well
    info(f"Environment: {os.environ.get('NODE_ENV', 'development')}") # NODE_ENV is not in our python config, so os.environ.get is fine here
    info(f"AZURE_OPENAI_API_VERSION: {AZURE_OPENAI_API_VERSION if AZURE_OPENAI_API_VERSION else '(not set)'}")
    info(f"AZURE_OPENAI_DEPLOYMENT: {AZURE_OPENAI_DEPLOYMENT if AZURE_OPENAI_DEPLOYMENT else '(not set)'}")
    info(f"ENABLE_AI_CARD_DETAILS: {ENABLE_AI_CARD_DETAILS}")
    
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
        timeout_keep_alive=UVICORN_TIMEOUT_KEEP_ALIVE,
        log_level="debug",
        log_config=log_config,
        use_colors=True,
        proxy_headers=True
    )
