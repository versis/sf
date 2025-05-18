import os
import json
import time
import base64
import io
import asyncio
import sys
import traceback
from typing import Dict, Any
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv
from PIL import Image

from api.utils.logger import log

load_dotenv(".env.local")

# Client for Azure OpenAI
azure_client = AsyncAzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

def resize_and_convert_image_for_openai(image_data_url: str, request_id: str = None) -> str:
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
        # Direct console output for debugging
        print(f"[DEBUG] Starting image resize and conversion for OpenAI API")
        sys.stdout.flush()
        
        log(f"Starting image resize and conversion for OpenAI API", request_id=request_id)
        
        # Truncate image data for logging
        truncated_data_url = image_data_url[:30] + "..." if image_data_url else None
        
        # Validate image data URL
        if ';base64,' not in image_data_url:
            print(f"[ERROR] Invalid image data URL format - missing base64 delimiter.")
            sys.stdout.flush()
            log(f"Invalid image data URL format - missing base64 delimiter.", request_id=request_id)
            raise ValueError("Invalid image data URL format")
        
        # Decode the data URL
        try:
            print(f"[DEBUG] Splitting image data URL")
            sys.stdout.flush()
            header, encoded = image_data_url.split(';base64,', 1)
            print(f"[DEBUG] Image format from header: {header}")
            sys.stdout.flush()
            log(f"Image format from header: {header}", request_id=request_id)
        except Exception as e:
            print(f"[ERROR] Error splitting image data URL: {str(e)}")
            sys.stdout.flush()
            log(f"Error splitting image data URL: {str(e)}", request_id=request_id)
            raise ValueError(f"Failed to parse image data URL: {str(e)}")
        
        # Decode base64 data
        try:
            print(f"[DEBUG] Decoding base64 data")
            sys.stdout.flush()
            image_data = base64.b64decode(encoded)
            # Don't log the length of encoded base64 string (could be very large)
            print(f"[DEBUG] Successfully decoded base64 data, size: {len(image_data) / 1024:.2f} KB")
            sys.stdout.flush()
            log(f"Successfully decoded base64 data, size: {len(image_data) / 1024:.2f} KB", request_id=request_id)
        except Exception as e:
            print(f"[ERROR] Error decoding base64 data: {str(e)}")
            sys.stdout.flush()
            log(f"Error decoding base64 data: {str(e)}", request_id=request_id)
            raise ValueError(f"Failed to decode base64 image data: {str(e)}")
        
        # Open the image
        try:
            print(f"[DEBUG] Opening image data")
            sys.stdout.flush()
            img_buffer = io.BytesIO(image_data)
            img = Image.open(img_buffer)
            print(f"[DEBUG] Successfully opened image. Format: {img.format}, Mode: {img.mode}, Size: {img.size}")
            sys.stdout.flush()
            log(f"Successfully opened image. Format: {img.format}, Mode: {img.mode}, Size: {img.size}", request_id=request_id)
        except Exception as e:
            print(f"[ERROR] Error opening image data: {str(e)}")
            sys.stdout.flush()
            log(f"Error opening image data: {str(e)}", request_id=request_id)
            raise ValueError(f"Failed to open image data: {str(e)}")
        
        # Convert to square by center cropping before resizing
        try:
            print(f"[DEBUG] Converting image to perfect square")
            sys.stdout.flush()
            
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
            img = img.crop((left, top, right, bottom))
            
            print(f"[DEBUG] Cropped to square: {img.size}")
            sys.stdout.flush()
            log(f"Cropped to square: {img.size}", request_id=request_id)
        except Exception as e:
            print(f"[ERROR] Error cropping image to square: {str(e)}")
            sys.stdout.flush()
            log(f"Error cropping image to square: {str(e)}", request_id=request_id)
            raise ValueError(f"Failed to crop image to square: {str(e)}")
        
        # Convert to RGB (removing alpha channel if present)
        try:
            print(f"[DEBUG] Converting image to RGB if needed")
            sys.stdout.flush()
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGB')
                print(f"[DEBUG] Converted image to RGB mode")
                sys.stdout.flush()
                log(f"Converted image to RGB mode", request_id=request_id)
        except Exception as e:
            print(f"[ERROR] Error converting image to RGB: {str(e)}")
            sys.stdout.flush()
            log(f"Error converting image to RGB: {str(e)}", request_id=request_id)
            raise ValueError(f"Failed to convert image to RGB: {str(e)}")
        
        # Resize to 512x512
        try:
            target_size = (512, 512)
            print(f"[DEBUG] Resizing image from {img.size} to {target_size}")
            sys.stdout.flush()
            log(f"Resizing image from {img.size} to {target_size} for OpenAI", request_id=request_id)
            img = img.resize(target_size, Image.Resampling.LANCZOS)
            print(f"[DEBUG] Successfully resized image to {img.size}")
            sys.stdout.flush()
            log(f"Successfully resized image to {img.size}", request_id=request_id)
        except Exception as e:
            print(f"[ERROR] Error resizing image: {str(e)}")
            sys.stdout.flush()
            log(f"Error resizing image: {str(e)}", request_id=request_id)
            raise ValueError(f"Failed to resize image: {str(e)}")
        
        # Save as JPG to buffer
        try:
            print(f"[DEBUG] Saving image as JPEG")
            sys.stdout.flush()
            output_buffer = io.BytesIO()
            img.save(output_buffer, format="JPEG", quality=90)
            output_buffer.seek(0)
            print(f"[DEBUG] Successfully saved image as JPEG")
            sys.stdout.flush()
            log(f"Successfully saved image as JPEG", request_id=request_id)
        except Exception as e:
            print(f"[ERROR] Error saving image as JPEG: {str(e)}")
            sys.stdout.flush()
            log(f"Error saving image as JPEG: {str(e)}", request_id=request_id)
            raise ValueError(f"Failed to save image as JPEG: {str(e)}")
        
        # Encode as base64
        try:
            print(f"[DEBUG] Encoding image to base64")
            sys.stdout.flush()
            jpg_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
            # Don't log the actual base64 string, just log its length
            print(f"[DEBUG] Successfully encoded image as base64, length: {len(jpg_base64) // 1024} KB")
            sys.stdout.flush()
            log(f"Successfully encoded image as base64, length: {len(jpg_base64) // 1024} KB", request_id=request_id)
        except Exception as e:
            print(f"[ERROR] Error encoding image to base64: {str(e)}")
            sys.stdout.flush()
            log(f"Error encoding image to base64: {str(e)}", request_id=request_id)
            raise ValueError(f"Failed to encode image as base64: {str(e)}")
        
        # Create new data URL
        resized_data_url = f"data:image/jpeg;base64,{jpg_base64}"
        
        # Calculate size reduction
        original_size = len(image_data_url) / 1024
        new_size = len(resized_data_url) / 1024
        print(f"[DEBUG] Image resized for OpenAI API: {original_size:.2f}KB -> {new_size:.2f}KB")
        sys.stdout.flush()
        log(f"Image resized for OpenAI API: {original_size:.2f}KB -> {new_size:.2f}KB", request_id=request_id)
        
        return resized_data_url
        
    except Exception as e:
        print(f"[ERROR] Unexpected error resizing image for OpenAI: {str(e)}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        sys.stdout.flush()
        log(f"Unexpected error resizing image for OpenAI: {str(e)}", request_id=request_id)
        # Re-raise with clear message
        raise ValueError(f"Failed to resize image for OpenAI: {str(e)}")

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
    
    # Direct print to console to track progress
    print(f"[TRACE] Starting generate_ai_card_details for hex color: {hex_color}")
    sys.stdout.flush()
    
    # Validate that the image is provided
    if not cropped_image_data_url:
        print(f"[ERROR] No cropped image provided for AI generation")
        sys.stdout.flush()
        log(f"Error: No cropped image provided for AI generation", request_id=request_id)
        raise ValueError("A cropped image is required for AI card detail generation")
    
    # Validate the image data URL format
    if not cropped_image_data_url.startswith('data:image/'):
        print(f"[ERROR] Invalid image data URL format: {cropped_image_data_url[:30]}...")
        sys.stdout.flush()
        log(f"Error: Invalid image data URL format: {cropped_image_data_url[:30]}...", request_id=request_id)
        raise ValueError("Invalid image data URL format. Must start with 'data:image/'")
    
    if ';base64,' not in cropped_image_data_url:
        print(f"[ERROR] Invalid image data URL format - missing base64 delimiter")
        sys.stdout.flush()
        log(f"Error: Invalid image data URL format - missing base64 delimiter", request_id=request_id)
        raise ValueError("Invalid image data URL format - missing base64 delimiter")
    
    OVERALL_TIMEOUT = 59.0 # Slightly less than Vercel's 60s Hobby limit

    print(f"[TRACE] Starting Azure OpenAI API call for hex color '{hex_color}' with image")
    sys.stdout.flush()
    log(f"Starting Azure OpenAI API call for hex color '{hex_color}' with image. Overall timeout {OVERALL_TIMEOUT}s.", request_id=request_id)
    api_call_start_time = time.time()

    try:
        # Resize and convert the image to 512x512 JPG for OpenAI
        try:
            print(f"[TRACE] Starting image optimization")
            sys.stdout.flush()
            log(f"Starting image optimization", request_id=request_id)
            optimized_image_data_url = resize_and_convert_image_for_openai(cropped_image_data_url, request_id)
            print(f"[TRACE] Image optimization complete")
            sys.stdout.flush()
            log(f"Image optimization complete", request_id=request_id)
        except ValueError as resize_error:
            print(f"[ERROR] Error resizing image for OpenAI API: {str(resize_error)}")
            sys.stdout.flush()
            log(f"Error resizing image for OpenAI API: {str(resize_error)}", request_id=request_id)
            raise ValueError(f"Image processing failed: {str(resize_error)}")
        except Exception as e:
            print(f"[ERROR] Unexpected error during image processing: {str(e)}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            sys.stdout.flush()
            log(f"Unexpected error during image processing: {str(e)}", request_id=request_id)
            raise ValueError(f"Unexpected error during image processing: {str(e)}")
        
        # Prepare messages with or without image
        print(f"[TRACE] Preparing OpenAI API request messages")
        sys.stdout.flush()
        system_message = {
            "role": "system",
            "content": "You are a creative assistant. For the given hex color and image, generate poetic and evocative card details."
        }
        
        # Always include the image since we validated it above
        print(f"[TRACE] Building OpenAI API request with optimized 512x512 image")
        sys.stdout.flush()
        log(f"Building OpenAI API request with optimized 512x512 image", request_id=request_id)
        
        # Truncate the optimized image URL for logging purposes
        logging_image_url = optimized_image_data_url[:30] + "..." if optimized_image_data_url else None
        
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
                        f"4. description: A poetic description (max 25-30 words) that evokes the feeling/mood of the image, describe the main chaacter. Explain what is the person wearing." # of this color, inspired by its hex value and the provided image.\n\n"
                        f"Format your response strictly as a JSON object with these exact keys: colorName, phoneticName, article, description."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": optimized_image_data_url,
                        "detail": "low"
                    }
                }
            ]
        }

        # Log the request parameters (excluding the actual image data for brevity)
        print(f"[TRACE] Preparing to send request to Azure OpenAI API")
        sys.stdout.flush()
        log_request = {
            "model": os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
            "message_count": 2,  # system + user
            "image_included": True,
            "detail_level": "low"
        }
        log(f"Azure OpenAI API request parameters: {json.dumps(log_request)}", request_id=request_id)

        try:
            print(f"[TRACE] Sending request to Azure OpenAI API")
            sys.stdout.flush()
            log(f"Sending request to Azure OpenAI API", request_id=request_id)
            
            print(f"[TRACE] API endpoint: {os.environ.get('AZURE_OPENAI_ENDPOINT')}")
            print(f"[TRACE] API model: {os.environ.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini')}")
            print(f"[TRACE] API version: {os.environ.get('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')}")
            sys.stdout.flush()
            
            # Ensure the Azure client is properly initialized
            if not azure_client:
                print(f"[ERROR] Azure OpenAI client is not initialized")
                sys.stdout.flush()
                raise ValueError("Azure OpenAI client is not initialized")
            
            completion = await asyncio.wait_for(
                azure_client.chat.completions.create(
                    model=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
                    messages=[system_message, user_message],
                    response_format={"type": "json_object"}
                ),
                timeout=OVERALL_TIMEOUT
            )
            print(f"[TRACE] Successfully received response from Azure OpenAI API")
            sys.stdout.flush()
            log(f"Successfully received response from Azure OpenAI API", request_id=request_id)
        except asyncio.TimeoutError:
            print(f"[ERROR] Azure OpenAI API call timed out after {OVERALL_TIMEOUT}s")
            sys.stdout.flush()
            log(f"Azure OpenAI API call timed out via asyncio.wait_for after {OVERALL_TIMEOUT}s.", request_id=request_id)
            raise ValueError(f"AI generation timed out after {OVERALL_TIMEOUT} seconds")
        except Exception as api_error:
            print(f"[ERROR] Error calling Azure OpenAI API: {str(api_error)}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            sys.stdout.flush()
            log(f"Error calling Azure OpenAI API: {str(api_error)}", request_id=request_id)
            raise ValueError(f"Error calling Azure OpenAI API: {str(api_error)}")
        
        api_call_duration = time.time() - api_call_start_time
        print(f"[TRACE] Azure OpenAI API call completed in {api_call_duration:.2f} seconds")
        sys.stdout.flush()
        log(f"Azure OpenAI API call completed in {api_call_duration:.2f} seconds", request_id=request_id)

        if not completion.choices or not completion.choices[0].message or not completion.choices[0].message.content:
            print(f"[ERROR] Azure OpenAI response was empty or malformed")
            sys.stdout.flush()
            log(f"Azure OpenAI response was empty or malformed.", request_id=request_id)
            raise ValueError("Empty or malformed response from AI")

        response_text = completion.choices[0].message.content
        print(f"[TRACE] Raw response from OpenAI: {response_text}")
        sys.stdout.flush()
        log(f"Raw response from OpenAI: {response_text}", request_id=request_id)
        
        try:
            print(f"[TRACE] Parsing JSON response")
            sys.stdout.flush()
            response_data = json.loads(response_text)
            print(f"[TRACE] Successfully parsed JSON response")
            sys.stdout.flush() 
            log(f"Parsed AI response: {json.dumps(response_data, indent=2)}", request_id=request_id)
        except json.JSONDecodeError as json_error:
            print(f"[ERROR] Failed to parse JSON response: {str(json_error)}")
            sys.stdout.flush()
            log(f"Failed to parse JSON response: {str(json_error)}", request_id=request_id)
            raise ValueError(f"Failed to parse AI response as JSON: {str(json_error)}")

        # Get default color name from hex if needed for fallbacks
        hex_clean = hex_color.lstrip('#').upper()
        default_color_name = f"HEX {hex_clean[:3]}"

        # Format the response
        print(f"[TRACE] Formatting the response")
        sys.stdout.flush()
        
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

        final_details = {
            "colorName": str(response_data.get("colorName", default_color_name.upper())).strip().upper(),
            "phoneticName": phonetic_final,
            "article": article_final,
            "description": str(response_data.get("description", f"A color with hex value {hex_color}.")).strip()
        }
        print(f"[TRACE] Successfully formatted AI details")
        sys.stdout.flush()
        log(f"Successfully formatted AI details: {json.dumps(final_details, indent=2)}", request_id=request_id)
        
        print(f"[TRACE] Returning final details")
        sys.stdout.flush()
        return final_details

    except asyncio.TimeoutError:
        print(f"[ERROR] Azure OpenAI API call timed out after {OVERALL_TIMEOUT}s")
        sys.stdout.flush()
        log(f"Azure OpenAI API call timed out via asyncio.wait_for after {OVERALL_TIMEOUT}s.", request_id=request_id)
        # Don't handle this error, propagate it to the caller
        raise ValueError(f"AI generation timed out after {OVERALL_TIMEOUT} seconds")
        
    except Exception as e:
        print(f"[ERROR] Error during Azure OpenAI call or processing: {str(e)}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        sys.stdout.flush()
        log(f"Error during Azure OpenAI call or processing: {str(e)}", request_id=request_id)
        # Propagate the error to the caller
        raise 