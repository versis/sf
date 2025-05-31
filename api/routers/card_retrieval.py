from fastapi import APIRouter, Depends, HTTPException
from supabase import Client as SupabaseClient
from typing import Any, Dict, Optional, List

from ..config import SUPABASE_URL, SUPABASE_SERVICE_KEY # Assuming these are in your config
from ..utils.logger import info, warning, error
from ..models.card_generation_models import CardGenerationRecord

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

class CardDetailsResponse(BaseModel):
    id: Optional[int] = None
    extendedId: Optional[str] = Field(None, alias="extended_id")
    hexColor: Optional[str] = Field(None, alias="hex_color")
    status: Optional[str] = None
    card_name: Optional[str] = None
    
    frontHorizontalImageUrl: Optional[str] = Field(None, alias="front_horizontal_image_url")
    frontVerticalImageUrl: Optional[str] = Field(None, alias="front_vertical_image_url")
    
    noteText: Optional[str] = Field(None, alias="note_text")
    hasNote: Optional[bool] = Field(None, alias="has_note")
    backHorizontalImageUrl: Optional[str] = Field(None, alias="back_horizontal_image_url")
    backVerticalImageUrl: Optional[str] = Field(None, alias="back_vertical_image_url")
    
    aiName: Optional[str] = Field(None, alias="ai_name")
    aiPhonetic: Optional[str] = Field(None, alias="ai_phonetic")
    aiArticle: Optional[str] = Field(None, alias="ai_article")
    aiDescription: Optional[str] = Field(None, alias="ai_description")

    # New EXIF data fields - use snake_case to match frontend expectations
    photo_date: Optional[str] = None  # Direct mapping from DB column
    photo_location: Optional[str] = None  # Will be populated from photo_location_country
    photo_location_coordinates: Optional[Dict[str, float]] = None  # GPS coordinates as {"lat": float, "lng": float}

    createdAt: Optional[str] = Field(None, alias="created_at")
    updatedAt: Optional[str] = Field(None, alias="updated_at")

    class Config:
        populate_by_name = True

class BatchCardResponse(BaseModel):
    """Response for batch card retrieval."""
    cards: Dict[str, Optional[CardDetailsResponse]]  # Maps extended_id to card data (or None if not found)
    
# Removed caching for simplicity

class BatchRetrieveRequest(BaseModel):
    extended_ids: List[str]

