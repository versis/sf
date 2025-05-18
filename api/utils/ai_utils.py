import os
import json
import time
import base64
import io
import asyncio
import sys
import traceback
from typing import Dict, Any, Optional, Tuple
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv
from PIL import Image

from api.utils.logger import log

# Load environment variables only once at module level
load_dotenv(".env.local")

# Constants
IMAGE_SIZE = (512, 512)
OVERALL_TIMEOUT = 59.0  # Slightly less than Vercel's 60s Hobby limit
JPG_QUALITY = 90

# Client for Azure OpenAI - initialize once at module level
azure_client = AsyncAzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

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
        log(f"Decoding image data URL", request_id=request_id)
        
        # Validate image data URL
        if ';base64,' not in image_data_url:
            log(f"Invalid image data URL format - missing base64 delimiter.", request_id=request_id)
            raise ValueError("Invalid image data URL format")
        
        try:
            header, encoded = image_data_url.split(';base64,', 1)
            log(f"Image format from header: {header}", request_id=request_id)
            
            image_data = base64.b64decode(encoded)
            log(f"Successfully decoded base64 data, size: {len(image_data) / 1024:.2f} KB", request_id=request_id)
            
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
            log(f"Converting image to perfect square", request_id=request_id)
            
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
            
            log(f"Cropped to square: {square_img.size}", request_id=request_id)
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
            log(f"Converting image to RGB if needed", request_id=request_id)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                rgb_img = img.convert('RGB')
                log(f"Converted image to RGB mode", request_id=request_id)
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
            log(f"Successfully opened image. Format: {img.format}, Mode: {img.mode}, Size: {img.size}", request_id=request_id)
        except Exception as e:
            log(f"Error opening image data: {str(e)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Failed to open image data: {str(e)}")
        
        # Create a perfect square image
        img = ImageProcessor.create_square_image(img, request_id)
        
        # Ensure RGB mode
        img = ImageProcessor.ensure_rgb_mode(img, request_id)
        
        # Resize to target size
        try:
            log(f"Resizing image from {img.size} to {IMAGE_SIZE} for OpenAI", request_id=request_id)
            img = img.resize(IMAGE_SIZE, Image.Resampling.LANCZOS)
            log(f"Successfully resized image to {img.size}", request_id=request_id)
        except Exception as e:
            log(f"Error resizing image: {str(e)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Failed to resize image: {str(e)}")
        
        # Save as JPG to buffer
        try:
            output_buffer = io.BytesIO()
            img.save(output_buffer, format="JPEG", quality=JPG_QUALITY)
            output_buffer.seek(0)
            log(f"Successfully saved image as JPEG", request_id=request_id)
        except Exception as e:
            log(f"Error saving image as JPEG: {str(e)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Failed to save image as JPEG: {str(e)}")
        
        # Encode as base64
        try:
            jpg_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
            log(f"Successfully encoded image as base64, length: {len(jpg_base64) // 1024} KB", request_id=request_id)
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

class OpenAIPromptBuilder:
    @staticmethod
    def build_messages(hex_color: str, image_data_url: str) -> list:
        """
        Builds the message array for OpenAI API with system and user messages.
        
        Parameters:
        -----------
        hex_color : str
            The hex color code to use in the prompt
        image_data_url : str
            The image data URL to include in the prompt
            
        Returns:
        --------
        list
            A list of message objects for the OpenAI API
        """
        system_message = {
            "role": "system",
            "content": "You are a creative assistant. For the given hex color and image, generate poetic and evocative card details."
        }
        
        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Generate details for a color card with hex value '{hex_color}'. I need these fields:\n"
                        f"1. colorName: A creative and evocative name for the color (max 3 words, ALL CAPS), inspired by both the hex color and the image.\n"
                        f"2. phoneticName: Phonetic pronunciation (IPA symbols) for your creative colorName.\n"
                        f"3. article: The part of speech for the colorName (e.g., noun, adjective phrase).\n"
                        f"4. description: A poetic description (max 25-30 words) that evokes the feeling/mood of the image, describe the main chaacter. Explain what is the person wearing."
                        f"Format your response strictly as a JSON object with these exact keys: colorName, phoneticName, article, description."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_url,
                        "detail": "low"
                    }
                }
            ]
        }
        
        return [system_message, user_message]

