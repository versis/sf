# api/services/supabase_service.py
from supabase import create_client, Client as SupabaseClient
from typing import Dict, Any, Optional

from api.core.config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from api.utils.logger import info, error, warning

supabase_client: Optional[SupabaseClient] = None

def init_supabase_client():
    global supabase_client
    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        try:
            supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            info("Successfully initialized Supabase client in supabase_service.")
        except Exception as e:
            error(f"Failed to initialize Supabase client in supabase_service: {e}")
            supabase_client = None
    else:
        warning("Supabase URL or Service Key missing. Supabase client in supabase_service not initialized.")

# Call initialization when module is loaded
init_supabase_client()

def get_supabase_client() -> SupabaseClient:
    if not supabase_client:
        error("Supabase client requested but not initialized.")
        raise ConnectionError("Supabase client is not available. Check configuration and logs.")
    return supabase_client

async def create_initial_card_record(hex_color: str) -> Dict[str, Any]:
    client = get_supabase_client()
    response = await client.table("card_generations").insert({
        "hex_color": hex_color,
        "status": "pending_details"
    }).execute()
    if not response.data:
        raise Exception("Failed to insert initial card record or no data returned.")
    return response.data[0]

async def update_card_with_extended_id(db_id: int, extended_id: str) -> Dict[str, Any]:
    client = get_supabase_client()
    response = await client.table("card_generations").update({
        "extended_id": extended_id
    }).eq("id", db_id).execute()
    if not response.data:
        raise Exception(f"Failed to update record with extended_id for DB ID: {db_id}")
    return response.data[0]

async def get_card_for_finalization(db_id: int) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    response = await client.table("card_generations").select("id, extended_id, hex_color, status").eq("id", db_id).maybe_single().execute()
    return response.data

async def finalize_card_record_update(db_id: int, horizontal_image_url: str | None, vertical_image_url: str | None, metadata: Dict[str, Any]) -> Dict[str, Any]:
    client = get_supabase_client()
    update_payload = {
        "horizontal_image_url": horizontal_image_url,
        "vertical_image_url": vertical_image_url,
        "metadata": metadata,
        "status": "completed"
    }
    # Filter out None values to avoid setting columns to NULL if an image URL is missing
    update_payload_filtered = {k: v for k, v in update_payload.items() if v is not None}

    response = await client.table("card_generations").update(update_payload_filtered).eq("id", db_id).execute()
    if not response.data:
        raise Exception(f"Failed to finalize Supabase record for DB ID: {db_id}")
    return response.data[0] 