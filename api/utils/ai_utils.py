import os
import json
import time
import asyncio
from typing import Dict, Any
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv

from api.utils.logger import log

load_dotenv(".env.local")

# Client for Azure OpenAI
azure_client = AsyncAzureOpenAI(
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
)

async def generate_ai_card_details(color_name: str, hex_color: str, request_id: str = None) -> Dict[str, Any]:
    """
    Generates AI-based card details using Azure OpenAI.
    Returns a dictionary with card name, phonetic, part of speech, and description.
    Overall operation timeout is 59s enforced by asyncio.wait_for.
    """
    
    OVERALL_TIMEOUT = 59.0 # Slightly less than Vercel's 60s Hobby limit

    log(f"Starting Azure OpenAI API call for color '{color_name}' (hex: {hex_color}). Overall timeout {OVERALL_TIMEOUT}s.", request_id=request_id)
    api_call_start_time = time.time()

    try:
        completion = await asyncio.wait_for(
            azure_client.chat.completions.create(
                model=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a creative assistant. For the given color, generate poetic and evocative card details."
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Generate details for a color card named '{color_name}' with hex value '{hex_color}'. I need these fields:\n"
                            f"1. cardName: A creative and evocative alternative name for the color (max 3 words, ALL CAPS).\n"
                            f"2. phoneticName: Phonetic pronunciation (IPA symbols) for your new creative cardName.\n"
                            f"3. article: The part of speech for the cardName (e.g., noun, adjective phrase).\n"
                            f"4. description: A poetic description (max 25-30 words) that evokes the feeling/mood of this color, inspired by its name and hex value.\n\n"
                            f"Format your response strictly as a JSON object with these exact keys: cardName, phoneticName, article, description."
                        )
                    }
                ],
                response_format={"type": "json_object"}
            ),
            timeout=OVERALL_TIMEOUT
        )
        
        api_call_duration = time.time() - api_call_start_time
        log(f"Azure OpenAI API call completed in {api_call_duration:.2f} seconds", request_id=request_id)

        if not completion.choices or not completion.choices[0].message or not completion.choices[0].message.content:
            log(f"Azure OpenAI response was empty or malformed.", request_id=request_id)
            raise ValueError("Empty or malformed response from AI")

        response_text = completion.choices[0].message.content
        response_data = json.loads(response_text)
        log(f"Parsed AI response: {json.dumps(response_data, indent=2)}", request_id=request_id)

        # Ensure required fields exist in the response
        if not response_data.get("cardName"):
            log(f"Missing required field 'cardName' in AI response", request_id=request_id)
            raise ValueError("AI response missing required field: cardName")
            
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
            "cardName": str(response_data["cardName"]).strip().upper(),
            "phoneticName": phonetic_final,
            "article": article_final,
            "description": str(response_data.get("description", "")).strip()
        }
        
        # Verify we have a description
        if not final_details["description"]:
            log(f"Missing required field 'description' in AI response", request_id=request_id)
            raise ValueError("AI response missing required field: description")
            
        log(f"Successfully formatted AI details: {json.dumps(final_details, indent=2)}", request_id=request_id)
        return final_details

    except asyncio.TimeoutError:
        log(f"Azure OpenAI API call timed out via asyncio.wait_for after {OVERALL_TIMEOUT}s.", request_id=request_id)
        raise TimeoutError(f"AI generation timed out after {OVERALL_TIMEOUT} seconds")
    
    except Exception as e:
        log(f"Error during Azure OpenAI call or processing: {str(e)}", request_id=request_id)
        raise ValueError(f"AI generation failed: {str(e)}") 