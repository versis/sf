# api/models/card_generation_models.py
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any

class InitiateCardRequest(BaseModel):
    hex_color: str

class InitiateCardResponse(BaseModel):
    db_id: int
    extended_id: str

class FinalizeCardRequest(BaseModel):
    db_id: int
    # Using str for cropped_image_data_url as HttpUrl might be too strict for data URLs if not perfectly formatted.
    # Validation of data URL content/format can be done in the endpoint.
    cropped_image_data_url: str 
    hex_color: str
    # Optional: if AI details are generated on frontend and passed here. For now, assuming AI is done backend.
    # ai_generated_details: Dict[str, Any] | None = None 

class FinalizeCardResponse(BaseModel):
    message: str
    db_id: int
    extended_id: str
    image_url: str
    ai_details_used: Dict[str, Any] 