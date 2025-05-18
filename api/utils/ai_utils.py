"""
Core AI functionality for generating card details using Azure OpenAI.
"""
import json
import time
import asyncio
import os
from typing import Dict, Any, Optional

from api.models.card import ColorCardDetails
from api.utils.logger import log, info, debug
from api.utils.image_processor import resize_and_convert_image_for_openai
from api.utils.response_formatter import OpenAIResponseFormatter
from api.utils.openai_client import azure_client, OVERALL_TIMEOUT

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
            debug(f"Starting image optimization", request_id=request_id)
            optimized_image_data_url = resize_and_convert_image_for_openai(cropped_image_data_url, request_id)
            debug(f"Image optimization complete", request_id=request_id)
        except ValueError as resize_error:
            log(f"Error resizing image for OpenAI API: {str(resize_error)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Image processing failed: {str(resize_error)}")
        
        # Log request parameters
        model_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        log_request = {
            "model": model_name,
            "image_included": True,
            "image_size": len(optimized_image_data_url) // 1024,
        }
        debug(f"Azure OpenAI API request parameters: {json.dumps(log_request)}", request_id=request_id)

        try:
            debug(f"Sending request to Azure OpenAI API", request_id=request_id)
            
            # Ensure the Azure client is properly initialized
            if not azure_client:
                log(f"Azure OpenAI client is not initialized", level="ERROR", request_id=request_id)
                raise ValueError("Azure OpenAI client is not initialized")

            # Create the messages array with image
            messages = [
                {
                    "role": "system", 
                    "content": "You are a creative assistant. For the given hex color and image, generate poetic and evocative card details."
                },
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text", 
                            "text": (
                                f"""
                                # Main goal
                                Generate details based for a color card, based on:
                                1. hex value '{hex_color}',
                                2. analysis of attached image.
                                
                                # Detailed description
                                Create a creative name and description inspired by both the color and the image content.
                                It's a pantone like swatch card with a twist.
                                
                                The image and color is coming from the user.
                                It should give the user his unique color name and description that will take into consideration not only the hex value (chosen by the user), but also the image.
                                When you try to figure the name and description out , remember - it's not only about the elements of image, but also the emotions one can feel when looks at the image. You should always find something positive. To make the user's day better, inspired. It will be poetic for sure. And unique. Each card is unique.
                                
                                The description should fit the name.
                                Make your ideas wander. Good luck.
                                """
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": optimized_image_data_url, "detail": "low"}
                        }
                    ]
                }
            ]
            
            # Measure just the OpenAI API call time
            openai_api_start_time = time.time()
            log(f"Starting Azure OpenAI API request at {time.strftime('%H:%M:%S')}", request_id=request_id)
            
            # Use the beta.chat.completions.parse method with the ColorCardDetails Pydantic model
            completion = await asyncio.wait_for(
                azure_client.beta.chat.completions.parse(
                    model=model_name,
                    messages=messages,
                    max_completion_tokens=1500,
                    response_format=ColorCardDetails,
                ),
                timeout=OVERALL_TIMEOUT
            )
            
            openai_api_duration = time.time() - openai_api_start_time
            log(f"Azure OpenAI API request completed in {openai_api_duration:.2f} seconds", request_id=request_id)
            
            log(f"Successfully received response from Azure OpenAI API", request_id=request_id)

            # Log token usage if available in the response
            if hasattr(completion, 'usage') and completion.usage:
                usage = completion.usage
                log(f"Token usage - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}", 
                    request_id=request_id)
            else:
                debug(f"No token usage information available in the response", request_id=request_id)

            if not completion.choices or not completion.choices[0].message or not completion.choices[0].message.parsed:
                log(f"Azure OpenAI response was empty or malformed", level="ERROR", request_id=request_id)
                raise ValueError("Empty or malformed response from AI")
            
            # Get the parsed output directly from the response
            card_details = completion.choices[0].message.parsed
            debug(f"Parsed structured output: {card_details}", request_id=request_id)
            
            # Format the response
            final_details = OpenAIResponseFormatter.format_response(card_details, hex_color)
            info(f"Successfully formatted AI details: {json.dumps(final_details, indent=2)}", request_id=request_id)
                
            return final_details
                
        except asyncio.TimeoutError:
            log(f"Azure OpenAI API call timed out via asyncio.wait_for after {OVERALL_TIMEOUT}s.", level="ERROR", request_id=request_id)
            raise ValueError(f"AI generation timed out after {OVERALL_TIMEOUT} seconds")
        except Exception as api_error:
            log(f"Error calling Azure OpenAI API: {str(api_error)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Error calling Azure OpenAI API: {str(api_error)}")
        
        api_call_duration = time.time() - api_call_start_time
        log(f"Azure OpenAI API call completed in {api_call_duration:.2f} seconds", request_id=request_id)

    except asyncio.TimeoutError:
        log(f"Azure OpenAI API call timed out via asyncio.wait_for after {OVERALL_TIMEOUT}s.", level="ERROR", request_id=request_id)
        raise ValueError(f"AI generation timed out after {OVERALL_TIMEOUT} seconds")
        
    except Exception as e:
        log(f"Error during Azure OpenAI call or processing: {str(e)}", level="ERROR", request_id=request_id)
        raise 