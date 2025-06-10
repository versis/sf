"""
Print generation router for creating A4 layouts from existing card TIFFs.
"""

from fastapi import APIRouter, HTTPException, Depends
from supabase import Client as SupabaseClient
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import requests
from PIL import Image
import io
import time

from ..config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from ..utils.logger import log, debug, error
from ..utils.print_utils import create_a4_layout_with_cards

router = APIRouter()

# Initialize Supabase client
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    supabase_client = SupabaseClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)
else:
    supabase_client = None
    log("Print Generation Router: Supabase client not initialized due to missing URL or Key.", level="WARNING")

class CreateA4LayoutRequest(BaseModel):
    """Request model for creating A4 layouts from existing card TIFFs."""
    extended_ids: List[str]
    passepartout_mm: float = 8
    target_content_width_mm: float = 146
    orientation: str = "horizontal"  # "horizontal" or "vertical"
    duplex_mode: bool = True  # If True, adjusts back layout for proper duplex printing
    output_prefix: str = "sf"  # Filename prefix

class A4LayoutResponse(BaseModel):
    """Response model for A4 layout generation."""
    success: bool
    message: str
    front_layout_size_mb: Optional[float] = None
    back_layout_size_mb: Optional[float] = None
    front_layout_file: Optional[str] = None
    back_layout_file: Optional[str] = None
    cards_processed: int = 0
    cards_found: int = 0

def download_image_from_url(url: str, request_id: str) -> Optional[Image.Image]:
    """Download an image from a URL and return as PIL Image."""
    try:
        debug(f"Downloading image from URL: {url}", request_id=request_id)
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))
        debug(f"Successfully downloaded image: {image.size}, mode: {image.mode}", request_id=request_id)
        return image
    except Exception as e:
        error(f"Failed to download image from {url}: {str(e)}", request_id=request_id)
        return None

