# api/dependencies.py
from fastapi import Request, HTTPException, status
from api.core.config import INTERNAL_API_KEY, DEV_MODE_SKIP_API_KEY_CHECK
from api.utils.logger import warning

async def verify_api_key(request: Request):
    # If in dev mode and skip check is enabled, bypass the key check
    if DEV_MODE_SKIP_API_KEY_CHECK:
        warning("DEV_MODE_SKIP_API_KEY_CHECK is true. Skipping API key verification.")
        return

    # If INTERNAL_API_KEY is not configured on the server, deny access
    if not INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key not configured on server."
        )

    client_api_key = request.headers.get("X-Internal-API-Key")
    if not client_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing API Key (X-Internal-API-Key header)"
        )
    
    if client_api_key != INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid API Key"
        )
    return # Key is valid 