@router.post("/batch-retrieve-cards", response_model=BatchCardResponse)
async def batch_retrieve_cards(request: BatchRetrieveRequest):
    """
    Retrieve multiple cards by their extended IDs in a single optimized query.
    
    Args:
        request: Request containing list of extended IDs to retrieve
        
    Returns:
        Dict mapping each extended_id to its card data (or None if not found)
    """
    if not supabase_client:
        raise HTTPException(status_code=503, detail="Database service unavailable.")

    extended_ids = request.extended_ids
    if not extended_ids:
        return BatchCardResponse(cards={})

    info(f"Batch retrieving {len(extended_ids)} cards")
    
    # PERFORMANCE OPTIMIZATION: Extract IDs and use IN query with primary keys
    from ..utils.id_utils import extract_id_from_extended_id
    
    # Build mapping of extended_id to db_id for fast lookup
    id_mapping = {}
    db_ids = []
    fallback_extended_ids = []
    
    for extended_id in extended_ids:
        db_id = extract_id_from_extended_id(extended_id)
        if db_id is not None:
            id_mapping[db_id] = extended_id
            db_ids.append(db_id)
        else:
            fallback_extended_ids.append(extended_id)
    
    results = {}
    
    try:
        # Fast path: Batch query by primary key IDs
        if db_ids:
            info(f"Using optimized batch ID query for {len(db_ids)} cards")
            db_response = (
                supabase_client.table("card_generations")
                .select("id, extended_id, hex_color, status, metadata, front_horizontal_image_url, front_vertical_image_url, note_text, has_note, back_horizontal_image_url, back_vertical_image_url, photo_location_country, photo_location_coordinates, photo_date, created_at, updated_at")
                .in_("id", db_ids)
                .execute()
            )
            
            if db_response.data:
                for card_data in db_response.data:
                    extended_id = card_data.get("extended_id")
                    if extended_id:
                        metadata = card_data.get("metadata", {})
                        db_card_name = metadata.get("card_name")
                        ai_card_name = metadata.get("ai_info", {}).get("colorName")
                        final_card_name = db_card_name or ai_card_name or "Color Card"

                        card_response = CardDetailsResponse(
                            id=card_data.get("id"),
                            extended_id=extended_id,
                            hex_color=card_data.get("hex_color"),
                            status=card_data.get("status"),
                            card_name=final_card_name,
                            front_horizontal_image_url=card_data.get("front_horizontal_image_url"),
                            front_vertical_image_url=card_data.get("front_vertical_image_url"),
                            note_text=card_data.get("note_text"),
                            has_note=card_data.get("has_note"),
                            back_horizontal_image_url=card_data.get("back_horizontal_image_url"),
                            back_vertical_image_url=card_data.get("back_vertical_image_url"),
                            ai_name=metadata.get("ai_info", {}).get("colorName"),
                            ai_phonetic=metadata.get("ai_info", {}).get("phoneticName"),
                            ai_article=metadata.get("ai_info", {}).get("article"),
                            ai_description=metadata.get("ai_info", {}).get("description"),
                            photo_date=card_data.get("photo_date"),
                            photo_location=card_data.get("photo_location_country"),
                            photo_location_coordinates=card_data.get("photo_location_coordinates"),
                            created_at=card_data.get("created_at"),
                            updated_at=card_data.get("updated_at")
                        )
                        results[extended_id] = card_response

        # Fallback path: Query by extended_id for any that couldn't be parsed
        if fallback_extended_ids:
            info(f"Using fallback extended_id query for {len(fallback_extended_ids)} cards")
            fallback_response = (
                supabase_client.table("card_generations")
                .select("id, extended_id, hex_color, status, metadata, front_horizontal_image_url, front_vertical_image_url, note_text, has_note, back_horizontal_image_url, back_vertical_image_url, photo_location_country, photo_location_coordinates, photo_date, created_at, updated_at")
                .in_("extended_id", fallback_extended_ids)
                .execute()
            )
            
            if fallback_response.data:
                for card_data in fallback_response.data:
                    extended_id = card_data.get("extended_id")
                    if extended_id:
                        metadata = card_data.get("metadata", {})
                        db_card_name = metadata.get("card_name")
                        ai_card_name = metadata.get("ai_info", {}).get("colorName")
                        final_card_name = db_card_name or ai_card_name or "Color Card"

                        card_response = CardDetailsResponse(
                            id=card_data.get("id"),
                            extended_id=extended_id,
                            hex_color=card_data.get("hex_color"),
                            status=card_data.get("status"),
                            card_name=final_card_name,
                            front_horizontal_image_url=card_data.get("front_horizontal_image_url"),
                            front_vertical_image_url=card_data.get("front_vertical_image_url"),
                            note_text=card_data.get("note_text"),
                            has_note=card_data.get("has_note"),
                            back_horizontal_image_url=card_data.get("back_horizontal_image_url"),
                            back_vertical_image_url=card_data.get("back_vertical_image_url"),
                            ai_name=metadata.get("ai_info", {}).get("colorName"),
                            ai_phonetic=metadata.get("ai_info", {}).get("phoneticName"),
                            ai_article=metadata.get("ai_info", {}).get("article"),
                            ai_description=metadata.get("ai_info", {}).get("description"),
                            photo_date=card_data.get("photo_date"),
                            photo_location=card_data.get("photo_location_country"),
                            photo_location_coordinates=card_data.get("photo_location_coordinates"),
                            created_at=card_data.get("created_at"),
                            updated_at=card_data.get("updated_at")
                        )
                        results[extended_id] = card_response

        # Ensure all requested IDs are in the response (with None for not found)
        final_results = {}
        for extended_id in extended_ids:
            final_results[extended_id] = results.get(extended_id)

        info(f"Batch retrieval complete. Found {len([r for r in final_results.values() if r is not None])}/{len(extended_ids)} cards")
        
        return BatchCardResponse(cards=final_results)

    except Exception as e:
        error(f"Error in batch card retrieval: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred during batch retrieval: {str(e)}")

