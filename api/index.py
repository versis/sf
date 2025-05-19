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

# Import configuration, including CARD_ID_SUFFIX
from api.core.config import (
    CARD_ID_SUFFIX, 
    SUPABASE_URL, 
    SUPABASE_SERVICE_KEY, 
    AZURE_OPENAI_API_VERSION, 
    AZURE_OPENAI_DEPLOYMENT, 
    ENABLE_AI_CARD_DETAILS,
    ALLOWED_ORIGINS,
    BLOB_READ_WRITE_TOKEN,
    DEFAULT_STATUS_COMPLETED
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
from api.models.request import GenerateCardsRequest
from api.models.response import CardImageResponseItem, GenerateCardsResponse
from api.services.supabase_service import create_card_generation_record, update_card_generation_status
from api.models.card_generation_models import CardGenerationCreateRequest, CardGenerationUpdateRequest

# Log app loading
info("==== Loading FastAPI app ====")

# Rate limiting with slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn

# load_dotenv(".env.local") # Removed, as it's handled in api.core.config.py

# Log environment variables
info(f"AZURE_OPENAI_API_VERSION: {AZURE_OPENAI_API_VERSION if AZURE_OPENAI_API_VERSION else '(not set)'}")
info(f"AZURE_OPENAI_DEPLOYMENT: {AZURE_OPENAI_DEPLOYMENT if AZURE_OPENAI_DEPLOYMENT else '(not set)'}")
info(f"ENABLE_AI_CARD_DETAILS: {ENABLE_AI_CARD_DETAILS}")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS, # Use from config
    allow_credentials=True,
    allow_methods=["POST"], # Keep this tight for now, will add PUT/GET later if other endpoints need it
    allow_headers=["Content-Type"], # Will add X-Internal-API-Key later
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

# --- Unified API Endpoint ---
@app.post("/api/generate-cards", response_model=GenerateCardsResponse)
@limiter.limit("5/minute")
async def generate_cards_route(data: GenerateCardsRequest, request: FastAPIRequest):
    request_id = str(uuid.uuid4())[:8]
    log(f"Unified /api/generate-cards request received", request_id=request_id)
    request_start_time = time.time()

    # --- Step 1: Create initial record in Supabase and get ID ---
    db_id: int | None = None
    extended_id_from_db: str | None = None
    # final_card_details will be populated after AI/fallback
    final_card_details: Dict[str, Any] = {}

    if supabase_client:
        try:
            log(f"Initiating card generation record for hex: {data.hexColor}", request_id=request_id)
            card_create_payload = CardGenerationCreateRequest(hex_color=data.hexColor)
            
            generation_record = await create_card_generation_record(
                db=supabase_client, 
                payload=card_create_payload
                # CARD_ID_SUFFIX is now handled within create_card_generation_record via config
            )
            db_id = generation_record.id
            extended_id_from_db = generation_record.extended_id
            log(f"Successfully created card generation record. DB ID: {db_id}, Extended ID: {extended_id_from_db}", request_id=request_id)

        except Exception as e_supabase:
            log(f"Error creating card generation record in Supabase: {str(e_supabase)}", level="ERROR", request_id=request_id)
            error(f"Supabase client available: {supabase_client is not None}")
            # Return an error response if Supabase operation fails
            return JSONResponse(
                status_code=500,
                content=GenerateCardsResponse(
                    request_id=request_id,
                    ai_details_used={},
                    generated_cards=[],
                    error=f"Failed to initiate card generation in database: {str(e_supabase)}"
                ).model_dump()
            )
    else:
        log("Supabase client not initialized. Cannot create card generation record.", level="ERROR", request_id=request_id)
        # Fallback or error if Supabase is not available (critical for ID generation)
        # For now, let's return an error as the ID is crucial
        return JSONResponse(
            status_code=500,
            content=GenerateCardsResponse(
                request_id=request_id,
                ai_details_used={},
                generated_cards=[],
                error="Database client not available. Cannot generate card ID."
            ).model_dump()
        )

    # Ensure extended_id_from_db is not None before proceeding
    if not extended_id_from_db:
        log("Failed to obtain extended_id from database. Aborting.", level="CRITICAL", request_id=request_id)
        return JSONResponse(
            status_code=500,
            content=GenerateCardsResponse(
                request_id=request_id,
                ai_details_used={},
                generated_cards=[],
                error="Failed to retrieve a valid card ID from the database."
            ).model_dump()
        )
    # --- End Step 1 ---

    # Validate that the cropped image is provided AFTER initial DB record creation
    # This allows us to potentially store a "failed" status if pre-checks fail
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

    # Defaults to True (use AI) if variable is not set or not explicitly "false"
    use_ai = ENABLE_AI_CARD_DETAILS # Use directly from config

    # Use the extended_id obtained from Supabase
    active_extended_id = extended_id_from_db
    if not active_extended_id: # Should not happen due to earlier check
        # This case is already handled, but as a safeguard:
        log("CRITICAL: extended_id_from_db is None after initial check passed. Aborting.", level="ERROR", request_id=request_id)
        return JSONResponse(status_code=500, content={"error": "Internal ID generation consistency error."})

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
                # final_card_details["cardId"] = active_extended_id # Old key
                final_card_details["extendedId"] = active_extended_id # New key
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
            error(f"Traceback: {traceback.format_exc()}")
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
        log(f"ENABLE_AI_CARD_DETAILS is '{ENABLE_AI_CARD_DETAILS}'. Using fallback text details.", request_id=request_id)
        # Use fixed "DUMMY COLOR NAME" when AI is disabled
        final_card_details = {
            "colorName": "DUMMY COLOR NAME",
            "phoneticName": "['dʌmi 'kʌlər neɪm]", # Phonetic for "dummy color name"
            "article": "[AI disabled]",
            "description": f"A color with hex value {data.hexColor}. AI-generated details are disabled.",
            # "cardId": active_extended_id # Old key
            "extendedId": active_extended_id # New key
        }

    # debug(f"Final card details for rendering (using DB generated ID): {json.dumps(final_card_details, indent=2)}", request_id=request_id)
    # Update log message to reflect new key name if desired, or keep general
    log(f"Final card details prepared (ID: {active_extended_id}): {json.dumps(final_card_details, indent=2)}", request_id=request_id)

    generated_cards_response_items: List[CardImageResponseItem] = []
    orientations_to_generate = ["horizontal", "vertical"]

    # Store Blob URLs here
    blob_urls: Dict[str, str] = {}

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
            # image_base64 = base64.b64encode(image_bytes).decode('utf-8') # No longer sending base64 to client

            # --- Vercel Blob Upload ---
            if not BLOB_READ_WRITE_TOKEN:
                log("BLOB_READ_WRITE_TOKEN not configured. Cannot upload to Vercel Blob.", level="ERROR", request_id=request_id)
                # Depending on requirements, either fail or skip upload
                # For now, we'll throw an error as upload is a key part of this step
                raise ConnectionError("Blob storage token not configured. Cannot save card image.")

            # Construct a unique filename for Vercel Blob
            # Making filename URL-safe and unique
            safe_extended_id = active_extended_id.replace(' ', '_').replace('/', '-') # Basic sanitization
            unique_suffix = uuid.uuid4().hex[:16] # New: 16 characters
            blob_filename = f"cards/{safe_extended_id}_{orientation}_{unique_suffix}.png"
            
            log(f"Uploading {orientation} card to Vercel Blob as {blob_filename}", request_id=request_id)
            try:
                blob_upload_response = vercel_blob_put(
                    blob_filename, 
                    image_bytes, 
                    options={'token': BLOB_READ_WRITE_TOKEN, 'access': 'public'}
                )
                blob_url = blob_upload_response['url']
                blob_urls[orientation] = blob_url # Store for potential later use (e.g., DB update)
                log(f"Successfully uploaded {orientation} card. URL: {blob_url}", request_id=request_id)
            except Exception as e_blob:
                log(f"Error uploading {orientation} image to Vercel Blob: {str(e_blob)}", level="ERROR", request_id=request_id)
                error(f"Vercel Blob upload traceback: {traceback.format_exc()}")
                raise ConnectionError(f"Failed to upload {orientation} image to blob storage: {str(e_blob)}")
            # --- End Vercel Blob Upload ---

            generated_cards_response_items.append(
                CardImageResponseItem(
                    orientation=orientation,
                    # image_base64=image_base64, # Old
                    imageUrl=blob_url, # New
                    filename=blob_filename, # Using the blob filename
                    extendedId=final_card_details['extendedId'] 
                )
            )
            log(f"Successfully generated and processed {orientation} card image.", request_id=request_id)
        
        total_duration = time.time() - request_start_time
        log(f"All cards generated successfully in {total_duration:.2f} seconds.", request_id=request_id)
        
        # --- Step 5: Update Supabase record with Blob URLs and metadata ---
        if supabase_client and db_id:
            try:
                log(f"Attempting to finalize Supabase record ID: {db_id}", request_id=request_id)
                
                # Prepare the update payload
                # For now, primary image_url will be horizontal. Both can be in metadata.
                # primary_image_url = blob_urls.get("horizontal") # Old logic
                # if not primary_image_url:
                #     primary_image_url = blob_urls.get("vertical") # Old logic
                
                # Add all blob_urls to metadata for completeness and set specific columns
                metadata_to_store = final_card_details.copy() 
                metadata_to_store["image_urls"] = blob_urls 
                metadata_to_store["hex_color"] = data.hexColor # Added hexColor

                update_payload_dict = {
                    "status": DEFAULT_STATUS_COMPLETED,
                    "metadata": metadata_to_store,
                }
                # if primary_image_url: # Old logic
                #     update_payload_dict["image_url"] = primary_image_url # Old logic

                # Use the correct column names from your table schema
                if "horizontal" in blob_urls:
                    update_payload_dict["horizontal_image_url"] = blob_urls["horizontal"]
                if "vertical" in blob_urls:
                    update_payload_dict["vertical_image_url"] = blob_urls["vertical"]
                
                # CardGenerationUpdateRequest might need to be updated if it strictly validates keys
                # For now, assuming supabase_service.update_card_generation_status handles the dict flexibly.
                # If CardGenerationUpdateRequest is used for validation before this point, ensure it has these fields.
                # Since we pass `details=update_payload_dict` directly to the service,
                # and the service uses `update_data.update(details)`, it should be flexible.
                
                # update_request = CardGenerationUpdateRequest(**update_payload_dict) # This might fail if model is strict
                # We will let the supabase_service handle the dictionary directly.

                updated_record = await update_card_generation_status(
                    db=supabase_client,
                    record_id=db_id,
                    status=DEFAULT_STATUS_COMPLETED, # Status is also part of details dict, but explicit here
                    details=update_payload_dict # Pass the full dict, status will be set from here
                )
                log(f"Successfully finalized Supabase record ID: {db_id}. Status: {updated_record.status}", request_id=request_id)
            except Exception as e_supabase_update:
                log(f"Error finalizing Supabase record ID {db_id}: {str(e_supabase_update)}", level="ERROR", request_id=request_id)
                error(f"Supabase update traceback: {traceback.format_exc()}")
                # Decide if this error should fail the request or just be logged
                # For now, we log it but still return the generated cards to the user
        else:
            log(f"Supabase client not available or db_id missing. Cannot finalize record.", level="WARNING", request_id=request_id)
        # --- End Step 5 ---

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
        error(f"Traceback: {traceback.format_exc()}")
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
        timeout_keep_alive=120,  # Increased from 75 seconds
        log_level="debug",
        log_config=log_config,
        use_colors=True,
        proxy_headers=True
    )
