from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, Form
from supabase import Client as SupabaseClient
from typing import Dict, Any, Optional
import base64
import io

from ..config import (
    SUPABASE_URL, SUPABASE_SERVICE_KEY, BLOB_READ_WRITE_TOKEN,
    DEFAULT_STATUS_PROCESSING, DEFAULT_STATUS_COMPLETED, DEFAULT_STATUS_FAILED,
    ENABLE_AI_CARD_DETAILS
)
from ..models.card_generation_models import (
    CardGenerationCreateRequest, CardGenerationRecord, InitiateCardGenerationResponse,
    CardGenerationUpdateRequest
)
from ..services.supabase_service import create_card_generation_record, update_card_generation_status
from ..services.blob_service import BlobService
from ..utils.logger import log, error
from ..dependencies import verify_api_key
from ..utils.card_utils import generate_card_image_bytes, generate_back_card_image_bytes
from ..utils.color_utils import hex_to_rgb, rgb_to_cmyk
from ..utils.ai_utils import generate_ai_card_details
from ..utils.common_utils import generate_random_suffix

router = APIRouter()

# Initialize Supabase client
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
    card_name: str = Form(...),
    photo_date: Optional[str] = Form(None),  # New optional field from client-side EXIF extraction
    photo_location: Optional[str] = Form(None),  # New optional field from client-side EXIF extraction
    photo_latitude: Optional[str] = Form(None),  # GPS coordinates
    photo_longitude: Optional[str] = Form(None),  # GPS coordinates
    user_prompt: Optional[str] = Body(None), # Stored in metadata, not currently used for AI call generation
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
        log(f"finalize_card_generation: Received user_image.filename: {user_image.filename}, user_image.content_type: {user_image.content_type}", request_id=str(db_id))

        # Convert user_image_bytes to data URL for generate_card_image_bytes
        user_image_content_type = user_image.content_type or 'image/png'
        user_image_data_url = f"data:{user_image_content_type};base64,{base64.b64encode(user_image_bytes).decode('utf-8')}"

        # Log the received EXIF data
        if photo_date or photo_location or photo_latitude or photo_longitude:
            log(f"Client-side EXIF data for DB ID {db_id}: Date='{photo_date}', Location='{photo_location}', GPS='{photo_latitude},{photo_longitude}'", request_id=str(db_id))
        else:
            log(f"No EXIF data received from client for DB ID {db_id}", request_id=str(db_id))

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
            except ValueError as ve:
                # Check if this ValueError is specifically our timeout error
                if "AI generation timed out" in str(ve):
                    log(f"AI details generation timed out for DB ID {db_id}: {str(ve)}", level="ERROR", request_id=str(db_id))
                    raw_ai_response_for_metadata = {"error": str(ve), "status": "AI call timed out"}
                    raise HTTPException(status_code=408, detail="AI generation timed out. Please try again.")
                else:
                    log(f"AI details generation failed with ValueError for DB ID {db_id}: {str(ve)}. Proceeding with fallback details.", level="ERROR", request_id=str(db_id))
                    raw_ai_response_for_metadata = {"error": str(ve), "status": "AI call failed (ValueError)"}
                    raise HTTPException(status_code=500, detail="AI failed to process details. Please try again.")
            except Exception as ai_exc:
                log(f"AI details generation failed for DB ID {db_id}: {str(ai_exc)}. Proceeding with fallback details.", level="ERROR", request_id=str(db_id))
                raw_ai_response_for_metadata = {"error": str(ai_exc), "status": "AI call failed"}
                raise HTTPException(status_code=500, detail="An unexpected error occurred with AI processing. Please try again.")
        else:
            log(f"AI Card Details are disabled. Using provided card name: {card_name}", request_id=str(db_id))
            raw_ai_response_for_metadata = {"status": "AI disabled"}

        # --- Prepare card details for image generation --- 
        card_details_for_image_gen = {
            "shade_freude_text": "ShadeFREUDE",
            "colorName": processed_ai_details.get("colorName", card_name.upper()), 
            "extendedId": extended_id,
            "hex_code": hex_color,
            "rgb_code": f"{rgb_tuple[0]} {rgb_tuple[1]} {rgb_tuple[2]}",
            "cmyk_code": f"{cmyk_tuple[0]} {cmyk_tuple[1]} {cmyk_tuple[2]} {cmyk_tuple[3]}",
            "phoneticName": processed_ai_details.get("phoneticName", "[ˈdʌmi fəˈnɛtɪk]"), # Fallback if AI fails after being enabled
            "article": processed_ai_details.get("article", "[noun]"),
            "description": processed_ai_details.get("description", "This is a detailed dummy description for the color when AI is not available. It provides a bit more text for layout testing.")
        }

        generated_images_for_blob = []
        orientations = ["horizontal", "vertical"]
        
        # Get the current output format from the card generation function
        # TODO: Make this configurable later, for now detect from function signature
        output_format = "PNG"  # Default format, will be configurable later
        file_extension = "tiff" if output_format.upper() == "TIFF" else "png"
        content_type = "image/tiff" if output_format.upper() == "TIFF" else "image/png"
        
        for orientation in orientations:
            img_bytes = await generate_card_image_bytes(
                cropped_image_data_url=user_image_data_url, 
                card_details=card_details_for_image_gen,
                hex_color_input=hex_color,
                orientation=orientation,
                request_id=str(db_id),
                photo_date=photo_date,
                photo_location=photo_location
            )
            random_suffix = generate_random_suffix()
            
            generated_images_for_blob.append({
                "data": img_bytes,
                "filename": f"{extended_id.replace(' ', '_')}_front_{orientation}_{random_suffix}.{file_extension}",
                "content_type": content_type,
                "orientation": orientation
            })

        # Upload images to Vercel Blob (now a synchronous call)
        log(f"Uploading {len(generated_images_for_blob)} images for DB ID: {db_id}")
        uploaded_image_info = blob_service.upload_multiple_images(generated_images_for_blob)
        log(f"Images uploaded for DB ID: {db_id}. Result: {uploaded_image_info}")
        
        # Prepare metadata and image URLs for Supabase update
        update_payload = {
            "metadata": {
                "card_name": card_details_for_image_gen["colorName"],
                "user_provided_initial_name": card_name,
                "user_prompt": user_prompt,
                "ai_info": raw_ai_response_for_metadata,
                "original_filename": user_image.filename,
                "image_generation_details": card_details_for_image_gen,
                "uploaded_blob_info": uploaded_image_info,
                "exif_data_extracted": {
                    "photo_date": photo_date,
                    "photo_location_country": photo_location
                }
            },
        }

        # Add EXIF data to dedicated database columns (for better performance and querying)
        if photo_location:
            update_payload["photo_location_country"] = photo_location
        else:
            log(f"No photo_location received from frontend for DB ID: {db_id}", request_id=str(db_id))

        # Store GPS coordinates if available
        if photo_latitude and photo_longitude:
            try:
                lat = float(photo_latitude)
                lng = float(photo_longitude)
                coordinates = {"lat": lat, "lng": lng}
                update_payload["photo_location_coordinates"] = coordinates
            except (ValueError, TypeError) as coord_error:
                log(f"Failed to parse coordinates lat='{photo_latitude}', lng='{photo_longitude}': {coord_error}", level="WARNING", request_id=str(db_id))
        
        if photo_date:
            log(f"Processing photo_date: '{photo_date}' for DB ID: {db_id}", request_id=str(db_id))
            # Convert photo_date string to proper timestamp format if needed
            # Note: photo_date from frontend is in format like "2024/05/28" 
            # We need to convert it to a proper ISO timestamp for the database
            try:
                from datetime import datetime
                if photo_date:
                    # Parse the date string and convert to ISO format
                    # Frontend sends dates like "2024/05/28" 
                    parsed_date = datetime.strptime(photo_date, "%Y/%m/%d")
                    iso_date = parsed_date.isoformat() + "+00:00"  # Add UTC timezone
                    update_payload["photo_date"] = iso_date
                    log(f"Converted photo_date '{photo_date}' to ISO: '{iso_date}' for DB ID: {db_id}", request_id=str(db_id))
            except Exception as date_parse_error:
                log(f"Failed to parse photo_date '{photo_date}': {date_parse_error}. Storing as-is.", level="WARNING", request_id=str(db_id))
                # Store the original string if parsing fails
                update_payload["photo_date"] = photo_date
        else:
            log(f"No photo_date received from frontend for DB ID: {db_id}", request_id=str(db_id))

        log(f"Final update_payload keys for DB ID {db_id}: {list(update_payload.keys())}", request_id=str(db_id))
        if "photo_location_country" in update_payload:
            log(f"photo_location_country value: '{update_payload['photo_location_country']}'", request_id=str(db_id))
        if "photo_date" in update_payload:
            log(f"photo_date value: '{update_payload['photo_date']}'", request_id=str(db_id))

        # Add direct columns for horizontal and vertical URLs if they exist in the table
        if uploaded_image_info.get("horizontal", {}).get("url"):
            update_payload["front_horizontal_image_url"] = uploaded_image_info["horizontal"]["url"]
        if uploaded_image_info.get("vertical", {}).get("url"):
            update_payload["front_vertical_image_url"] = uploaded_image_info["vertical"]["url"]

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