@router.get("/generations", response_model=List[CardGenerationRecord])
async def get_generations(limit: int = 30, offset: int = 0):
    if not supabase_client:
        raise HTTPException(status_code=503, detail="Database service unavailable.")

    info(f"Attempting to retrieve generations with limit: {limit}, offset: {offset}")
    
    try:
        db_response = (
            supabase_client.table("card_generations")
            .select("id, extended_id, hex_color, status, metadata, front_horizontal_image_url, front_vertical_image_url, note_text, has_note, back_horizontal_image_url, back_vertical_image_url, photo_location_country, photo_location_coordinates, photo_date, created_at, updated_at")
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
    
    # PERFORMANCE OPTIMIZATION: Try to extract ID and query by primary key first
    from ..utils.id_utils import extract_id_from_extended_id
    
    db_id = extract_id_from_extended_id(original_extended_id)
    
    try:
        if db_id is not None:
            # Fast path: Query by primary key ID
            info(f"Using optimized ID-based query for db_id: {db_id}")
            db_response = (
                supabase_client.table("card_generations")
                .select("id, extended_id, hex_color, status, metadata, front_horizontal_image_url, front_vertical_image_url, note_text, has_note, back_horizontal_image_url, back_vertical_image_url, photo_location_country, photo_location_coordinates, photo_date, created_at, updated_at")
                .eq("id", db_id)
                .single()
                .execute()
            )
        else:
            # Fallback: Query by extended_id (slower but backward compatible)
            info(f"Using fallback extended_id query for: {original_extended_id}")
            db_response = (
                supabase_client.table("card_generations")
                .select("id, extended_id, hex_color, status, metadata, front_horizontal_image_url, front_vertical_image_url, note_text, has_note, back_horizontal_image_url, back_vertical_image_url, photo_location_country, photo_location_coordinates, photo_date, created_at, updated_at")
                .eq("extended_id", original_extended_id) # Query directly on extended_id
                .single()
                .execute()
            )

        if not db_response.data:
            warning(f"No card found for original_extended_id: {original_extended_id} (derived from slug: {extended_id_slug})")
            raise HTTPException(status_code=404, detail="Card not found.")
        
        card_data = db_response.data
        metadata = card_data.get("metadata", {})
        # Determine card_name from metadata (consistent with Next.js API route)
        db_card_name = metadata.get("card_name") # From finalize step
        ai_card_name = metadata.get("ai_info", {}).get("colorName") # From AI
        final_card_name = db_card_name or ai_card_name or "Color Card"

        response_data = CardDetailsResponse(
            id=card_data.get("id"),
            extended_id=card_data.get("extended_id"),
            hex_color=card_data.get("hex_color"),
            status=card_data.get("status"),
            card_name=final_card_name,
            front_horizontal_image_url=card_data.get("front_horizontal_image_url"),
            front_vertical_image_url=card_data.get("front_vertical_image_url"),
            note_text=card_data.get("note_text"),
            has_note=card_data.get("has_note"),
            back_horizontal_image_url=card_data.get("back_horizontal_image_url"),
            back_vertical_image_url=card_data.get("back_vertical_image_url"),
            ai_name=metadata.get("ai_info", {}).get("colorName"), 
            ai_phonetic=metadata.get("ai_info", {}).get("phoneticName"),
            ai_article=metadata.get("ai_info", {}).get("article"),
            ai_description=metadata.get("ai_info", {}).get("description"),
            photo_date=card_data.get("photo_date"),
            photo_location=card_data.get("photo_location_country"),
            photo_location_coordinates=card_data.get("photo_location_coordinates"),
            created_at=card_data.get("created_at"),
            updated_at=card_data.get("updated_at")
        )
        
        info(f"Card found for original_extended_id: {original_extended_id}. Prepared data: {response_data.model_dump(by_alias=True)}")
        return response_data

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        error(f"Error retrieving card by original_extended_id {original_extended_id} (derived from slug {extended_id_slug}): {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving card data: {str(e)}") 