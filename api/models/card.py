"""
Pydantic models for card data structures.
"""
from pydantic import BaseModel, Field

class ColorCardDetails(BaseModel):
    """
    The structure of the response expected from Azure OpenAI.
    
    Attributes:
    -----------
    colorName : str
        A unique and meaningful name for the color (max 3 words, ALL CAPS)
    phoneticName : str
        Phonetic pronunciation (IPA symbols) for the color name
    article : str
        The part of speech for the color name (e.g., noun, adjective)
    description : str
        A personal description (max 30-40 words) that captures this specific
        color-image combination without generic openers
    """
    colorName: str = Field(
        description="A unique and meaningful name for the color (max 3 words, ALL CAPS)"
    )
    phoneticName: str = Field(
        description="Phonetic pronunciation (IPA symbols) for your creative colorName"
    )
    article: str = Field(
        description="The part of speech for the colorName (e.g., noun, adjective). Do not use the word `phrase`. It's just `noun`, and not `noun phrase`."
    )
    description: str = Field(
        description="A personal description (25-33 words) starting with concrete imagery or a moment, never with 'This color' or similar. Captures the unique intersection of this specific color and image."
    )