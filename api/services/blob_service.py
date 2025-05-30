import traceback
from typing import Dict, List, Union, Optional
from vercel_blob import put as vercel_blob_put # Removed unused delete import
from ..utils.logger import log, error

class BlobService:
    """Service class for handling interactions with Vercel Blob storage."""
    
    def __init__(self, token: str):
        """Initialize the BlobService with a Vercel Blob token."""
        # The BlobClient from vercel_blob might not be necessary if using functions directly
        # For now, let's keep it simple and use the put/del_by_url functions directly if token is for them.
        # If BlobClient is indeed needed for other operations, ensure its usage aligns with the library.
        # self.client = BlobClient({"token": token}) # Assuming token is directly for put/del_by_url
        self.token = token # Store token if needed by functions, or if client is used.
        log("BlobService initialized")
    
    def upload_image(
        self, 
        image_data: bytes, 
        filename: str,
        content_type: str = "image/png"
    ) -> Dict[str, str]:
        """
        Upload an image to Vercel Blob storage.
        
        Args:
            image_data: The binary image data to upload
            filename: The name to use for the file in storage
            content_type: The MIME type of the image (default: image/png)
        
        Returns:
            Dict containing the uploaded blob information
        """
        try:
            log(f"Attempting to upload image: {filename} (Content-Type: {content_type})")
            # Removed await, vercel_blob_put is synchronous
            blob = vercel_blob_put(
                filename, 
                image_data,
                options={'token': self.token, 'access': 'public', 'contentType': content_type}
            )
            log(f"Successfully uploaded image. URL: {blob['url']}")
            return {
                "url": blob['url'],
                "pathname": blob['pathname'],
                "size": blob.get('size', 0),
                "contentType": blob.get('contentType', content_type),
                "uploadedAt": str(blob.get('uploadedAt'))
            }
        except Exception as e:
            error_detail = f"Failed to upload image {filename} to Vercel Blob: {str(e)}"
            error(error_detail)
            error(traceback.format_exc())
            raise Exception(error_detail)
    
    def upload_multiple_images(
        self,
        images: List[Dict[str, Union[bytes, str, Dict]]],
        use_parallel: bool = True
    ) -> Dict[str, Dict[str, str]]:
        """
        Upload multiple images to Vercel Blob storage.
        
        Args:
            images: List of dictionaries with image data and metadata
                   Each dict should have: 
                   - 'data': bytes - The binary image data
                   - 'filename': str - The filename to use
                   - 'content_type': str - Optional MIME type (default: image/png)
                   - 'orientation': str - Optional orientation identifier (e.g., 'horizontal', 'vertical')
            use_parallel: Whether to upload images in parallel (default: True for performance)
        
        Returns:
            Dict mapping orientation keys to image URLs and metadata
        """
        try:
            upload_method = "in parallel" if use_parallel else "sequentially"
            log(f"Attempting to upload {len(images)} images to Vercel Blob {upload_method}")
            
            if use_parallel:
                return self._upload_images_parallel(images)
            else:
                return self._upload_images_sequential(images)
                
        except Exception as e:
            error_detail = f"Failed to upload multiple images: {str(e)}"
            error(error_detail)
            error(traceback.format_exc())
            raise Exception(error_detail)
    
    def _upload_images_sequential(self, images: List[Dict[str, Union[bytes, str, Dict]]]) -> Dict[str, Dict[str, str]]:
        """Upload images one by one (original method)."""
        results_by_orientation = {}
        
        for image_info in images:
            data = image_info.get('data')
            filename = image_info.get('filename')
            content_type = image_info.get('content_type', 'image/png')
            orientation = image_info.get('orientation', 'default')
            
            if not data or not filename:
                error(f"Missing required data or filename for an image in batch upload. Orientation: {orientation}. Skipping.")
                continue
            
            try:
                upload_result = self.upload_image(data, filename, content_type)
                results_by_orientation[orientation] = upload_result
                log(f"Successfully uploaded image for orientation '{orientation}': {upload_result['url']}")
            except Exception as upload_err:
                error(f"Failed to upload image for orientation '{orientation}' (filename: {filename}): {str(upload_err)}")
        
        if not results_by_orientation and images: 
            raise Exception("Failed to upload any images from the batch.")
            
        log(f"Successfully processed sequential batch upload. {len(results_by_orientation)} images uploaded.")
        return results_by_orientation
    
    def _upload_images_parallel(self, images: List[Dict[str, Union[bytes, str, Dict]]]) -> Dict[str, Dict[str, str]]:
        """Upload images in parallel using ThreadPoolExecutor."""
        import concurrent.futures
        import threading
        
        results_by_orientation = {}
        results_lock = threading.Lock()
        
        def upload_single_image(image_info):
            """Upload a single image and return the result."""
            data = image_info.get('data')
            filename = image_info.get('filename')
            content_type = image_info.get('content_type', 'image/png')
            orientation = image_info.get('orientation', 'default')
            
            if not data or not filename:
                error(f"Missing required data or filename for an image in parallel upload. Orientation: {orientation}.")
                return None, orientation, "Missing data or filename"
            
            try:
                upload_result = self.upload_image(data, filename, content_type)
                log(f"Successfully uploaded image for orientation '{orientation}': {upload_result['url']}")
                return upload_result, orientation, None
            except Exception as upload_err:
                error_msg = f"Failed to upload image for orientation '{orientation}' (filename: {filename}): {str(upload_err)}"
                error(error_msg)
                return None, orientation, error_msg
        
        # Use ThreadPoolExecutor for parallel uploads
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all upload tasks
            future_to_image = {executor.submit(upload_single_image, img): img for img in images}
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_image):
                upload_result, orientation, error_msg = future.result()
                
                if upload_result is not None:
                    with results_lock:
                        results_by_orientation[orientation] = upload_result
                else:
                    error(f"Parallel upload failed for orientation '{orientation}': {error_msg}")
        
        if not results_by_orientation and images:
            raise Exception("Failed to upload any images from the parallel batch.")
            
        log(f"Successfully processed parallel batch upload. {len(results_by_orientation)} images uploaded.")
        return results_by_orientation

    # _upload_single_image_with_orientation was removed previously.
    
    # Unused delete_image method removed for cleanup.
    # def delete_image(self, url: str) -> bool:
    #     try:
    #         log(f"Attempting to delete image from Vercel Blob at URL: {url}")
    #         vercel_blob_delete([url], options={'token': self.token})
    #         log(f"Successfully deleted image at URL: {url}")
    #         return True
    #     except Exception as e:
    #         error_detail = f"Failed to delete image at URL {url} from Vercel Blob: {str(e)}"
    #         error(error_detail)
    #         error(traceback.format_exc())
    #         return False 