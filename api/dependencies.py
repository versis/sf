import os
from fastapi import Header, HTTPException, status
from .config import INTERNAL_API_KEY, DEV_MODE_SKIP_API_KEY_CHECK
from .utils.logger import log, error

# DEV_MODE_SKIP_API_KEY_CHECK is now imported from config.py
# # A new environment variable to allow skipping API key check in dev mode
# DEV_MODE_SKIP_API_KEY_CHECK = os.environ.get("DEV_MODE_SKIP_API_KEY_CHECK", "False").lower() == "true"

async def verify_api_key(x_internal_api_key: str = Header(None)):
    """Dependency to verify the internal API key."""
    if DEV_MODE_SKIP_API_KEY_CHECK:
        log("DEV_MODE_SKIP_API_KEY_CHECK is True, skipping API key verification.")
        return

    if not INTERNAL_API_KEY:
        error("Internal API Key is not configured on the server.")
        # This is a server-side configuration issue, so we deny access.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured."
        )

    if not x_internal_api_key:
        error("X-Internal-API-Key header is missing.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing Internal API Key"
        )

    if x_internal_api_key != INTERNAL_API_KEY:
        error(f"Invalid API Key received: {x_internal_api_key[:5]}...") # Log only a prefix for security
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid Internal API Key"
        )
    log("Internal API Key verified successfully.") 