@router.post("/cards/{db_id}/add-note",
             response_model=CardGenerationRecord,
             dependencies=[Depends(verify_api_key)])
async def add_note_to_card(
    db_id: int,
    payload: Optional[Dict[str, Optional[str]]] = Body(None) # Expecting {"note_text": "..."} or None/empty for skip
):
    """
    Adds a note to the back of a card and generates corresponding back images.
    If note_text is None or empty, it generates default back images.
    """
    if not supabase_client or not blob_service:
        error("Supabase client or Blob service not available for add_note_to_card")
        raise HTTPException(status_code=503, detail="A required service is unavailable.")

    note_text = payload.get("note_text") if payload else None

    try:
        log(f"Adding note for DB ID: {db_id}. Note provided: {bool(note_text)}")

        # 1. Fetch the existing card record to get hex_color and extended_id
        fetch_response = supabase_client.table("card_generations").select("hex_color, extended_id, created_at").eq("id", db_id).single().execute()
        if not fetch_response.data:
            error(f"No record found for DB ID: {db_id} when trying to add note.")
            raise HTTPException(status_code=404, detail=f"Card record with ID {db_id} not found.")
        
        record_data = fetch_response.data
        hex_color = record_data.get("hex_color")
        extended_id = record_data.get("extended_id", f"{str(db_id).zfill(9)} ???")
        created_at_str = record_data.get("created_at") # Will be used for default back if no note

        if not hex_color:
            # This should ideally not happen if the record exists
            raise HTTPException(status_code=400, detail="Hex color is missing for the specified card record.")

        # 2. Generate back images (details of this function in Step 4)
        
        back_images_for_blob = []
        orientations = ["horizontal", "vertical"]
        
        # Use same output format as front cards for consistency
        output_format = "PNG"  # Default format, will be configurable later
        file_extension = "tiff" if output_format.upper() == "TIFF" else "png"
        content_type = "image/tiff" if output_format.upper() == "TIFF" else "image/png"
        
        for orientation in orientations:
            img_bytes = await generate_back_card_image_bytes(
                note_text=note_text,
                hex_color_input=hex_color, 
                orientation=orientation,
                created_at_iso_str=created_at_str, 
                request_id=str(db_id)
            )
            random_suffix = generate_random_suffix()
            back_images_for_blob.append({
                "data": img_bytes,
                "filename": f"{extended_id.replace(' ', '_')}_back_{orientation}_{random_suffix}.{file_extension}",
                "content_type": content_type,
                "orientation": orientation
            })

        log(f"Preparing to upload {len(back_images_for_blob)} back images for DB ID: {db_id}")
        uploaded_back_image_info = blob_service.upload_multiple_images(back_images_for_blob)
        log(f"Back images uploaded for DB ID: {db_id}. Result: {uploaded_back_image_info}")

        # 3. Prepare payload for database update
        update_payload_for_note = {
            "note_text": note_text if note_text and note_text.strip() else None,
            "has_note": bool(note_text and note_text.strip()),
        }
        if uploaded_back_image_info.get("horizontal", {}).get("url"):
            update_payload_for_note["back_horizontal_image_url"] = uploaded_back_image_info["horizontal"]["url"]
        if uploaded_back_image_info.get("vertical", {}).get("url"):
            update_payload_for_note["back_vertical_image_url"] = uploaded_back_image_info["vertical"]["url"]

        # 4. Update the database record
        # Note: We are not changing the main card 'status' here, just adding note-related info.
        updated_record_response = (
            supabase_client.table("card_generations")
            .update(update_payload_for_note)
            .eq("id", db_id)
            .execute()
        )

        if not updated_record_response.data or len(updated_record_response.data) == 0:
            error_msg = f"Failed to update record ID {db_id} with note details."
            if updated_record_response.error:
                error_msg += f" Details: {updated_record_response.error.message}"
            error(error_msg)
            raise Exception(error_msg)
        
        log(f"Successfully updated record ID {db_id} with note and back image URLs.")
        return CardGenerationRecord.model_validate(updated_record_response.data[0])

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        error_msg = f"Error in add_note_to_card for DB ID {db_id}: {str(e)}"
        error(error_msg)
        # Potentially update status to a specific 'note_failed' status if desired, or just log
        raise HTTPException(status_code=500, detail=error_msg)