class OpenAIResponseFormatter:
    @staticmethod
    def format_response(response_data: Dict[str, Any], hex_color: str) -> Dict[str, Any]:
        """
        Formats the OpenAI API response into the desired format.
        
        Parameters:
        -----------
        response_data : Dict[str, Any]
            The parsed JSON response from OpenAI
        hex_color : str
            The original hex color for fallback
            
        Returns:
        --------
        Dict[str, Any]
            A formatted dictionary with the card details
        """
        # Get default color name from hex if needed for fallbacks
        hex_clean = hex_color.lstrip('#').upper()
        default_color_name = f"HEX {hex_clean[:3]}"
        
        phonetic_raw = str(response_data.get("phoneticName", "")).strip()
        if phonetic_raw.startswith('[') and phonetic_raw.endswith(']'):
            phonetic_final = phonetic_raw
        else:
            phonetic_final = f"[{phonetic_raw.strip('[]')}]"
        
        article_raw = str(response_data.get("article", "noun")).strip()
        if article_raw.startswith('[') and article_raw.endswith(']'):
            article_final = article_raw
        else:
            article_final = f"[{article_raw.strip('[]')}]"
        
        return {
            "colorName": str(response_data.get("colorName", default_color_name.upper())).strip().upper(),
            "phoneticName": phonetic_final,
            "article": article_final,
            "description": str(response_data.get("description", f"A color with hex value {hex_color}.")).strip()
        }

