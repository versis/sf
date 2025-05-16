import os
import json
import time
import uuid
import base64
import re
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Request as FastAPIRequest
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from api.utils.logger import log
from api.utils.ai_utils import generate_ai_card_details
from api.utils.card_utils import generate_card_image_bytes, hex_to_rgb

# Rate limiting with slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn

load_dotenv(".env.local")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sf.tinker.institute", "https://sf-livid.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

# OpenAI client initialization is kept for future use
# client = OpenAI(
#     api_key=os.environ.get("OPENAI_API_KEY"),
# )

# Azure OpenAI client initialization (REMOVED - now handled in api/utils/ai_utils.py)
# azure_client = AzureOpenAI(
#     api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
#     api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
#     azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
# )

# class ChatRequest(BaseModel):
#     messages: List[ClientMessage]

# --- Color Conversion Utilities (from shadefreude) ---
def hex_to_rgb(hex_color: str) -> tuple[int, int, int] | None:
    """Converts a HEX color string to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if not re.match(r"^[0-9a-fA-F]{6}$", hex_color) and not re.match(r"^[0-9a-fA-F]{3}$", hex_color):
        print(f"Invalid HEX format: {hex_color}")
        return None 
    
    if len(hex_color) == 3:
        r = int(hex_color[0]*2, 16)
        g = int(hex_color[1]*2, 16)
        b = int(hex_color[2]*2, 16)
    else: # len == 6
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    return (r, g, b)

def rgb_to_cmyk(r: int, g: int, b: int) -> tuple[int, int, int, int]:
    """Converts an RGB color (0-255) to CMYK (0-100)."""
    if (r, g, b) == (0, 0, 0):
        return 0, 0, 0, 100

    c = 1 - (r / 255.0)
    m = 1 - (g / 255.0)
    y = 1 - (b / 255.0)

    min_cmy = min(c, m, y)
    # Handle case for white to avoid division by zero if 1 - min_cmy is 0
    if min_cmy == 1.0: # This means c, m, y were all 0 (white)
        return 0, 0, 0, 0

    c = (c - min_cmy) / (1 - min_cmy)
    m = (m - min_cmy) / (1 - min_cmy)
    y = (y - min_cmy) / (1 - min_cmy)
    k = min_cmy

    return round(c * 100), round(m * 100), round(y * 100), round(k * 100)
# --- End Color Conversion Utilities ---

# --- Font Loading ---
def get_font(size: int, weight: str = "Regular", style: str = "Normal", font_family: str = "Inter"):
    """
    Loads a font variant.
    font_family: "Inter" (default) or "Mono" for monospace
    Weight: "Regular", "Bold", "Light", "Medium", "SemiBold", "ExtraBold", "Black", "Thin", "ExtraLight"
    Style: "Normal", "Italic"
    """
    # Import at function level to ensure availability in all scopes
    import os
    
    # Get the current working directory to help with debugging
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
    
    font_style_suffix = ""
    if style.lower() == "italic":
        font_style_suffix = "Italic"

    # Choose the best point size based on the requested size
    if size <= 20:
        pt_suffix = "18pt"
    elif size <= 25:
        pt_suffix = "24pt"
    else:
        pt_suffix = "28pt"
    
    if font_family == "Mono":
        # Use IBM Plex Mono for monospace text
        if weight == "Light":
            ibm_plex_path = "IBMPlexMono-Light.ttf"
        elif weight in ["Medium", "Bold", "SemiBold"]:
            ibm_plex_path = "IBMPlexMono-Medium.ttf"
        else:
            ibm_plex_path = "IBMPlexMono-Regular.ttf"
        
        # Fixed path for IBM Plex Mono fonts - only in assets/fonts/mono
        ibm_plex_mono_path = f"assets/fonts/mono/{ibm_plex_path}"
        
        try:
            loaded_font = ImageFont.truetype(ibm_plex_mono_path, size)
            print(f"Successfully loaded IBM Plex Mono")
            return loaded_font
        except IOError as e:
            print(f"Failed to load IBM Plex Mono: {e}")
            
            # If IBM Plex Mono fails, try Inter as fallback
            print("Falling back to Inter for monospace text")
            inter_fallback = f"assets/fonts/inter/Inter_{pt_suffix}-Regular.ttf"
            try:
                return ImageFont.truetype(inter_fallback, size)
            except:
                # Last resort
                return ImageFont.load_default()
    
    # For Inter font (default)
    font_name = f"Inter_{pt_suffix}-{weight}{font_style_suffix}.ttf"
    
    # Just one path to Inter fonts - now in inter directory
    inter_path = f"assets/fonts/inter/{font_name}"
    
    print(f"Attempting to load Inter: {inter_path}")
    try:
        loaded_font = ImageFont.truetype(inter_path, size)
        print(f"Successfully loaded Inter")
        return loaded_font
    except IOError as e:
        print(f"Failed to load Inter: {e}")
        # Just use the default font if Inter fails
        return ImageFont.load_default()
# --- End Font Loading ---

# --- Helper Function for Font Measurements ---
def get_text_dimensions(text: str, font):
    """
    Get text dimensions using the appropriate method based on PIL version.
    Works with both older PIL versions (getsize) and newer ones (getbbox).
    """
    try:
        # Try newer method first
        if hasattr(font, 'getbbox'):
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]  # width, height
        # Fall back to older method
        elif hasattr(font, 'getsize'):
            return font.getsize(text)
        # Last resort approximation
        else:
            # Very rough approximation
            return len(text) * (font.size // 2), font.size
    except Exception as e:
        print(f"Error measuring text '{text}': {e}")
        # Return a failsafe dimension
        return len(text) * 10, font.size

# --- Pydantic Models ---
class GenerateCardsRequest(BaseModel):
    croppedImageDataUrl: str
    hexColor: str
    colorName: str
    cardName: Optional[str] = None
    phoneticName: Optional[str] = None
    article: Optional[str] = None
    description: Optional[str] = None
    cardId: Optional[str] = "0000023 FE T"

class CardImageResponseItem(BaseModel):
    orientation: str
    image_base64: str
    filename: str

class GenerateCardsResponse(BaseModel):
    request_id: str
    ai_details_used: Dict[str, Any]
    generated_cards: List[CardImageResponseItem]
    error: Optional[str] = None

# --- Unified API Endpoint ---
@app.post("/api/generate-cards", response_model=GenerateCardsResponse)
@limiter.limit("5/minute")
async def generate_cards_route(data: GenerateCardsRequest, request: FastAPIRequest):
    request_id = str(uuid.uuid4())[:8]
    log(f"Unified /api/generate-cards request received", request_id=request_id)
    request_start_time = time.time()

    final_card_details: Dict[str, Any] = {}
    default_card_id = "0000023 FE T"

    if not hex_to_rgb(data.hexColor):
        log(f"Invalid hexColor format provided: {data.hexColor}", request_id=request_id)
        return JSONResponse(
            status_code=400,
            content=GenerateCardsResponse(
                request_id=request_id, 
                ai_details_used={},
                generated_cards=[],
                error=f"Invalid hexColor format: {data.hexColor}"
            ).model_dump()
        )

    if data.cardName and data.phoneticName and data.article and data.description:
        log("User provided all card details. Skipping AI generation.", request_id=request_id)
        final_card_details = {
            "cardName": data.cardName.strip().upper(),
            "phoneticName": data.phoneticName.strip(),
            "article": data.article.strip(),
            "description": data.description.strip(),
            "cardId": data.cardId.strip() if data.cardId else default_card_id
        }
    else:
        log("User did not provide all details, proceeding with AI generation.", request_id=request_id)
        try:
            ai_generated_details = await generate_ai_card_details(data.colorName, data.hexColor, request_id)
            final_card_details = ai_generated_details
            final_card_details["cardId"] = data.cardId.strip() if data.cardId else default_card_id
        except Exception as e:
            log(f"AI details generation ultimately failed: {str(e)}. Using fallback text details.", request_id=request_id)
            final_card_details = {
                "cardName": data.colorName.strip().upper(), 
                "phoneticName": "['fɔːl.bæk]",
                "article": "[noun]",
                "description": f"A beautiful color named {data.colorName.strip()}. (AI generation yielded fallback)",
                "cardId": data.cardId.strip() if data.cardId else default_card_id
            }

    log(f"Final card details for rendering: {json.dumps(final_card_details, indent=2)}", request_id=request_id)

    generated_cards_response_items: List[CardImageResponseItem] = []
    orientations_to_generate = ["horizontal", "vertical"]

    try:
        for orientation in orientations_to_generate:
            log(f"Generating {orientation} card image...", request_id=request_id)
            image_bytes = await generate_card_image_bytes(
                cropped_image_data_url=data.croppedImageDataUrl,
                card_details=final_card_details,
                hex_color_input=data.hexColor,
                orientation=orientation,
                request_id=request_id
            )
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            generated_cards_response_items.append(
                CardImageResponseItem(
                    orientation=orientation,
                    image_base64=image_base64,
                    filename=f"card_{final_card_details['cardName'].replace(' ', '_')}_{orientation}_{request_id}.jpg"
                )
            )
            log(f"Successfully generated {orientation} card image.", request_id=request_id)
        
        total_duration = time.time() - request_start_time
        log(f"All cards generated successfully in {total_duration:.2f} seconds.", request_id=request_id)
        
        return GenerateCardsResponse(
            request_id=request_id,
            ai_details_used=final_card_details,
            generated_cards=generated_cards_response_items
        )

    except ValueError as ve:
        log(f"ValueError during card generation: {str(ve)}", request_id=request_id)
        return JSONResponse(
            status_code=400,
            content=GenerateCardsResponse(
                request_id=request_id, 
                ai_details_used=final_card_details, 
                generated_cards=[], 
                error=str(ve)
            ).model_dump()
        )
    except Exception as e:
        log(f"General error during card generation processing: {str(e)}", request_id=request_id)
        return JSONResponse(
            status_code=500,
            content=GenerateCardsResponse(
                request_id=request_id, 
                ai_details_used=final_card_details, 
                generated_cards=[], 
                error="Internal server error during image processing."
            ).model_dump()
        )

# available_tools = {
#     "get_current_weather": get_current_weather,
# }

# def do_stream(messages: List[ChatCompletionMessageParam]):
#     stream = client.chat.completions.create(
#         messages=messages,
#         model="gpt-4o",
#         stream=True,
#         tools=[{
#             "type": "function",
#             "function": {
#                 "name": "get_current_weather",
#                 "description": "Get the current weather at a location",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "latitude": {
#                             "type": "number",
#                             "description": "The latitude of the location",
#                         },
#                         "longitude": {
#                             "type": "number",
#                             "description": "The longitude of the location",
#                         },
#                     },
#                     "required": ["latitude", "longitude"],
#                 },
#             },
#         }]
#     )
#     return stream

# def stream_text(messages: List[ChatCompletionMessageParam], protocol: str = 'data'):
#     draft_tool_calls = []
#     draft_tool_calls_index = -1
#     stream = client.chat.completions.create(
#         messages=messages,
#         model="gpt-4o",
#         stream=True,
#         tools=[{
#             "type": "function",
#             "function": {
#                 "name": "get_current_weather",
#                 "description": "Get the current weather at a location",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "latitude": {
#                             "type": "number",
#                             "description": "The latitude of the location",
#                         },
#                         "longitude": {
#                             "type": "number",
#                             "description": "The longitude of the location",
#                         },
#                     },
#                     "required": ["latitude", "longitude"],
#                 },
#             },
#         }]
#     )
#     for chunk in stream:
#         for choice in chunk.choices:
#             if choice.finish_reason == "stop":
#                 continue
#             elif choice.finish_reason == "tool_calls":
#                 for tool_call in draft_tool_calls:
#                     yield '9:{{"toolCallId":"{id}","toolName":"{name}","args":{args}}}\n'.format(
#                         id=tool_call["id"],
#                         name=tool_call["name"],
#                         args=tool_call["arguments"])
#                 for tool_call in draft_tool_calls:
#                     tool_result = available_tools[tool_call["name"]](
#                         **json.loads(tool_call["arguments"])) # type: ignore
#                     yield 'a:{{"toolCallId":"{id}","toolName":"{name}","args":{args},"result":{result}}}\n'.format(
#                         id=tool_call["id"],
#                         name=tool_call["name"],
#                         args=tool_call["arguments"],
#                         result=json.dumps(tool_result))
#             elif choice.delta.tool_calls:
#                 for tool_call in choice.delta.tool_calls:
#                     id = tool_call.id
#                     name = tool_call.function.name
#                     arguments = tool_call.function.arguments
#                     if (id is not None):
#                         draft_tool_calls_index += 1
#                         draft_tool_calls.append(
#                             {"id": id, "name": name, "arguments": ""})
#                     else:
#                         draft_tool_calls[draft_tool_calls_index]["arguments"] += arguments # type: ignore
#             else:
#                 yield '0:{text}\n'.format(text=json.dumps(choice.delta.content))
#         if chunk.choices == []:
#             usage = chunk.usage # type: ignore
#             prompt_tokens = usage.prompt_tokens
#             completion_tokens = usage.completion_tokens
#             yield 'e:{{"finishReason":"{reason}","usage":{{"promptTokens":{prompt},"completionTokens":{completion}}},"isContinued":false}}\n'.format(
#                 reason="tool-calls" if len(
#                     draft_tool_calls) > 0 else "stop",
#                 prompt=prompt_tokens,
#                 completion=completion_tokens
#             )

# @app.post("/api/chat")
# async def handle_chat_data(request: ChatRequest, protocol: str = Query('data')):
#     messages = request.messages
#     openai_messages = convert_to_openai_messages(messages)
#     response = StreamingResponse(stream_text(openai_messages, protocol))
#     response.headers['x-vercel-ai-data-stream'] = 'v1'
#     return response

class CardDetailsRequest(BaseModel):
    hexColor: str
    colorName: str

@app.post("/api/generate-card-details")
@limiter.limit("10/minute")
async def generate_card_details_route(data: CardDetailsRequest, request: FastAPIRequest):
    """
    Generate AI-based card details using Azure OpenAI.
    This endpoint can be called separately before image generation.
    """
    try:
        hex_color = data.hexColor
        color_name = data.colorName
        
        if not hex_color or not color_name:
            raise HTTPException(status_code=400, detail="Missing required data: hexColor or colorName")
            
        # Validate hex color format
        rgb_color = hex_to_rgb(hex_color)
        if rgb_color is None:
            raise HTTPException(status_code=400, detail=f"Invalid HEX color format: {hex_color}")
            
        # Generate the card details
        card_details = await generate_card_details(color_name, hex_color)
        
        return {
            "success": True,
            "cardDetails": card_details
        }
        
    except HTTPException as e:
        # Re-raise HTTPException
        raise e
    except Exception as e:
        print(f"Error generating card details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate card details: {str(e)}")

# To run locally (ensure uvicorn is installed: pip install uvicorn)
if __name__ == "__main__":
    # Ensure ASSETS_BASE_PATH in card_utils.py is correct for local running
    # If index.py is in /api, and assets are in /assets, card_utils.ASSETS_BASE_PATH might need to be "../assets"
    # Or, ensure the CWD is the project root when running uvicorn.
    # For uvicorn from project root: uvicorn api.index:app --reload
    log("Starting Uvicorn server for local development...")
    uvicorn.run("index:app", app_dir="api", host="0.0.0.0", port=8000, reload=True, reload_dirs=["api"], timeout_keep_alive=75)
