"""
Pydantic models for structured outputs from OpenAI API.
"""
from pydantic import BaseModel, Field

class ColorCardDetails(BaseModel):
    """
    The structure of the response expected from Azure OpenAI.
    
    Attributes:
    -----------
    colorName : str
        A creative and evocative name for the color (max 3 words, ALL CAPS)
    phoneticName : str
        Phonetic pronunciation (IPA symbols) for the color name
    article : str
        The part of speech for the color name (e.g., noun, adjective phrase)
    description : str
        A poetic description (max 25-30 words) of the color's feeling/mood
    """
    colorName: str = Field(
        description="A creative and evocative name for the color (max 3 words, ALL CAPS)"
    )
    phoneticName: str = Field(
        description="Phonetic pronunciation (IPA symbols) for your creative colorName"
    )
    article: str = Field(
        description="The part of speech for the colorName (e.g., noun, adjective phrase)"
    )
    description: str = Field(
        description="A poetic description (max 25-30 words) that evokes the feeling/mood of this color, inspired by the image"
    ) 