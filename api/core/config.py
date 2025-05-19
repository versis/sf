# api/core/config.py
import os

CARD_ID_SUFFIX: str = "FE F"

# Environment variables for Supabase (consider using Pydantic Settings for robust loading)
SUPABASE_URL: str | None = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY: str | None = os.environ.get("SUPABASE_SERVICE_KEY") # Service Role Key

# Environment variable for the internal API key
INTERNAL_API_KEY: str | None = os.environ.get("INTERNAL_API_KEY")

# Fallback for local development if INTERNAL_API_KEY is not set (for easier local testing without header)
# In production, ensure INTERNAL_API_KEY is set and this fallback is not hit, or remove it.
DEV_MODE_SKIP_API_KEY_CHECK: bool = os.environ.get("DEV_MODE_SKIP_API_KEY_CHECK", "False").lower() == "true"

# Blob Storage Token (for local SDK use primarily, Vercel injects it in deployment)
BLOB_READ_WRITE_TOKEN: str | None = os.environ.get("BLOB_READ_WRITE_TOKEN")

# AI Configuration
AZURE_OPENAI_API_VERSION: str | None = os.environ.get('AZURE_OPENAI_API_VERSION')
AZURE_OPENAI_DEPLOYMENT: str | None = os.environ.get('AZURE_OPENAI_DEPLOYMENT')
ENABLE_AI_CARD_DETAILS: bool = os.environ.get('ENABLE_AI_CARD_DETAILS', "true").lower() != "false"


# Basic check for essential Supabase config
if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("WARNING: Supabase URL or Service Key not found in environment variables. Supabase client might not initialize.")

if not INTERNAL_API_KEY and not DEV_MODE_SKIP_API_KEY_CHECK:
    print("WARNING: INTERNAL_API_KEY is not set. API calls might be rejected unless DEV_MODE_SKIP_API_KEY_CHECK is true.") 