# api/services/blob_service.py
import asyncio
# Removed specific BlobError import as it causes ImportError
from vercel_blob import put as vercel_blob_put 
from api.utils.logger import log, error # Assuming your logger has an error function too
import traceback

async def upload_image_to_blob(pathname: str, body: bytes) -> str:
    """Uploads image bytes to Vercel Blob and returns the URL."""
    try:
        # vercel_blob_put is synchronous, run in a thread to avoid blocking asyncio event loop
        log(f"Attempting to upload to Vercel Blob: {pathname}")
        blob_response = await asyncio.to_thread(
            vercel_blob_put,
            pathname=pathname,
            body=body,
            options={
                'access': 'public', 
                'add_random_suffix': 'false' # We construct the full unique pathname
            }
        )
        log(f"Vercel Blob raw response for {pathname}: {blob_response}")

        if not blob_response or not isinstance(blob_response, dict) or 'url' not in blob_response:
            error_msg = f"Vercel Blob upload failed or did not return a valid URL/response structure for {pathname}. Response: {blob_response}"
            error(error_msg)
            # For a more specific error to the client, you might raise a custom exception here
            # that the router can convert to an HTTPException, or directly raise HTTPException if this service
            # is tightly coupled with FastAPI (which it is in this structure).
            raise Exception("Blob upload did not return a valid URL or response.") # Generic exception
        
        log(f"Successfully uploaded {pathname} to Vercel Blob. URL: {blob_response['url']}")
        return blob_response['url']
    # It's good to catch more specific exceptions if known, e.g., from httpx if vercel_blob uses it and lets them propagate
    # from httpx import HTTPStatusError
    # except HTTPStatusError as http_err:
    #     error_msg = f"Vercel Blob upload HTTP error for {pathname}: {http_err.response.status_code} - {http_err.response.text}"
    #     error(error_msg)
    #     raise Exception(f"Image storage HTTP error: {http_err.response.status_code}")
    except Exception as e:
        # This will catch any exception from vercel_blob_put or our checks above
        error_msg = f"Unexpected error during Vercel Blob upload for {pathname}: {type(e).__name__} - {str(e)}"
        error(error_msg)
        error(f"Traceback for {pathname} upload error: {traceback.format_exc()}") # Make sure traceback is imported where this log is actually called
        raise Exception(f"Image storage encountered an unexpected error: {str(e)}") 