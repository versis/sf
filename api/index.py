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

from fastapi import FastAPI, Request as FastAPIRequest, HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, HttpUrl

# Import logger early to ensure it's configured before use
from api.utils.logger import log, error, info, warning, debug, critical

# Only log startup messages using the logger
info("==== STARTUP: Direct from FastAPI entry point ====")

# Define CARD_ID_SUFFIX
CARD_ID_SUFFIX = "FE F"

# Supabase and Vercel Blob imports
from supabase import create_client, Client as SupabaseClient
from vercel_blob import put as vercel_blob_put, BlobError as VercelBlobError

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

# Supabase Client Initialization
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") # Ensure this is your SERVICE ROLE KEY

supabase_client: SupabaseClient | None = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        info("Successfully initialized Supabase client.")
    except Exception as e:
        error(f"Failed to initialize Supabase client: {e}")
        supabase_client = None # Ensure it's None if initialization fails
else:
    warning("Supabase URL or Service Key not found in environment variables. Supabase client not initialized.")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sf.tinker.institute", "https://sf-livid.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["POST", "PUT"],
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

# --- Pydantic Models for New Endpoints ---
class InitiateCardRequest(BaseModel):
    hex_color: str

class FinalizeCardRequest(BaseModel):
    db_id: int
    cropped_image_data_url: HttpUrl # Using HttpUrl for basic validation of data URL format
    hex_color: str # Required for AI and image generation, even if in DB
    # Optional: if AI details are generated on frontend and passed here
    # ai_generated_details: Dict[str, Any] | None = None

# --- New Endpoints for Two-Step Card Generation ---

@app.post("/api/initiate-card-generation")
@limiter.limit("10/minute") # Adjust rate limit as needed
async def initiate_card_generation_route(data: InitiateCardRequest, request: FastAPIRequest):
    request_id = str(uuid.uuid4())[:8]
    log("Initiate card generation request received", request_id=request_id)

    if not supabase_client:
        error("Supabase client not available for initiate_card_generation_route", request_id=request_id)
        raise HTTPException(status_code=503, detail="Database service not available.")

    if not hex_to_rgb(data.hex_color): # Validate hex color
        log(f"Invalid hexColor format provided: {data.hex_color}", level="ERROR", request_id=request_id)
        raise HTTPException(status_code=400, detail=f"Invalid hexColor format: {data.hex_color}")

    try:
        # 1. Create initial record to get DB ID
        insert_response = await supabase_client.table("card_generations").insert({
            "hex_color": data.hex_color,
            "status": "pending_details"
        }).execute()

        if not insert_response.data:
            error("Failed to insert initial card record into Supabase or no data returned.", request_id=request_id)
            raise HTTPException(status_code=500, detail="Could not initiate card generation record.")

        db_id = insert_response.data[0]['id']
        log(f"Initial record created with DB ID: {db_id}", request_id=request_id)

        # 2. Create extended_id
        extended_id_str = f"{db_id} {CARD_ID_SUFFIX}"

        # 3. Update the record with the extended_id
        update_response = await supabase_client.table("card_generations").update({
            "extended_id": extended_id_str
        }).eq("id", db_id).execute()

        if not update_response.data:
            # This is a critical issue, as the extended_id might not be set.
            # Consider a cleanup or retry mechanism if this happens.
            error(f"Failed to update record with extended_id for DB ID: {db_id}", request_id=request_id)
            # Potentially rollback or mark the initial insert as failed
            # For now, raise an error.
            raise HTTPException(status_code=500, detail="Failed to set extended card ID.")

        log(f"Record DB ID {db_id} updated with extended_id: {extended_id_str}", request_id=request_id)
        
        return {"db_id": db_id, "extended_id": extended_id_str}

    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        error(f"Error in initiate_card_generation_route: {str(e)}", request_id=request_id)
        error(f"Traceback: {traceback.format_exc()}", request_id=request_id)
        raise HTTPException(status_code=500, detail="An error occurred while initiating card generation.")


