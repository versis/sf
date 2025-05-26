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
    A surprising and memorable name for the color (max 3 words, ALL CAPS)
    phoneticName : str
    Phonetic pronunciation (IPA symbols) for the color name
    article : str
    The part of speech for the color name (e.g., noun, adjective)
    description : str
    A moment, observation, or fortune-cookie-style message (25-33 words)
    that captures the unexpected story of this color+image combination
    """
    colorName: str = Field(
        description="A surprising and memorable name for the color (max 3 words, ALL CAPS). Should feel unexpected but perfect."
    )
    phoneticName: str = Field(
        description="Phonetic pronunciation (IPA symbols) for your creative colorName"
    )
    article: str = Field(
        description="The part of speech for the colorName (e.g., noun, adjective). Do not use the word `phrase`. It's just `noun`, and not `noun phrase`."
    )
    description: str = Field(
        description="Two short lines separated by ' — ': First line is an unexpected observation (10-15 words), second line is a different angle or twist (10-15 words). Make it surprisingly specific."
    )