"""
OpenAI client initialization and configuration.
"""
# import os # No longer needed directly for environ access here
from openai import AsyncAzureOpenAI
# from dotenv import load_dotenv # Removed, handled in api.core.config

# Import necessary configurations
from ..config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_CLIENT_TIMEOUT,
)

# Client for Azure OpenAI - initialize once at module level
azure_client = AsyncAzureOpenAI(
    # api_key=os.environ.get("AZURE_OPENAI_API_KEY"), # Old way
    # api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"), # Old way
    # azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"), # Old way
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION, # Default is handled in config.py if env var not set
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    timeout=AZURE_OPENAI_CLIENT_TIMEOUT, # Use the imported config
) 