async def generate_ai_card_details(hex_color: str, cropped_image_data_url: str = None, request_id: str = None) -> Dict[str, Any]:
    """
    Generates AI-based card details using Azure OpenAI.
    
    This function sends a prompt to Azure OpenAI to generate creative and poetic card details
    based on the provided hex color value and (optionally) the user's cropped image.
    When an image is provided, the AI will analyze both the color and image content to create
    more contextually relevant and thematically appropriate card details.
    
    Parameters:
    -----------
    hex_color : str
        The hex color code to use as inspiration (e.g., "#FF5500")
    cropped_image_data_url : str, optional
        The cropped image as a data URL (base64 encoded) to be included in the AI prompt
    request_id : str, optional
        A unique identifier for logging and tracking the request
        
    Returns:
    --------
    Dict[str, Any]
        A dictionary containing the following keys:
        - colorName: A creative name for the color (max 3 words, ALL CAPS)
        - phoneticName: Phonetic pronunciation (IPA symbols) in brackets
        - article: The part of speech in brackets
        - description: A poetic description (25-30 words)
        
    Raises:
    -------
    ValueError:
        If the API response is empty/malformed or if the request times out
        If no image is provided (cropped_image_data_url is None or empty)
    Exception:
        For any other errors during API call or processing
    """
    log(f"Starting generate_ai_card_details for hex color: {hex_color}", request_id=request_id)
    
    # Validate image is provided
    if not cropped_image_data_url:
        log(f"Error: No cropped image provided for AI generation", level="ERROR", request_id=request_id)
        raise ValueError("A cropped image is required for AI card detail generation")
    
    # Validate the image data URL format
    if not cropped_image_data_url.startswith('data:image/'):
        log(f"Error: Invalid image data URL format: {cropped_image_data_url[:30]}...", level="ERROR", request_id=request_id)
        raise ValueError("Invalid image data URL format. Must start with 'data:image/'")
    
    if ';base64,' not in cropped_image_data_url:
        log(f"Error: Invalid image data URL format - missing base64 delimiter", level="ERROR", request_id=request_id)
        raise ValueError("Invalid image data URL format - missing base64 delimiter")
    
    log(f"Starting Azure OpenAI API call for hex color '{hex_color}' with image. Overall timeout {OVERALL_TIMEOUT}s.", request_id=request_id)
    api_call_start_time = time.time()

    try:
        # Resize and convert the image to 512x512 JPG for OpenAI
        try:
            log(f"Starting image optimization", request_id=request_id)
            optimized_image_data_url = resize_and_convert_image_for_openai(cropped_image_data_url, request_id)
            log(f"Image optimization complete", request_id=request_id)
        except ValueError as resize_error:
            log(f"Error resizing image for OpenAI API: {str(resize_error)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Image processing failed: {str(resize_error)}")
        
        # Prepare messages
        log(f"Building OpenAI API request with optimized 512x512 image", request_id=request_id)
        messages = OpenAIPromptBuilder.build_messages(hex_color, optimized_image_data_url)
        
        # Log request parameters
        log_request = {
            "model": os.environ.get("AZURE_OPENAI_DEPLOYMENT"),
            "message_count": len(messages),
            "image_included": True,
            "detail_level": "low"
        }
        log(f"Azure OpenAI API request parameters: {json.dumps(log_request)}", request_id=request_id)

        try:
            log(f"Sending request to Azure OpenAI API", request_id=request_id)
            
            # Ensure the Azure client is properly initialized
            if not azure_client:
                log(f"Azure OpenAI client is not initialized", level="ERROR", request_id=request_id)
                raise ValueError("Azure OpenAI client is not initialized")
            
            completion = await asyncio.wait_for(
                azure_client.chat.completions.create(
                    model=os.environ.get("AZURE_OPENAI_DEPLOYMENT"),
                    messages=messages,
                    response_format={"type": "json_object"}
                ),
                timeout=OVERALL_TIMEOUT
            )
            log(f"Successfully received response from Azure OpenAI API", request_id=request_id)
        except asyncio.TimeoutError:
            log(f"Azure OpenAI API call timed out via asyncio.wait_for after {OVERALL_TIMEOUT}s.", level="ERROR", request_id=request_id)
            raise ValueError(f"AI generation timed out after {OVERALL_TIMEOUT} seconds")
        except Exception as api_error:
            log(f"Error calling Azure OpenAI API: {str(api_error)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Error calling Azure OpenAI API: {str(api_error)}")
        
        api_call_duration = time.time() - api_call_start_time
        log(f"Azure OpenAI API call completed in {api_call_duration:.2f} seconds", request_id=request_id)

        if not completion.choices or not completion.choices[0].message or not completion.choices[0].message.content:
            log(f"Azure OpenAI response was empty or malformed.", level="ERROR", request_id=request_id)
            raise ValueError("Empty or malformed response from AI")

        response_text = completion.choices[0].message.content
        log(f"Raw response from OpenAI: {response_text}", request_id=request_id)
        
        try:
            response_data = json.loads(response_text)
            log(f"Parsed AI response: {json.dumps(response_data, indent=2)}", request_id=request_id)
        except json.JSONDecodeError as json_error:
            log(f"Failed to parse JSON response: {str(json_error)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Failed to parse AI response as JSON: {str(json_error)}")

        # Format the response
        final_details = OpenAIResponseFormatter.format_response(response_data, hex_color)
        log(f"Successfully formatted AI details: {json.dumps(final_details, indent=2)}", request_id=request_id)
        
        return final_details

    except asyncio.TimeoutError:
        log(f"Azure OpenAI API call timed out via asyncio.wait_for after {OVERALL_TIMEOUT}s.", level="ERROR", request_id=request_id)
        raise ValueError(f"AI generation timed out after {OVERALL_TIMEOUT} seconds")
        
    except Exception as e:
        log(f"Error during Azure OpenAI call or processing: {str(e)}", level="ERROR", request_id=request_id)
        raise 