@app.post("/api/finalize-card-generation")
@limiter.limit("5/minute") # Adjust rate limit
async def finalize_card_generation_route(data: FinalizeCardRequest = Body(...), request: FastAPIRequest = FastAPIRequest):
    request_id = str(uuid.uuid4())[:8] # New request_id for this step
    log(f"Finalize card generation request for DB ID: {data.db_id}", request_id=request_id)
    request_start_time = time.time()

    if not supabase_client:
        error("Supabase client not available for finalize_card_generation_route", request_id=request_id)
        raise HTTPException(status_code=503, detail="Database service not available.")

    try:
        # 1. Fetch the existing record to get extended_id and verify status
        record_response = await supabase_client.table("card_generations").select("id, extended_id, hex_color, status").eq("id", data.db_id).maybe_single().execute()

        if not record_response.data:
            log(f"Card generation record not found for DB ID: {data.db_id}", level="ERROR", request_id=request_id)
            raise HTTPException(status_code=404, detail=f"Record with ID {data.db_id} not found.")
        
        current_record = record_response.data
        if current_record['status'] != 'pending_details':
            log(f"Record DB ID {data.db_id} is not in 'pending_details' status. Current status: {current_record['status']}", level="WARNING", request_id=request_id)
            raise HTTPException(status_code=409, detail=f"Card generation for ID {data.db_id} is not awaiting finalization or already processed.")

        extended_id = current_record['extended_id']
        hex_color_from_db = current_record['hex_color'] # Use this for consistency if needed

        if not extended_id:
             log(f"Extended_id not found for DB ID: {data.db_id}. This should not happen.", level="ERROR", request_id=request_id)
             raise HTTPException(status_code=500, detail="Critical error: Extended ID missing for the record.")


        # 2. AI Details Generation (reusing existing logic structure)
        final_card_details_for_ai: Dict[str, Any] = {}
        ai_details_to_store: Dict[str, Any] = {} # This will be stored in metadata

        enable_ai_env = os.environ.get("ENABLE_AI_CARD_DETAILS", "true").lower()
        use_ai = enable_ai_env != "false"

        if use_ai:
            log(f"Proceeding with AI generation for DB ID: {data.db_id}", request_id=request_id)
            try:
                ai_generated_details = await generate_ai_card_details(
                    data.hex_color, # Or hex_color_from_db if you prefer
                    str(data.cropped_image_data_url), # Pass as string
                    request_id # Pass the new request_id for this finalize step
                )
                final_card_details_for_ai = ai_generated_details
                ai_details_to_store = ai_generated_details.copy() # Store a copy
            except asyncio.TimeoutError as timeout_err:
                log(f"Timeout calling Azure OpenAI for DB ID {data.db_id}: {str(timeout_err)}", level="ERROR", request_id=request_id)
                raise HTTPException(status_code=504, detail="AI service timed out.")
            except ValueError as ve:
                log(f"AI details generation ValueError for DB ID {data.db_id}: {str(ve)}", level="ERROR", request_id=request_id)
                raise HTTPException(status_code=400, detail=f"AI Error: {str(ve)}")
            except Exception as e:
                log(f"AI details generation failed for DB ID {data.db_id}: {str(e)}", level="ERROR", request_id=request_id)
                log(f"Traceback: {traceback.format_exc()}", level="ERROR", request_id=request_id)
                raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")
        else:
            log(f"AI is disabled. Using fallback details for DB ID: {data.db_id}", request_id=request_id)
            final_card_details_for_ai = {
                "colorName": "DUMMY COLOR NAME",
                "phoneticName": "['dʌmi 'kʌlər neɪm]",
                "article": "[AI disabled]",
                "description": f"A color with hex value {data.hex_color}. AI-generated details are disabled."
            }
            ai_details_to_store = final_card_details_for_ai.copy()

        # Ensure cardId for image generation uses the correct extended_id
        final_card_details_for_ai["cardId"] = extended_id


        # 3. Generate final image (with ID rendered on it) using your existing utility
        # Assuming generate_card_image_bytes renders the cardId (our extended_id) onto the image
        log(f"Generating final card image for DB ID: {data.db_id}, extended_id: {extended_id}", request_id=request_id)
        
        # Defaulting orientation, make this a parameter in FinalizeCardRequest if frontend needs to specify
        image_orientation = "horizontal" 
        
        final_image_bytes = await generate_card_image_bytes(
            cropped_image_data_url=str(data.cropped_image_data_url),
            card_details=final_card_details_for_ai, # This contains the extended_id as cardId
            hex_color_input=data.hex_color, # Or hex_color_from_db
            orientation=image_orientation,
            request_id=request_id
        )

        # 4. Upload the final image to Vercel Blob
        # Generate a unique filename for Vercel Blob
        random_suffix = str(uuid.uuid4())[:8]
        # Sanitize extended_id for filename (replace spaces, etc.)
        safe_extended_id_part = extended_id.replace(" ", "_").replace("/", "_")
        image_filename_for_blob = f"cards/{safe_extended_id_part}-{random_suffix}.jpg" # Assuming JPG, adjust if needed

        log(f"Uploading final image to Vercel Blob as: {image_filename_for_blob}", request_id=request_id)
        try:
            blob_response = await asyncio.to_thread(
                vercel_blob_put,
                pathname=image_filename_for_blob,
                body=final_image_bytes,
                options={'access': 'public', 'add_random_suffix': 'false'} # Already added our own random part
            )
            uploaded_image_url = blob_response['url']
            log(f"Image uploaded successfully to Vercel Blob: {uploaded_image_url}", request_id=request_id)
        except VercelBlobError as e:
            log(f"Vercel Blob upload failed for DB ID {data.db_id}: {str(e)}", level="ERROR", request_id=request_id)
            raise HTTPException(status_code=500, detail=f"Image storage failed: {str(e)}")
        except Exception as e: # Catch any other exception during blob upload
            log(f"Unexpected error during Vercel Blob upload for DB ID {data.db_id}: {str(e)}", level="ERROR", request_id=request_id)
            log(f"Traceback: {traceback.format_exc()}", level="ERROR", request_id=request_id)
            raise HTTPException(status_code=500, detail="Image storage encountered an unexpected error.")


        # 5. Update Supabase record with image URL, metadata, and set status to 'completed'
        update_payload = {
            "image_url": uploaded_image_url,
            "metadata": ai_details_to_store, # Store the AI generated details (or fallback)
            "status": "completed"
        }
        update_response = await supabase_client.table("card_generations").update(update_payload).eq("id", data.db_id).execute()

        if not update_response.data:
            log(f"Failed to finalize Supabase record for DB ID: {data.db_id}", level="CRITICAL", request_id=request_id)
            # At this point, image is in Blob but DB record is not updated. Requires manual check or more robust retry/cleanup.
            raise HTTPException(status_code=500, detail="Failed to update card generation record after image upload.")

        total_duration = time.time() - request_start_time
        log(f"Card generation finalized successfully for DB ID {data.db_id} in {total_duration:.2f}s. Image URL: {uploaded_image_url}", request_id=request_id)
        
        return {
            "message": "Card finalized successfully",
            "db_id": data.db_id,
            "extended_id": extended_id,
            "image_url": uploaded_image_url,
            "ai_details_used": ai_details_to_store
        }

    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        error(f"Error in finalize_card_generation_route for DB ID {data.db_id}: {str(e)}", request_id=request_id)
        error(f"Traceback: {traceback.format_exc()}", request_id=request_id)
        raise HTTPException(status_code=500, detail=f"An error occurred during card finalization: {str(e)}")


# --- Unified API Endpoint (Existing - TO BE DEPRECATED/REMOVED LATER) ---
# Consider adding a deprecation warning log here if calls are still made to it.
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
