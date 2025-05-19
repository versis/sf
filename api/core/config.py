import os
from dotenv import load_dotenv

# Load .env.local first, then .env
# This allows .env.local to override .env for local development specifics
load_dotenv(".env.local") 
load_dotenv() 

# General Configuration
APP_NAME = "shadefreude API"
API_PREFIX = "/api"

# Card Generation Specifics
CARD_ID_SUFFIX = os.environ.get("CARD_ID_SUFFIX", "FE T")
DB_ID_PADDING_LENGTH = 9  # e.g., to format 1 as "000000001"
DEFAULT_STATUS_PENDING = "pending_details"
DEFAULT_STATUS_PROCESSING = "processing_image"
DEFAULT_STATUS_COMPLETED = "completed"
DEFAULT_STATUS_FAILED = "failed"


# Supabase Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
ENABLE_AI_CARD_DETAILS = os.environ.get("ENABLE_AI_CARD_DETAILS", "true").lower() == "true"

# Vercel Blob Storage Configuration
BLOB_READ_WRITE_TOKEN = os.environ.get("BLOB_READ_WRITE_TOKEN")

# Internal API Key for securing certain endpoints
INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY")

# Logging Configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# CORS Origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://sf.tinker.institute",
    "https://sf-livid.vercel.app",
    # Add any other origins as needed
]

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("WARNING: Supabase URL or Service Key is not set in environment variables.")

if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
    print("WARNING: Azure OpenAI API Key or Endpoint is not set in environment variables.")

if not BLOB_READ_WRITE_TOKEN:
    print("WARNING: Vercel Blob Read/Write Token is not set in environment variables.")

if not INTERNAL_API_KEY:
    print("WARNING: Internal API Key is not set. Secure endpoints will not be protected.") 