@router.post("/create-a4-layouts", response_model=A4LayoutResponse)
async def create_a4_layouts_from_cards(request: CreateA4LayoutRequest):
    """
    Create A4 layouts for front and back sides from existing card TIFFs.
    
    Args:
        request: Contains extended_ids, passepartout settings, and layout parameters
        
    Returns:
        A4LayoutResponse with layout files and processing statistics
    """
    if not supabase_client:
        raise HTTPException(status_code=503, detail="Database service unavailable.")
    
    extended_ids = request.extended_ids
    if not extended_ids:
        raise HTTPException(status_code=400, detail="No extended IDs provided.")
    
    if len(extended_ids) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 cards allowed per A4 layout.")
    
    request_id = f"a4_layout_{hash(''.join(extended_ids)) % 10000:04d}"
    log(f"Creating A4 layouts for {len(extended_ids)} cards", request_id=request_id)
    
    try:
        # Query database for TIFF URLs
        from ..utils.id_utils import extract_id_from_extended_id
        
        # Build mapping for efficient queries
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
        
        cards_data = {}
        
        # Fast path: Query by primary key IDs
        if db_ids:
            debug(f"Querying database for {len(db_ids)} cards by ID", request_id=request_id)
            db_response = (
                supabase_client.table("card_generations")
                .select("id, extended_id, front_horizontal_tiff_url, back_horizontal_tiff_url, metadata")
                .in_("id", db_ids)
                .execute()
            )
            
            if db_response.data:
                for card_data in db_response.data:
                    extended_id = card_data.get("extended_id")
                    if extended_id:
                        cards_data[extended_id] = card_data
        
        # Fallback path: Query by extended_id
        if fallback_extended_ids:
            debug(f"Querying database for {len(fallback_extended_ids)} cards by extended_id", request_id=request_id)
            fallback_response = (
                supabase_client.table("card_generations")
                .select("id, extended_id, front_horizontal_tiff_url, back_horizontal_tiff_url, metadata")
                .in_("extended_id", fallback_extended_ids)
                .execute()
            )
            
            if fallback_response.data:
                for card_data in fallback_response.data:
                    extended_id = card_data.get("extended_id")
                    if extended_id:
                        cards_data[extended_id] = card_data
        
        cards_found = len(cards_data)
        log(f"Found {cards_found}/{len(extended_ids)} cards in database", request_id=request_id)
        
        if cards_found == 0:
            raise HTTPException(status_code=404, detail="No cards found for the provided extended IDs.")
        
        # Download front and back TIFF images
        # Store images with their corresponding extended_ids for proper ordering
        front_card_images = []  # List of tuples: (extended_id, image)
        back_card_images = []   # List of tuples: (extended_id, image)
        cards_processed = 0
        
        # Choose TIFF URLs based on orientation
        front_tiff_field = "front_horizontal_tiff_url" if request.orientation == "horizontal" else "front_vertical_tiff_url"
        back_tiff_field = "back_horizontal_tiff_url" if request.orientation == "horizontal" else "back_vertical_tiff_url"
        
        log(f"Using {request.orientation} orientation: {front_tiff_field}, {back_tiff_field}", request_id=request_id)
        
        for extended_id in extended_ids:
            card_data = cards_data.get(extended_id)
            if not card_data:
                log(f"Card {extended_id} not found, skipping", level="WARNING", request_id=request_id)
                continue
            
            front_tiff_url = card_data.get(front_tiff_field)
            back_tiff_url = card_data.get(back_tiff_field)
            
            # Download front TIFF
            if front_tiff_url:
                front_image = download_image_from_url(front_tiff_url, request_id)
                if front_image:
                    front_card_images.append((extended_id, front_image))
                    debug(f"Added front image for card {extended_id}", request_id=request_id)
                else:
                    log(f"Failed to download front TIFF for card {extended_id}", level="WARNING", request_id=request_id)
            else:
                log(f"No front TIFF URL for card {extended_id}", level="WARNING", request_id=request_id)
            
            # Download back TIFF
            if back_tiff_url:
                back_image = download_image_from_url(back_tiff_url, request_id)
                if back_image:
                    back_card_images.append((extended_id, back_image))
                    debug(f"Added back image for card {extended_id}", request_id=request_id)
                else:
                    log(f"Failed to download back TIFF for card {extended_id}", level="WARNING", request_id=request_id)
            else:
                log(f"No back TIFF URL for card {extended_id}", level="WARNING", request_id=request_id)
            
            cards_processed += 1
        
        # Extract images in the correct order for front and back
        front_images = [image for _, image in front_card_images]
        back_images = [image for _, image in back_card_images]
        
        # Note: Card order stays the same for both front and back
        # The duplex alignment is handled by horizontal positioning (left vs right)
        
        if not front_images and not back_images:
            raise HTTPException(status_code=404, detail="No TIFF images could be downloaded from the provided cards.")
        
        # Create A4 layouts and save to local files
        front_layout_bytes = None
        back_layout_bytes = None
        front_layout_size_mb = None
        back_layout_size_mb = None
        front_layout_file = None
        back_layout_file = None
        
        # Generate filename using new format: sf_w156_pp12_extendedids
        def clean_extended_id(extended_id: str) -> str:
            """Remove spaces and dashes from extended ID."""
            return extended_id.replace(" ", "").replace("-", "")
        
        # Clean extended IDs and join with underscores
        cleaned_ids = [clean_extended_id(ext_id) for ext_id in extended_ids]
        ids_part = "_".join(cleaned_ids)
        
        # Build filename components
        width_part = f"w{int(request.target_content_width_mm)}"
        passepartout_part = f"pp{int(request.passepartout_mm)}"
        
        # Create filename prefix: sf_w156_pp12_000000632FEF_000000633FEF_000000634FEF
        filename_prefix = f"{request.output_prefix}_{width_part}_{passepartout_part}_{ids_part}"
        
        if front_images:
            log(f"Creating front A4 layout with {len(front_images)} cards", request_id=request_id)
            front_layout_bytes = create_a4_layout_with_cards(
                card_images=front_images,
                target_content_width_mm=request.target_content_width_mm,
                passepartout_mm=request.passepartout_mm,
                duplex_back_side=False,  # Front side: positioned on left
                request_id=f"{request_id}_front"
            )
            front_layout_size_mb = len(front_layout_bytes) / 1024 / 1024
            
            # Save front layout to local file
            front_layout_file = f"{filename_prefix}_front.tiff"
            with open(front_layout_file, "wb") as f:
                f.write(front_layout_bytes)
            
            log(f"Front A4 layout created: {front_layout_size_mb:.1f}MB, saved as {front_layout_file}", request_id=request_id)
        
        if back_images:
            log(f"Creating back A4 layout with {len(back_images)} cards", request_id=request_id)
            back_layout_bytes = create_a4_layout_with_cards(
                card_images=back_images,
                target_content_width_mm=request.target_content_width_mm,
                passepartout_mm=request.passepartout_mm,
                duplex_back_side=True,  # Back side: positioned on right for duplex alignment
                request_id=f"{request_id}_back"
            )
            back_layout_size_mb = len(back_layout_bytes) / 1024 / 1024
            
            # Save back layout to local file
            back_layout_file = f"{filename_prefix}_back.tiff"
            with open(back_layout_file, "wb") as f:
                f.write(back_layout_bytes)
            
            log(f"Back A4 layout created: {back_layout_size_mb:.1f}MB, saved as {back_layout_file}", request_id=request_id)
        
        # Return success with file sizes and file paths
        duplex_info = " (duplex-ready)" if request.duplex_mode else ""
        return A4LayoutResponse(
            success=True,
            message=f"A4 layouts created successfully for {cards_processed} cards in {request.orientation} orientation{duplex_info}",
            front_layout_size_mb=front_layout_size_mb,
            back_layout_size_mb=back_layout_size_mb,
            front_layout_file=front_layout_file,
            back_layout_file=back_layout_file,
            cards_processed=cards_processed,
            cards_found=cards_found
        )
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        error(f"Error creating A4 layouts: {str(e)}", request_id=request_id)
        raise HTTPException(status_code=500, detail=f"An error occurred while creating A4 layouts: {str(e)}")

@router.post("/create-a4-layouts-files")
async def create_a4_layouts_files(request: CreateA4LayoutRequest):
    """
    Create A4 layouts and return the actual TIFF files as response.
    
    This endpoint returns the binary TIFF files directly.
    """
    if not supabase_client:
        raise HTTPException(status_code=503, detail="Database service unavailable.")
    
    extended_ids = request.extended_ids
    if not extended_ids:
        raise HTTPException(status_code=400, detail="No extended IDs provided.")
    
    if len(extended_ids) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 cards allowed per A4 layout.")
    
    request_id = f"a4_files_{hash(''.join(extended_ids)) % 10000:04d}"
    log(f"Creating A4 layout files for {len(extended_ids)} cards", request_id=request_id)
    
    # This endpoint would need to be implemented to return actual files
    # For now, return a placeholder response
    raise HTTPException(status_code=501, detail="File download endpoint not yet implemented. Use /create-a4-layouts for now.") 