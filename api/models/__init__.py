"""
Models package for the API.
Provides type definitions and Pydantic models for API requests, responses, and internal data structures.
"""
from api.models.card import ColorCardDetails
# Import new models if they are intended for package-level export
from .card_generation_models import (
    CardGenerationCreateRequest, 
    CardGenerationRecord, 
    InitiateCardGenerationResponse,
    CardGenerationUpdateRequest
)

__all__ = [
    'ColorCardDetails',
    'CardGenerationCreateRequest',
    'CardGenerationRecord',
    'InitiateCardGenerationResponse',
    'CardGenerationUpdateRequest'
]

# This file makes Python treat the directory api/models as a package. 