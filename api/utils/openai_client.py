"""
OpenAI client initialization and configuration.
"""
import os
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv

# Load environment variables only once at module level
load_dotenv(".env.local")

# Constants
OVERALL_TIMEOUT = 59.0  # Slightly less than Vercel's 60s Hobby limit

# Client for Azure OpenAI - initialize once at module level
azure_client = AsyncAzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
) 