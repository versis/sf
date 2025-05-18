from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class GenerateCardsRequest(BaseModel):
    croppedImageDataUrl: str
    hexColor: str
    # Only for manual API calls if needed
    cardId: Optional[str] = "0000023 FE T"

class CardImageResponseItem(BaseModel):
    orientation: str
    image_base64: str
    filename: str

class GenerateCardsResponse(BaseModel):
    request_id: str
    ai_details_used: Dict[str, Any]
    generated_cards: List[CardImageResponseItem]
    error: Optional[str] = None

class CardDetailsRequest(BaseModel):
    hexColor: str 