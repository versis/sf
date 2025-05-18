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
    # Only for manual API calls if needed
    cardId: Optional[str] = "0000023 FE T" 