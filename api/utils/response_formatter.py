"""
Utilities for formatting AI responses into standardized formats.
"""
from typing import Dict, Any

from api.models.card import ColorCardDetails

class OpenAIResponseFormatter:
    @staticmethod
    def format_response(card_details: ColorCardDetails, hex_color: str) -> Dict[str, Any]:
        """
        Formats the OpenAI API response into the desired format.
        
        Parameters:
        -----------
        card_details : ColorCardDetails
            The structured output from OpenAI
        hex_color : str
            The original hex color for fallback
            
        Returns:
        --------
        Dict[str, Any]
            A formatted dictionary with the card details
        """
        # Get default color name from hex if needed for fallbacks
        hex_clean = hex_color.lstrip('#').upper()
        default_color_name = f"HEX {hex_clean[:3]}"
        
        # Process phonetic name
        phonetic_raw = str(card_details.phoneticName).strip()
        if phonetic_raw.startswith('[') and phonetic_raw.endswith(']'):
            phonetic_final = phonetic_raw
        else:
            phonetic_final = f"[{phonetic_raw.strip('[]')}]"
        
        # Process article
        article_raw = str(card_details.article).strip()
        if article_raw.startswith('[') and article_raw.endswith(']'):
            article_final = article_raw
        else:
            article_final = f"[{article_raw.strip('[]')}]"
        
        return {
            "colorName": str(card_details.colorName).strip().upper(),
            "phoneticName": phonetic_final,
            "article": article_final,
            "description": str(card_details.description).strip()
        } 