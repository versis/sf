"""
Pydantic models for API request data.
"""
from typing import Optional
from pydantic import BaseModel

class GenerateCardsRequest(BaseModel):
    """
    Request model for generating cards.
    
    Attributes:
    -----------
    croppedImageDataUrl : str
        The data URL of the cropped image.
    hexColor : str
        The hexadecimal color value.
    cardId : Optional[str]
        Optional card ID for manual API calls.
    """
    croppedImageDataUrl: str
    hexColor: str
    # Optional: The backend will now generate the definitive ID.
    # This field might be removed later if frontend never sends it.
    cardId: Optional[str] = None 