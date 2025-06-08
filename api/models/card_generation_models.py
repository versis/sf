from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class CardGenerationCreateRequest(BaseModel):
    """Request model to initiate card generation."""
    hex_color: str = Field(..., description="The hex color for the card (e.g., '#RRGGBB').")

class CardGenerationUpdateRequest(BaseModel):
    """Request model to update an existing card generation record."""
    status: Optional[str] = Field(None, description="New status of the card generation process.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="JSON metadata associated with the card.")
    image_url: Optional[str] = Field(None, description="URL of the generated and stored card image.")
    ai_prompt: Optional[str] = Field(None, description="The prompt used for AI generation, if applicable.")
    ai_response: Optional[Dict[str, Any]] = Field(None, description="The raw response from AI, if applicable.")
    error_message: Optional[str] = Field(None, description="Error message if generation failed.")

class CardGenerationRecord(BaseModel):
    """Response model representing a card generation record from the database."""
    id: int = Field(..., description="Unique database identifier.")
    extended_id: Optional[str] = Field(None, description="User-facing formatted ID (e.g., '0000001 FE F').")
    hex_color: str = Field(..., description="The hex color of the card.")
    status: str = Field(..., description="Current status of the card generation process.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="JSON metadata for the card.")
    front_horizontal_image_url: Optional[str] = Field(None, description="URL of the generated front horizontal card image (PNG).")
    front_vertical_image_url: Optional[str] = Field(None, description="URL of the generated front vertical card image (PNG).")
    front_horizontal_tiff_url: Optional[str] = Field(None, description="URL of the high-resolution front horizontal card TIFF (300 DPI, print-ready).")
    front_vertical_tiff_url: Optional[str] = Field(None, description="URL of the high-resolution front vertical card TIFF (300 DPI, print-ready).")
    note_text: Optional[str] = Field(None, description="User's note for the back of the card.")
    has_note: bool = Field(False, description="Flag indicating if a note is present.")
    back_horizontal_image_url: Optional[str] = Field(None, description="URL of the generated back horizontal card image (PNG).")
    back_vertical_image_url: Optional[str] = Field(None, description="URL of the generated back vertical card image (PNG).")
    back_horizontal_tiff_url: Optional[str] = Field(None, description="URL of the high-resolution back horizontal card TIFF (300 DPI, print-ready).")
    back_vertical_tiff_url: Optional[str] = Field(None, description="URL of the high-resolution back vertical card TIFF (300 DPI, print-ready).")
    created_at: Optional[Any] = Field(None, description="Timestamp of creation.") # Supabase provides this
    updated_at: Optional[Any] = Field(None, description="Timestamp of last update.") # Supabase provides this

    class Config:
        # Pydantic V2 uses from_attributes instead of orm_mode
        from_attributes = True

class InitiateCardGenerationResponse(BaseModel):
    """Response model for the initiate card generation endpoint."""
    message: str = "Card generation initiated successfully."
    db_id: int
    extended_id: str
    current_status: str 