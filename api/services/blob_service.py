# api/services/blob_service.py
import asyncio
from vercel_blob import put as vercel_blob_put, BlobError as VercelBlobError
from api.utils.logger import log # Assuming your logger is named 'log'

async def upload_image_to_blob(pathname: str, body: bytes) -> str:
    """Uploads image bytes to Vercel Blob and returns the URL."""
    try:
        # vercel_blob_put is synchronous, run in a thread to avoid blocking asyncio event loop
        blob_response = await asyncio.to_thread(
            vercel_blob_put,
            pathname=pathname,
            body=body,
            options={
                'access': 'public', 
                'add_random_suffix': 'false' # We construct the full unique pathname
            }
        )
        if not blob_response or 'url' not in blob_response:
            log(f"Vercel Blob upload failed or did not return a URL for {pathname}. Response: {blob_response}", level="ERROR")
            raise VercelBlobError("Blob upload did not return a valid URL.")
        return blob_response['url']
    except VercelBlobError as e:
        log(f"Vercel Blob upload directly failed for {pathname}: {str(e)}", level="ERROR")
        raise # Re-raise the specific BlobError
    except Exception as e:
        log(f"Unexpected error during Vercel Blob upload for {pathname}: {str(e)}", level="ERROR")
        # Wrap unexpected errors in a standard exception or a custom one
        raise Exception(f"Image storage encountered an unexpected error: {str(e)}") 