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
from api.utils.openai_client import azure_client
from ..config import AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_CLIENT_TIMEOUT

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
    
    log(f"Starting Azure OpenAI API call for hex color '{hex_color}' with image. Overall timeout {AZURE_OPENAI_CLIENT_TIMEOUT}s.", request_id=request_id)
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
        model_name = AZURE_OPENAI_DEPLOYMENT
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
                    "content": "You are a creative color curator who crafts meaningful and personal color experiences. You create names and descriptions that make each person feel understood and celebrated through the intersection of their chosen color and image."
                },
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text", 
                            "text": (
                                f"""
                                    # Main Goal
                                    Create a deeply personal color card based on:
                                    1. Hex value: '{hex_color}'
                                    2. The attached image
                                    
                                    # Core Philosophy
                                    You're creating a unique color that belongs to THIS specific person. This isn't just any color - it's THEIR color, discovered in THEIR moment, through THEIR lens.
                                    
                                    # Image Analysis Guidelines
                                    First, analyze the image carefully:
                                    - If there's one main person: This is likely the user themselves. Speak to them directly through the color.
                                    - If it's a scene/object/multiple people: The user chose to capture this moment. Honor their eye, their timing, their perspective.
                                    
                                    # Personalization Approach
                                    Consider:
                                    - What emotion or memory might this photo hold for them?
                                    - What was special about the moment they pressed the shutter?
                                    - How does their chosen color connect to their personal story in this image?
                                    - What quality in them does this photo+color combination reveal?
                                    
                                    # Writing Style Requirements
                                    - Avoid generic descriptions (no "whispers of," "dance of," "embrace of," "symphony of")
                                    - NEVER start with: "This hue," "This color," "This shade," "A color that," "The color," "A shade," "The shade," "The hue," or ANY variation mentioning color/hue/shade/tone
                                    - Begin immediately with descriptive language - like a snapshot of a moment
                                    - Jump straight into the essence: "Afternoon light on grandmother's jewelry box" or "Three AM coffee and unfinished conversations"
                                    - Start with concrete imagery or relatable moments - NEVER with color terminology
                                    - Each description should feel like it could ONLY belong to this specific photo+color combination
                                    - Use clear, evocative language that balances creativity with accessibility
                                    - Write in third person, describing the color/concept itself
                                    - The description should feel personal and meaningful without being overly flowery
                                    
                                    # Description Depth (let the image+color naturally guide which aspect emerges):
                                    - For intimate moments: Focus on personal memories or familiar details
                                    - For joyful/achievement moments: Capture celebration or personal milestones
                                    - For contemplative scenes: Explore reflections or meaningful observations
                                    - For dynamic/energetic images: Highlight personality or creative energy
                                    - For grounding moments: Anchor significant life moments or transitions
                                    
                                    # Analysis Process (complete this internally before creating the final output)
                                    
                                    ## Step 1: Image Analysis
                                    - Visual elements: What objects, people, scenery are present?
                                    - Composition: What's the focal point? Background elements?
                                    - Lighting: Natural/artificial? Time of day? Shadows and highlights?
                                    - Mood/Atmosphere: What emotions does this image evoke?
                                    - Story: What moment is being captured? What happened before/after?
                                    - Personal significance: Why might this photo be special to the person who took it?
                                    
                                    ## Step 2: Color Analysis
                                    - Basic properties: Is it warm/cool? Light/dark? Saturated/muted?
                                    - Emotional qualities: Calm/energetic? Joyful/melancholic? Bold/subtle?
                                    - Natural associations: What in nature has this color? (sky, plants, minerals, etc.)
                                    - Cultural associations: What does this color typically represent?
                                    - Sensory connections: What textures, tastes, sounds, or temperatures relate to this color?
                                    
                                    ## Step 3: Intersection Discovery
                                    - How does this specific color relate to this specific image?
                                    - What unique story emerges from THIS color in THIS context?
                                    - What unexpected connections can be made?
                                    - What makes this combination one-of-a-kind?
                                    - What personal quality or moment does this combination reveal?
                                    
                                    ## Step 4: Creative Synthesis
                                    - Based on the above analysis, craft a name and description that:
                                      - Captures the unique intersection of color + image
                                      - Feels deeply personal and specific
                                      - Uses fresh, unexpected language
                                      - Creates a sense of discovery and significance
                                    
                                    # Output Structure
                                    Create:
                                    - A color name that feels like a personal discovery (max 3 words, ALL CAPS)
                                    - A description written in third person that captures the essence of this unique color (25-33 words)
                                    - The description should describe the color/concept itself, not address the user directly
                                    - Still make it deeply personal and unique to their photo+color combination
                                    
                                    Remember: This color didn't exist until they created it. Make them feel the magic of that creation through poetic, immediate description.
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
                    max_completion_tokens=2500,
                    response_format=ColorCardDetails,
                ),
                timeout=AZURE_OPENAI_CLIENT_TIMEOUT
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
            log(f"Azure OpenAI API call timed out via asyncio.wait_for after {AZURE_OPENAI_CLIENT_TIMEOUT}s.", level="ERROR", request_id=request_id)
            raise ValueError(f"AI generation timed out after {AZURE_OPENAI_CLIENT_TIMEOUT} seconds")
        except Exception as api_error:
            log(f"Error calling Azure OpenAI API: {str(api_error)}", level="ERROR", request_id=request_id)
            raise ValueError(f"Error calling Azure OpenAI API: {str(api_error)}")
        
        api_call_duration = time.time() - api_call_start_time
        log(f"Azure OpenAI API call completed in {api_call_duration:.2f} seconds", request_id=request_id)

    except asyncio.TimeoutError:
        log(f"Azure OpenAI API call timed out via asyncio.wait_for after {AZURE_OPENAI_CLIENT_TIMEOUT}s.", level="ERROR", request_id=request_id)
        raise ValueError(f"AI generation timed out after {AZURE_OPENAI_CLIENT_TIMEOUT} seconds")
        
    except Exception as e:
        log(f"Error during Azure OpenAI call or processing: {str(e)}", level="ERROR", request_id=request_id)
        raise 