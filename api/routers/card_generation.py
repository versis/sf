from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
from supabase import Client as SupabaseClient
from typing import Dict, Any, Optional
import base64

from ..config import (
    SUPABASE_URL, SUPABASE_SERVICE_KEY, BLOB_READ_WRITE_TOKEN,
    DEFAULT_STATUS_PROCESSING, DEFAULT_STATUS_COMPLETED, DEFAULT_STATUS_FAILED,
    ENABLE_AI_CARD_DETAILS # Added import for AI flag
)
from ..models.card_generation_models import (
    CardGenerationCreateRequest, CardGenerationRecord, InitiateCardGenerationResponse,
    CardGenerationUpdateRequest # Ensure this is imported if used directly
)
from ..services.supabase_service import create_card_generation_record, update_card_generation_status
from ..services.blob_service import BlobService
from ..utils.logger import log, error
from ..dependencies import verify_api_key
from ..utils.card_utils import generate_card_image_bytes
from ..utils.color_utils import hex_to_rgb, rgb_to_cmyk
from ..utils.ai_utils import generate_ai_card_details # Added import for AI function

router = APIRouter()

# Initialize Supabase client
# This should ideally be managed via a dependency for better testing and reuse
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    supabase_client = SupabaseClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)
else:
    supabase_client = None
    log("Supabase client not initialized due to missing URL or Key.")

# Initialize BlobService
if BLOB_READ_WRITE_TOKEN:
    blob_service = BlobService(token=BLOB_READ_WRITE_TOKEN)
else:
    blob_service = None
    log("BlobService not initialized due to missing token.")

# ImageProcessor initialization was here, now fully removed.

@router.post("/initiate-card-generation", 
             response_model=InitiateCardGenerationResponse, 
             dependencies=[Depends(verify_api_key)])
async def initiate_card_generation(payload: CardGenerationCreateRequest):
    """
    Initiates the card generation process by creating a record in Supabase 
    and returning a unique ID (both db_id and extended_id).
    """
    if not supabase_client:
        error("Supabase client not available for initiate_card_generation")
        raise HTTPException(status_code=503, detail="Database service unavailable.")

    try:
        log(f"Initiating card generation for hex: {payload.hex_color}")
        record = await create_card_generation_record(db=supabase_client, payload=payload)
        log(f"Card generation initiated. DB ID: {record.id}, Extended ID: {record.extended_id}")
        return InitiateCardGenerationResponse(
            db_id=record.id,
            extended_id=record.extended_id,
            current_status=record.status
        )
    except Exception as e:
        error(f"Error in initiate_card_generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate card generation: {str(e)}")

@router.post("/finalize-card-generation/{db_id}", 
             response_model=CardGenerationRecord,
             dependencies=[Depends(verify_api_key)])
