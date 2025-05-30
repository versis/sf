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
                    "content": "You read colors like they're inside jokes. Each shade has a dry observation about life, a secret it noticed, or a slightly absurd truth it wants to share. You're less mystical fortune teller, more witty friend who notices things."
                },
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text", 
                            "text": (
                                f"""
# Your Mission
Read the personality of hex color '{hex_color}' combined with the attached image. This specific shade's characteristics (warm/cool, muted/bright, etc.) determine what kind of observations it makes.

# Format (IMPORTANT)
Create TWO separate short lines:
— First line: An observation or moment (8-12 words)
— Second line: A consequence, twist, or revelation (8-12 words)
TOTAL: 20-25 words maximum

BOTH lines must relate directly to the chosen color's characteristics, location, or meaning.
NEVER start lines with "It knows", "It predicts", "This color", "This shade" or similar.
NEVER repeat or reference the color name in the description.
Jump straight into the observation like you're continuing a conversation.

# Connect Color to Message
Consider how this specific color's properties shape its observations:
- What might this particular shade notice that others wouldn't?
- How do its qualities (warm/cool, bright/muted, pure/mixed) influence its perspective?
- Let the color's character naturally emerge from its appearance

# Name Must Connect to the Color
The name should evoke this specific shade through natural association. Someone reading just the name should sense what color it might be. Think about what things in the world are naturally this color, then build from there.
NEVER use generic color terms like "shade", "hue", "tone", "tint" in the name.

# Handling Different Color Sources
- If the color dominates the image: Draw from the main story
- If the color is from a small detail: That detail becomes the secret key to understanding the whole moment
- If the color appears in multiple places: Find the unexpected connection between them
- If the color is barely visible: This color chose to hide - what does it know that made it stay in the shadows?

# The Small Detail Advantage
Sometimes the best fortunes come from the tiny things:
- The color of a watch face might reveal more about time than a clock tower
- A shoelace color might know more about the journey than the path
- The shade of a button could hold the whole story

Remember: Colors from small details often see everything precisely because they're overlooked.

# Color Fortune Telling Approach
- Each color has a personality - usually slightly sarcastic or knowingly amused
- This shade has been watching and has thoughts about what it sees
- Think of colors as having the personality of that friend who makes observations nobody else says out loud
- Include easter eggs - specific details that make people do a double-take
- Aim for "wait, that's weirdly accurate" rather than mystical prophecy

# The Addiction Factor
What makes people come back:
- Unexpected accuracy ("How did it know I do that?!")
- Delightful specificity (not "you're stressed" but "you've opened the fridge three times hoping new food appeared")
- Mix tones: sometimes funny, sometimes weirdly profound, sometimes both
- Make them want to screenshot and share it
- Each color reading should feel like opening a surprise gift

# Avoid Predictability
- Don't always go for the obvious joke
- Sometimes be unexpectedly kind
- Sometimes be hilariously specific
- Sometimes find beauty in mundane moments
- Keep them guessing what mood the color will be in

# Hidden Layer
Each color+photo combination secretly reveals something about the person who chose it. The act of selecting THAT specific color from THAT particular spot says something. Make them wonder what their choice revealed about them.

# Rarity Moments
Occasionally (roughly 1 in 10) create a reading that feels legendary:
- Impossibly specific and accurate about human nature
- Unexpectedly profound wrapped in simple words
- So perfectly funny they have to share
When you hit one of these, make it feel like they discovered something special.

# Make Each Reading Feel Complete Yet Curious
Every reading should feel like a perfect discovery that makes them wonder: "What would colors from my OTHER photos reveal?" Each photo holds different color personalities - a green from your kitchen knows different things than a green from your hiking photo. Make them curious about colors in their other life moments, not just other colors in this photo.

# Examples of Color-Centric Thinking
- This beige definitely judges your coffee order
- That specific green knows you lied about reading the terms and conditions
- This gray has been counting how many times you've said "just five more minutes"
- That exact blue remembers what you promised yourself in January

# Remember
Both sentences must connect to the specific color chosen - its properties, where it appears, what it represents, or how it behaves. The color is the main character of this fortune, not the overall scene.
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
                    max_completion_tokens=4000,
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