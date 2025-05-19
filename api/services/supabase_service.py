import traceback
from supabase import Client as SupabaseClient, PostgrestAPIResponse
from ..models.card_generation_models import CardGenerationCreateRequest, CardGenerationRecord
from ..core.config import CARD_ID_SUFFIX, DB_ID_PADDING_LENGTH, DEFAULT_STATUS_PENDING
from ..utils.logger import log, error # Make sure logger is correctly placed

async def create_card_generation_record(
    db: SupabaseClient,
    payload: CardGenerationCreateRequest
) -> CardGenerationRecord:
    """
    Creates an initial record in the 'card_generations' table, 
    generates an extended_id, and updates the record with this ID.
    """
    try:
        log(f"Attempting to insert card generation record for hex: {payload.hex_color}")
        
        initial_data = {
            "hex_color": payload.hex_color,
            "status": DEFAULT_STATUS_PENDING,
            # extended_id, metadata, image_url are initially null or handled by DB default
        }
        
        # Step 1: Insert the initial record to get the auto-incremented 'id'
        insert_response: PostgrestAPIResponse = db.table("card_generations").insert(initial_data).execute()

        if not insert_response.data or len(insert_response.data) == 0:
            error_msg = "Failed to insert initial card generation record into Supabase."
            if insert_response.error:
                error_msg += f" Details: Code: {insert_response.error.code}, Message: {insert_response.error.message}"
            error(error_msg)
            raise Exception(error_msg)

        inserted_record = insert_response.data[0]
        db_id = inserted_record["id"]
        log(f"Initial record inserted with DB ID: {db_id}")

        # Step 2: Generate the extended_id
        formatted_db_id = str(db_id).zfill(DB_ID_PADDING_LENGTH)
        extended_id = f"{formatted_db_id} {CARD_ID_SUFFIX}"
        log(f"Generated extended_id: {extended_id} for DB ID: {db_id}")

        # Step 3: Update the record with the generated extended_id
        update_response: PostgrestAPIResponse = (
            db.table("card_generations")
            .update({"extended_id": extended_id})
            .eq("id", db_id)
            .execute()
        )

        if not update_response.data or len(update_response.data) == 0:
            error_msg = f"Failed to update record ID {db_id} with extended_id."
            if update_response.error:
                error_msg += f" Details: Code: {update_response.error.code}, Message: {update_response.error.message}"
            error(error_msg)
            # Attempt to delete the orphaned record if update fails
            try:
                log(f"Attempting to cleanup orphaned record ID {db_id} due to update failure.")
                db.table("card_generations").delete().eq("id", db_id).execute()
                log(f"Successfully cleaned up orphaned record ID {db_id}.")
            except Exception as cleanup_e:
                error(f"Failed to cleanup orphaned record ID {db_id}: {str(cleanup_e)}")
            raise Exception(error_msg)
        
        log(f"Successfully updated record ID {db_id} with extended_id.")
        
        # Fetch the fully updated record to return (optional, but good practice)
        # Or, construct from available data if confident
        final_record_data = update_response.data[0]

        return CardGenerationRecord(
            id=final_record_data["id"],
            extended_id=final_record_data["extended_id"],
            hex_color=final_record_data["hex_color"],
            status=final_record_data["status"],
            metadata=final_record_data.get("metadata"),
            image_url=final_record_data.get("image_url"),
            created_at=final_record_data.get("created_at"),
            updated_at=final_record_data.get("updated_at")
        )
            
    except Exception as e:
        error_detail = f"Exception in create_card_generation_record for hex {payload.hex_color}: {str(e)}"
        error(error_detail)
        error(traceback.format_exc()) # Log the full traceback
        raise Exception(error_detail) # Re-raise with a more specific message or the original exception

async def update_card_generation_status(
    db: SupabaseClient,
    record_id: int,
    status: str,
    details: dict = None
) -> CardGenerationRecord:
    """Updates the status and optionally other details of a card generation record."""
    try:
        log(f"Updating card generation record ID {record_id} to status: {status}")
        update_data = {"status": status}
        if details:
            update_data.update(details) # e.g., metadata, image_url, error_message
        
        response: PostgrestAPIResponse = (
            db.table("card_generations")
            .update(update_data)
            .eq("id", record_id)
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            log(f"Successfully updated record ID {record_id}.")
            return CardGenerationRecord.model_validate(response.data[0]) # Pydantic v2
        else:
            error_msg = f"Failed to update record ID {record_id}."
            if response.error:
                error_msg += f" Details: {response.error.message}"
            error(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        error(f"Exception in update_card_generation_status for ID {record_id}: {str(e)}")
        error(traceback.format_exc())
        raise 