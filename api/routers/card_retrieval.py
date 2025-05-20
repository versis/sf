from fastapi import APIRouter, Depends, HTTPException
from supabase import Client as SupabaseClient
from typing import Any, Dict

from ..config import SUPABASE_URL, SUPABASE_SERVICE_KEY # Assuming these are in your config
from ..utils.logger import info, warning, error
from ..models.card_generation_models import CardGenerationRecord
from typing import List

router = APIRouter()

# Initialize Supabase client (consider a shared dependency)
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    supabase_client = SupabaseClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)
else:
    supabase_client = None
    warning("Card Retrieval Router: Supabase client not initialized due to missing URL or Key.")

# Define a Pydantic model for the response for better validation and OpenAPI docs
# This should match the CardDetails interface in app/color/[id]/page.tsx
from pydantic import BaseModel, Field
from typing import Optional

class CardDetailsResponse(BaseModel):
    extendedId: Optional[str] = Field(None, alias="extended_id")
    hexColor: Optional[str] = Field(None, alias="hex_color")
    colorName: Optional[str] = None
    description: Optional[str] = None
    phoneticName: Optional[str] = None
    article: Optional[str] = None
    horizontalImageUrl: Optional[str] = Field(None, alias="horizontal_image_url")
    verticalImageUrl: Optional[str] = Field(None, alias="vertical_image_url")

    class Config:
        populate_by_name = True # Allows using alias for field names from DB

@router.get("/generations", response_model=List[CardGenerationRecord])
async def get_generations(limit: int = 30, offset: int = 0):
    if not supabase_client:
        raise HTTPException(status_code=503, detail="Database service unavailable.")

    info(f"Attempting to retrieve generations with limit: {limit}, offset: {offset}")
    
    try:
        db_response = (
            supabase_client.table("card_generations")
            .select("id, extended_id, hex_color, status, metadata, horizontal_image_url, vertical_image_url, created_at, updated_at")
            .order("created_at", desc=True)
            .limit(limit)
            .offset(offset)
            .execute()
        )

        if db_response.data is None: # Check if data is None, could happen if execute() returns unexpected result
            warning(f"No generations found or error in query. Limit: {limit}, Offset: {offset}")
            return [] # Return empty list if no data or error
        
        # The response.data should already be a list of dicts suitable for CardGenerationRecord.model_validate
        generations = [CardGenerationRecord.model_validate(item) for item in db_response.data]
        info(f"Successfully retrieved {len(generations)} generations.")
        return generations

    except Exception as e:
        error(f"Error retrieving generations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving generations: {str(e)}")

@router.get(
    "/retrieve-card-by-extended-id/{extended_id_slug}", 
    response_model=CardDetailsResponse,
    response_model_by_alias=False # Ensure API response uses field names (camelCase)
)
async def retrieve_card_by_extended_id(extended_id_slug: str):
    if not supabase_client:
        raise HTTPException(status_code=503, detail="Database service unavailable.")

    info(f"Attempting to retrieve card with extended_id_slug: {extended_id_slug}")
    
    # Reverse the slug transformation to get the original extended_id format
    # Slug: "000000057-fe-f" -> Original: "000000057 FE F"
    original_extended_id = extended_id_slug.replace('-', ' ').upper()
    info(f"Converted slug to original format for query: {original_extended_id}")
    
    try:
        db_response = (
            supabase_client.table("card_generations")
            .select("hex_color, horizontal_image_url, vertical_image_url, extended_id, metadata")
            .eq("extended_id", original_extended_id) # Query directly on extended_id
            .single()
            .execute()
        )

        if not db_response.data:
            warning(f"No card found for original_extended_id: {original_extended_id} (derived from slug: {extended_id_slug})")
            raise HTTPException(status_code=404, detail="Card not found.")
        
        card_data = db_response.data
        metadata = card_data.get("metadata", {})
        image_gen_details = metadata.get("image_generation_details", {})

        response_data = CardDetailsResponse(
            extended_id=card_data.get("extended_id"),
            hex_color=card_data.get("hex_color"),
            colorName=image_gen_details.get("colorName"),
            description=image_gen_details.get("description"),
            phoneticName=image_gen_details.get("phoneticName"),
            article=image_gen_details.get("article"),
            horizontal_image_url=card_data.get("horizontal_image_url"),
            vertical_image_url=card_data.get("vertical_image_url")
        )
        
        info(f"Card found for original_extended_id: {original_extended_id}. Prepared data: {response_data.model_dump(by_alias=True)}")
        return response_data

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        error(f"Error retrieving card by original_extended_id {original_extended_id} (derived from slug {extended_id_slug}): {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving card data: {str(e)}") 