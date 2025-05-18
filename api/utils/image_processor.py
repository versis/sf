"""
Utilities for processing and preparing images for AI processing.
"""
import base64
import io
from typing import Optional, Tuple
from PIL import Image

from api.utils.logger import log, debug

# Constants
IMAGE_SIZE = (512, 512)
JPG_QUALITY = 90

class ImageProcessor:
    @staticmethod
    def decode_image_data_url(image_data_url: str, request_id: Optional[str] = None) -> Tuple[str, bytes]:
        """
        Decodes a data URL into format and binary data.
        
        Parameters:
        -----------
        image_data_url : str
            The original image as a data URL (base64 encoded)
        request_id : str, optional
            A unique identifier for logging and tracking the request
            
        Returns:
        --------
        Tuple[str, bytes]
            A tuple containing (format, binary_data)
            
        Raises:
        -------
        ValueError:
            If the image data URL is invalid or cannot be decoded
        """
        debug(f"Decoding image data URL", request_id=request_id)
        
        # Validate image data URL
        if ';base64,' not in image_data_url:
            log(f"Invalid image data URL format - missing base64 delimiter.", level="ERROR", request_id=request_id)
            raise ValueError("Invalid image data URL format")
        
        try:
            header, encoded = image_data_url.split(';base64,', 1)
            debug(f"Image format from header: {header}", request_id=request_id)
            
            image_data = base64.b64decode(encoded)
            debug(f"Successfully decoded base64 data, size: {len(image_data) / 1024:.2f} KB", request_id=request_id)
            
            return header, image_data
        except Exception as e:
            log(f"Error decoding image data URL: {str(e)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Failed to process image data URL: {str(e)}")

    @staticmethod
    def create_square_image(img: Image.Image, request_id: Optional[str] = None) -> Image.Image:
        """
        Creates a square image by center cropping.
        
        Parameters:
        -----------
        img : Image.Image
            The original PIL Image object
        request_id : str, optional
            A unique identifier for logging and tracking the request
            
        Returns:
        --------
        Image.Image
            A square PIL Image object
            
        Raises:
        -------
        ValueError:
            If the image cannot be cropped
        """
        try:
            debug(f"Converting image to perfect square", request_id=request_id)
            
            # Get dimensions
            width, height = img.size
            
            # Take the smaller dimension
            size = min(width, height)
            
            # Calculate crop box (centered)
            left = (width - size) // 2
            top = (height - size) // 2
            right = left + size
            bottom = top + size
            
            # Crop to square
            square_img = img.crop((left, top, right, bottom))
            
            debug(f"Cropped to square: {square_img.size}", request_id=request_id)
            return square_img
        except Exception as e:
            log(f"Error cropping image to square: {str(e)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Failed to crop image to square: {str(e)}")

    @staticmethod
    def ensure_rgb_mode(img: Image.Image, request_id: Optional[str] = None) -> Image.Image:
        """
        Ensures the image is in RGB mode.
        
        Parameters:
        -----------
        img : Image.Image
            The original PIL Image object
        request_id : str, optional
            A unique identifier for logging and tracking the request
            
        Returns:
        --------
        Image.Image
            A PIL Image object in RGB mode
            
        Raises:
        -------
        ValueError:
            If the image cannot be converted to RGB
        """
        try:
            debug(f"Converting image to RGB if needed", request_id=request_id)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                rgb_img = img.convert('RGB')
                debug(f"Converted image to RGB mode", request_id=request_id)
                return rgb_img
            return img
        except Exception as e:
            log(f"Error converting image to RGB: {str(e)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Failed to convert image to RGB: {str(e)}")

def resize_and_convert_image_for_openai(image_data_url: str, request_id: Optional[str] = None) -> str:
    """
    Resizes and converts an image data URL to 512x512 JPG format for optimal use with OpenAI API.
    
    Parameters:
    -----------
    image_data_url : str
        The original image as a data URL (base64 encoded)
    request_id : str, optional
        A unique identifier for logging and tracking the request
        
    Returns:
    --------
    str
        A new data URL containing the resized and converted image
        
    Raises:
    -------
    ValueError:
        If the image cannot be processed
    """
    try:
        log(f"Starting image resize and conversion for OpenAI API", request_id=request_id)
        
        # Decode the data URL
        _, image_data = ImageProcessor.decode_image_data_url(image_data_url, request_id)
        
        # Open the image
        try:
            img_buffer = io.BytesIO(image_data)
            img = Image.open(img_buffer)
            debug(f"Successfully opened image. Format: {img.format}, Mode: {img.mode}, Size: {img.size}", request_id=request_id)
        except Exception as e:
            log(f"Error opening image data: {str(e)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Failed to open image data: {str(e)}")
        
        # Create a perfect square image
        img = ImageProcessor.create_square_image(img, request_id)
        
        # Ensure RGB mode
        img = ImageProcessor.ensure_rgb_mode(img, request_id)
        
        # Resize to target size
        try:
            debug(f"Resizing image from {img.size} to {IMAGE_SIZE} for OpenAI", request_id=request_id)
            img = img.resize(IMAGE_SIZE, Image.Resampling.LANCZOS)
            debug(f"Successfully resized image to {img.size}", request_id=request_id)
        except Exception as e:
            log(f"Error resizing image: {str(e)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Failed to resize image: {str(e)}")
        
        # Save as JPG to buffer
        try:
            output_buffer = io.BytesIO()
            img.save(output_buffer, format="JPEG", quality=JPG_QUALITY)
            output_buffer.seek(0)
            debug(f"Successfully saved image as JPEG", request_id=request_id)
        except Exception as e:
            log(f"Error saving image as JPEG: {str(e)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Failed to save image as JPEG: {str(e)}")
        
        # Encode as base64
        try:
            jpg_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
            debug(f"Successfully encoded image as base64, length: {len(jpg_base64) // 1024} KB", request_id=request_id)
        except Exception as e:
            log(f"Error encoding image to base64: {str(e)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Failed to encode image as base64: {str(e)}")
        
        # Create new data URL
        resized_data_url = f"data:image/jpeg;base64,{jpg_base64}"
        
        # Calculate size reduction
        original_size = len(image_data_url) / 1024
        new_size = len(resized_data_url) / 1024
        log(f"Image resized for OpenAI API: {original_size:.2f}KB -> {new_size:.2f}KB", request_id=request_id)
        
        return resized_data_url
        
    except Exception as e:
        log(f"Unexpected error resizing image for OpenAI: {str(e)}", level="ERROR", request_id=request_id)
        # Re-raise with clear message
        raise ValueError(f"Failed to resize image for OpenAI: {str(e)}") 