"""
Pydantic models for API response data.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class CardImageResponseItem(BaseModel):
    """
    Model for a single card image item in the response.
    
    Attributes:
    -----------
    orientation : str
        The orientation of the card image.
    image_base64 : str
        The base64-encoded image data.
    filename : str
        The filename of the generated card image.
    extendedId : str
        The unique identifier for the card.
    """
    orientation: str
    image_base64: str
    filename: str
    extendedId: str

class GenerateCardsResponse(BaseModel):
    """
    Response model for the card generation API.
    
    Attributes:
    -----------
    request_id : str
        A unique identifier for the request.
    ai_details_used : Dict[str, Any]
        Details from the AI that were used to generate the cards.
    generated_cards : List[CardImageResponseItem]
        A list of generated card images.
    error : Optional[str]
        An optional error message.
    """
    request_id: str
    ai_details_used: Dict[str, Any]
    generated_cards: List[CardImageResponseItem]
    error: Optional[str] = None 