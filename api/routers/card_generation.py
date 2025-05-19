# api/routers/card_generation.py
import uuid
import time
import asyncio
import traceback # Ensure traceback is imported if used directly
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Body, Depends, Request as FastAPIRequest
from slowapi import Limiter
from slowapi.util import get_remote_address # If you use get_remote_address directly in router

from api.models.card_generation_models import (
    InitiateCardRequest,
    InitiateCardResponse,
    FinalizeCardRequest,
    FinalizeCardResponse
)
from api.services import supabase_service, blob_service
from api.utils.logger import log, error, warning # Assuming your logger functions
from api.utils.color_utils import hex_to_rgb
from api.utils.ai_utils import generate_ai_card_details
from api.utils.card_utils import generate_card_image_bytes
from api.core.config import CARD_ID_SUFFIX, ENABLE_AI_CARD_DETAILS
from api.dependencies import verify_api_key

router = APIRouter()
limiter = Limiter(key_func=get_remote_address) # Assuming you want same rate limiting strategy

@router.post("/initiate-card-generation", response_model=InitiateCardResponse)
@limiter.limit("10/minute")
async def initiate_card_generation_route(data: InitiateCardRequest, request: FastAPIRequest, _api_key_verified: None = Depends(verify_api_key)):
    request_id = str(uuid.uuid4())[:8]
    log(f"Initiate card generation request received (router)", request_id=request_id)

    if not hex_to_rgb(data.hex_color):
        log(f"Invalid hexColor format provided: {data.hex_color}", level="ERROR", request_id=request_id)
        raise HTTPException(status_code=400, detail=f"Invalid hexColor format: {data.hex_color}")

    try:
        initial_record = await supabase_service.create_initial_card_record(data.hex_color)
        db_id = initial_record['id']
        log(f"Initial record created with DB ID: {db_id}", request_id=request_id)

        extended_id_str = f"{db_id} {CARD_ID_SUFFIX}"
        await supabase_service.update_card_with_extended_id(db_id, extended_id_str)
        log(f"Record DB ID {db_id} updated with extended_id: {extended_id_str}", request_id=request_id)
        
        return InitiateCardResponse(db_id=db_id, extended_id=extended_id_str)

    except ConnectionError as ce: # Catch if Supabase client not init
        error(f"Supabase connection error in initiate_card_generation_route: {str(ce)}", request_id=request_id)
        raise HTTPException(status_code=503, detail="Database service not available.")
    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        error(f"Error in initiate_card_generation_route (router): {str(e)}", request_id=request_id)
        error(f"Traceback: {traceback.format_exc()}", request_id=request_id)
        raise HTTPException(status_code=500, detail="An error occurred while initiating card generation.")

