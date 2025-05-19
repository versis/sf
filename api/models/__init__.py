"""
Models package for the API.
Provides type definitions and Pydantic models for API requests, responses, and internal data structures.
"""
from api.models.card import ColorCardDetails
from api.models.request import GenerateCardsRequest
from api.models.response import CardImageResponseItem, GenerateCardsResponse

__all__ = [
    'ColorCardDetails',
    'GenerateCardsRequest',
    'CardImageResponseItem',
    'GenerateCardsResponse'
]

# This file makes Python treat the directory api/models as a package. 