async def finalize_card_generation(
    db_id: int, 
    user_image: UploadFile = File(...),
    card_name: str = Body(...), # This will be a fallback if AI is off or fails
    user_prompt: Optional[str] = Body(None), # Stored in metadata, not currently used for AI call generation
    # ai_generated_details: Optional[Dict[str, Any]] = Body(None) # This param is now redundant if backend calls AI
):
    """
    Finalizes the card generation process:
    1. Receives the user's image and card name.
    2. Generates horizontal and vertical card images with the db_id and other details.
    3. Uploads these images to Vercel Blob storage.
    4. Updates the Supabase record with image URLs, metadata, and status.
    """
    if not supabase_client or not blob_service:
        error("Supabase client or Blob service not available for finalize_card_generation")
        raise HTTPException(status_code=503, detail="A required service is unavailable.")

    try:
        log(f"Finalizing card generation for DB ID: {db_id}") 
        
        # Fetch the initial record to get hex_color and extended_id
        fetch_response = supabase_client.table("card_generations").select("*").eq("id", db_id).single().execute()
        if not fetch_response.data:
            error(f"No record found for DB ID: {db_id}")
            raise HTTPException(status_code=404, detail=f"Card generation record with ID {db_id} not found.")
        
        record_data = fetch_response.data
        hex_color = record_data.get("hex_color")
        extended_id = record_data.get("extended_id", f"{str(db_id).zfill(9)} ???") 

        if not hex_color:
            raise HTTPException(status_code=400, detail="Hex color is missing from the specified record.")

        rgb_tuple = hex_to_rgb(hex_color)
        if not rgb_tuple:
            raise HTTPException(status_code=400, detail=f"Invalid hex color format in record: {hex_color}")
        cmyk_tuple = rgb_to_cmyk(rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])

        # Update status to processing
        await update_card_generation_status(supabase_client, db_id, DEFAULT_STATUS_PROCESSING)
        
        # Prepare image data
        user_image_bytes = await user_image.read()
        # Convert user_image_bytes to data URL for generate_card_image_bytes
        # Assuming user_image.content_type is available and correct (e.g., 'image/png', 'image/jpeg')
        user_image_content_type = user_image.content_type or 'image/png' # Default if not provided
        user_image_data_url = f"data:{user_image_content_type};base64,{base64.b64encode(user_image_bytes).decode('utf-8')}"

        # --- AI Details Generation Step --- 
        processed_ai_details = {} # Store details from AI or fallback
        raw_ai_response_for_metadata = None # Store raw AI response for logging/metadata

        if ENABLE_AI_CARD_DETAILS:
            log(f"AI Card Details enabled. Calling AI service for DB ID: {db_id}", request_id=str(db_id))
            try:
                # generate_ai_card_details is expected to return a dict like ColorCardDetails model
                processed_ai_details = await generate_ai_card_details(
                    hex_color=hex_color,
                    cropped_image_data_url=user_image_data_url,
                    request_id=str(db_id)
                )
                log(f"AI details received: {processed_ai_details}", request_id=str(db_id))
                raw_ai_response_for_metadata = processed_ai_details # Assuming this is the dict to store
            except Exception as ai_exc:
                log(f"AI details generation failed for DB ID {db_id}: {str(ai_exc)}. Proceeding with fallback details.", level="ERROR", request_id=str(db_id))
                raw_ai_response_for_metadata = {"error": str(ai_exc), "status": "AI call failed"}
                # Fallback details will be used (i.e., processed_ai_details remains empty or has defaults)
        else:
            log(f"AI Card Details are disabled. Using provided card name: {card_name}", request_id=str(db_id))
            raw_ai_response_for_metadata = {"status": "AI disabled"}

        # --- Prepare card details for image generation --- 
        card_details_for_image_gen = {
            "shade_freude_text": "ShadeFREUDE",
            "colorName": processed_ai_details.get("colorName", card_name.upper()), # Prioritize AI, fallback to user input
            "extendedId": extended_id,
            "hex_code": hex_color,
            "rgb_code": f"{rgb_tuple[0]} {rgb_tuple[1]} {rgb_tuple[2]}",
            "cmyk_code": f"{cmyk_tuple[0]} {cmyk_tuple[1]} {cmyk_tuple[2]} {cmyk_tuple[3]}",
            "phoneticName": processed_ai_details.get("phoneticName", ""), # Fallback to empty or placeholder
            "article": processed_ai_details.get("article", ""),
            "description": processed_ai_details.get("description", "Your unique shade.")
        }

        generated_images_for_blob = []
        orientations = ["horizontal", "vertical"]
        
        for orientation in orientations:
            img_bytes = await generate_card_image_bytes(
                cropped_image_data_url=user_image_data_url, 
                card_details=card_details_for_image_gen,
                hex_color_input=hex_color,
                orientation=orientation,
                request_id=str(db_id) 
            )
            generated_images_for_blob.append({
                "data": img_bytes,
                "filename": f"card_{extended_id.replace(' ', '_')}_{orientation}.png",
                "content_type": "image/png",
                "orientation": orientation
            })

        # Upload images to Vercel Blob (now a synchronous call)
        log(f"Uploading {len(generated_images_for_blob)} images for DB ID: {db_id}")
        uploaded_image_info = blob_service.upload_multiple_images(generated_images_for_blob) # Removed await
        log(f"Images uploaded for DB ID: {db_id}. Result: {uploaded_image_info}")
        
        # Prepare metadata and image URLs for Supabase update
        # Ensure keys here match actual column names in your Supabase table
        update_payload = {
            "metadata": {
                "card_name": card_details_for_image_gen["colorName"], # Store the final name used
                "user_provided_initial_name": card_name, # Keep track of original user input
                "user_prompt": user_prompt,
                "ai_info": raw_ai_response_for_metadata, # Store AI call outcome/details
                "original_filename": user_image.filename,
                "image_generation_details": card_details_for_image_gen,
                "uploaded_blob_info": uploaded_image_info # This correctly stores the dict with horizontal/vertical URLs
            },
        }

        # Add direct columns for horizontal and vertical URLs if they exist in the table
        # These should match your actual table column names.
        if uploaded_image_info.get("horizontal", {}).get("url"):
            update_payload["horizontal_image_url"] = uploaded_image_info["horizontal"]["url"]
        if uploaded_image_info.get("vertical", {}).get("url"):
            update_payload["vertical_image_url"] = uploaded_image_info["vertical"]["url"]

        # Update Supabase record with image URLs, metadata, and set status to completed
        final_record = await update_card_generation_status(
            db=supabase_client, 
            record_id=db_id, 
            status=DEFAULT_STATUS_COMPLETED, 
            details=update_payload
        )
        log(f"Card generation finalized and record updated for DB ID: {db_id}")
        return final_record

    except HTTPException as http_exc:
        raise http_exc 
    except Exception as e:
        error_msg = f"Error in finalize_card_generation for DB ID {db_id}: {str(e)}"
        error(error_msg)
        # Attempt to update status to failed in Supabase, storing error in metadata
        try:
            failure_details = {
                "metadata": {
                    "error_info": error_msg,
                    "original_user_image_filename": user_image.filename if user_image else None,
                    "attempted_card_name": card_name,
                    "ai_info_on_failure": raw_ai_response_for_metadata if 'raw_ai_response_for_metadata' in locals() else "AI not called or error before AI stage"
                }
            }
            await update_card_generation_status(supabase_client, db_id, DEFAULT_STATUS_FAILED, failure_details)
        except Exception as update_err:
            error(f"Additionally, failed to update status to 'failed' for DB ID {db_id}: {str(update_err)}")
        raise HTTPException(status_code=500, detail=error_msg)

# Example router inclusion comment was here, now fully removed. 