@router.post("/finalize-card-generation", response_model=FinalizeCardResponse)
@limiter.limit("5/minute")
async def finalize_card_generation_route(data: FinalizeCardRequest = Body(...), request: FastAPIRequest = FastAPIRequest, _api_key_verified: None = Depends(verify_api_key)):
    request_id = str(uuid.uuid4())[:8]
    log(f"Finalize card generation request for DB ID: {data.db_id} (router)", request_id=request_id)
    request_start_time = time.time()

    try:
        current_record = await supabase_service.get_card_for_finalization(data.db_id)

        if not current_record:
            log(f"Card generation record not found for DB ID: {data.db_id}", level="ERROR", request_id=request_id)
            raise HTTPException(status_code=404, detail=f"Record with ID {data.db_id} not found.")
        
        if current_record['status'] != 'pending_details':
            log(f"Record DB ID {data.db_id} is not in 'pending_details' status. Current status: {current_record['status']}", level="WARNING", request_id=request_id)
            raise HTTPException(status_code=409, detail=f"Card generation for ID {data.db_id} is not awaiting finalization or already processed.")

        extended_id = current_record['extended_id']
        # hex_color_from_db = current_record['hex_color'] # Available if needed

        if not extended_id:
             log(f"Extended_id not found for DB ID: {data.db_id}. This should not happen.", level="ERROR", request_id=request_id)
             raise HTTPException(status_code=500, detail="Critical error: Extended ID missing for the record.")

        # AI Details Generation
        ai_details_to_store: Dict[str, Any]
        final_card_details_for_image_render: Dict[str, Any]

        if ENABLE_AI_CARD_DETAILS:
            log(f"Proceeding with AI generation for DB ID: {data.db_id}", request_id=request_id)
            try:
                ai_generated_details = await generate_ai_card_details(
                    data.hex_color,
                    data.cropped_image_data_url,
                    request_id
                )
                ai_details_to_store = ai_generated_details.copy()
                final_card_details_for_image_render = ai_generated_details.copy()
            except asyncio.TimeoutError as timeout_err:
                log(f"Timeout calling Azure OpenAI for DB ID {data.db_id}: {str(timeout_err)}", level="ERROR", request_id=request_id)
                raise HTTPException(status_code=504, detail="AI service timed out.")
            except ValueError as ve:
                log(f"AI details generation ValueError for DB ID {data.db_id}: {str(ve)}", level="ERROR", request_id=request_id)
                raise HTTPException(status_code=400, detail=f"AI Error: {str(ve)}")
            except Exception as e:
                log(f"AI details generation failed for DB ID {data.db_id}: {str(e)}", level="ERROR", request_id=request_id)
                error(f"Traceback: {traceback.format_exc()}", request_id=request_id)
                raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")
        else:
            log(f"AI is disabled. Using fallback details for DB ID: {data.db_id}", request_id=request_id)
            fallback_details = {
                "colorName": "DUMMY COLOR NAME",
                "phoneticName": "['dʌmi 'kʌlər neɪm]",
                "article": "[AI disabled]",
                "description": f"A color with hex value {data.hex_color}. AI-generated details are disabled."
            }
            ai_details_to_store = fallback_details.copy()
            final_card_details_for_image_render = fallback_details.copy()

        final_card_details_for_image_render["cardId"] = extended_id

        # Generate final image
        log(f"Generating final card image for DB ID: {data.db_id}, extended_id: {extended_id}", request_id=request_id)
        image_orientation = "horizontal" # Defaulting, or make it a param in FinalizeCardRequest
        
        # Decode base64 data URL to bytes for image generation and blob upload
        try:
            if ';base64,' not in data.cropped_image_data_url:
                raise ValueError("Invalid Data URL format: missing ';base64,' part")
            header, base64_data = data.cropped_image_data_url.split(';base64,', 1)
            # TODO: Potentially parse 'header' for mime-type if needed by generate_card_image_bytes or blob storage for content-type
            image_bytes_for_processing = base64.b64decode(base64_data)
        except Exception as decode_err:
            log(f"Invalid base64 data URL for DB ID {data.db_id}: {str(decode_err)}", level="ERROR", request_id=request_id)
            raise HTTPException(status_code=400, detail="Invalid image data format.")

        final_image_bytes = await generate_card_image_bytes(
            # Pass decoded bytes or keep as data_url if card_utils handles data_urls directly
            # Assuming generate_card_image_bytes expects a data URL as per original code for now:
            cropped_image_data_url=data.cropped_image_data_url, 
            card_details=final_card_details_for_image_render,
            hex_color_input=data.hex_color,
            orientation=image_orientation,
            request_id=request_id
        )
        # If generate_card_image_bytes now returns bytes, and you need bytes for blob:
        # The `final_image_bytes` from `generate_card_image_bytes` are used directly for blob upload.

        # Upload image to Vercel Blob
        random_suffix = str(uuid.uuid4())[:4] # Shorter random suffix
        safe_extended_id_part = extended_id.replace(" ", "_").replace("/", "_")
        image_extension = ".jpg" # Determine from header or assume based on generate_card_image_bytes output
        image_filename_for_blob = f"cards/{safe_extended_id_part}-{random_suffix}{image_extension}"

        log(f"Uploading final image to Vercel Blob as: {image_filename_for_blob}", request_id=request_id)
        uploaded_image_url = await blob_service.upload_image_to_blob(image_filename_for_blob, final_image_bytes)
        log(f"Image uploaded successfully to Vercel Blob: {uploaded_image_url}", request_id=request_id)

        # Update Supabase record
        await supabase_service.finalize_card_record_update(data.db_id, uploaded_image_url, ai_details_to_store)

        total_duration = time.time() - request_start_time
        log(f"Card generation finalized successfully for DB ID {data.db_id} in {total_duration:.2f}s. Image URL: {uploaded_image_url}", request_id=request_id)
        
        return FinalizeCardResponse(
            message="Card finalized successfully",
            db_id=data.db_id,
            extended_id=extended_id,
            image_url=uploaded_image_url,
            ai_details_used=ai_details_to_store
        )

    except ConnectionError as ce: # Catch if Supabase client not init
        error(f"Supabase connection error in finalize_card_generation_route: {str(ce)}", request_id=request_id)
        raise HTTPException(status_code=503, detail="Database service not available.")
    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        error(f"Error in finalize_card_generation_route (router) for DB ID {data.db_id}: {str(e)}", request_id=request_id)
        error(f"Traceback: {traceback.format_exc()}", request_id=request_id)
        raise HTTPException(status_code=500, detail=f"An error occurred during card finalization: {str(e)}") 