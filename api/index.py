import os
import json
from typing import List, Optional
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, Query, HTTPException, Request as FastAPIRequest
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
# from .utils.prompt import ClientMessage, convert_to_openai_messages # Commented out
# from .utils.tools import get_current_weather # Commented out

import io
import re 
import base64 
from PIL import Image, ImageDraw, ImageFont, ImageOps

# Rate limiting with slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv(".env.local")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

app.state.limiter = limiter # type: ignore
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sf.tinker.institute", "https://sf-livid.vercel.app", "http://localhost:3000"], # Updated production URLs
    allow_credentials=True,
    allow_methods=["POST"], # Restrict methods
    allow_headers=["Content-Type"], # Restrict headers
)

# OpenAI client initialization is kept for future use
# client = OpenAI(
#     api_key=os.environ.get("OPENAI_API_KEY"),
# )

# class ChatRequest(BaseModel):
#     messages: List[ClientMessage]

# --- Color Conversion Utilities (from shadenfreude) ---
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
    c = (c - min_cmy) / (1 - min_cmy)
    m = (m - min_cmy) / (1 - min_cmy)
    y = (y - min_cmy) / (1 - min_cmy)
    k = min_cmy

    return round(c * 100), round(m * 100), round(y * 100), round(k * 100)
# --- End Color Conversion Utilities ---

# --- Font Loading (from shadenfreude) ---
def get_font(size: int, bold: bool = False):
    font_name_suffix = "-Bold" if bold else ""
    try:
        try:
            return ImageFont.truetype(f"DejaVuSans{font_name_suffix}.ttf", size)
        except IOError:
            try: 
                return ImageFont.truetype(f"Arial{font_name_suffix}.ttf", size)
            except IOError:
                try:
                    return ImageFont.truetype(f"Helvetica{font_name_suffix}.ttf", size) 
                except IOError:
                    print(f"Warning: DejaVuSans, Arial, Helvetica not found. Using PIL default.")
                    return ImageFont.load_default()
    except Exception as e:
        print(f"Error loading font: {e}. Using PIL default.")
        return ImageFont.load_default()
# --- End Font Loading ---

class ImageGenerationRequest(BaseModel):
    croppedImageDataUrl: str
    hexColor: str
    colorName: str

@app.post("/api/generate-image")
@limiter.limit("10/minute") # Apply rate limit: 10 requests per minute per IP
async def generate_image_route(data: ImageGenerationRequest, request: FastAPIRequest):
    cropped_image_data_url = data.croppedImageDataUrl
    hex_color_input = data.hexColor
    color_name = data.colorName

    if not cropped_image_data_url or not hex_color_input or not color_name:
        raise HTTPException(status_code=400, detail="Missing required data: croppedImageDataUrl, hexColor, or colorName")

    # Check payload size
    payload_size_mb = len(cropped_image_data_url) / (1024 * 1024)
    if payload_size_mb > 4.5:  # Limit to 4.5MB to stay under 5MB Vercel limit
        raise HTTPException(
            status_code=413, 
            detail=f"Image too large ({payload_size_mb:.1f}MB). Please reduce image size to under 4.5MB."
        )
    
    print(f"Received image data URL size: {payload_size_mb:.2f}MB")
    
    rgb_color = hex_to_rgb(hex_color_input)
    if rgb_color is None:
        raise HTTPException(status_code=400, detail=f"Invalid HEX color format: {hex_color_input}")
    
    cmyk_color = rgb_to_cmyk(rgb_color[0], rgb_color[1], rgb_color[2])
    
    print(f"Input HEX: {hex_color_input}")
    print(f"Converted RGB: {rgb_color}")
    print(f"Converted CMYK: {cmyk_color}")
    print(f"Color Name: {color_name}")

    try:
        print("Attempting to decode base64 image data...")
        if ';base64,' not in cropped_image_data_url:
            print("Error: Invalid image data URL format - missing base64 delimiter.")
            raise HTTPException(status_code=400, detail="Invalid image data URL format")
        header, encoded = cropped_image_data_url.split(';base64,', 1)
        
        try:
            image_data = base64.b64decode(encoded)
        except Exception as e:
            print(f"Base64 decoding error: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to decode base64 image: {str(e)}")
        
        # Validate decoded image data
        if len(image_data) == 0:
            raise HTTPException(status_code=400, detail="Decoded image data is empty")
            
        try:
            img_buffer = io.BytesIO(image_data)
            user_image_pil = Image.open(img_buffer).convert("RGBA")
            print(f"User image decoded successfully. Mode: {user_image_pil.mode}, Size: {user_image_pil.size}")
        except Exception as e:
            print(f"Error opening image data: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to open image data: {str(e)}")

        # Check image dimensions
        if user_image_pil.width > 4000 or user_image_pil.height > 4000:
            print(f"Image too large: {user_image_pil.width}x{user_image_pil.height}")
            # Resize to manageable dimensions
            max_dim = 2000
            ratio = min(max_dim / user_image_pil.width, max_dim / user_image_pil.height)
            new_width = int(user_image_pil.width * ratio)
            new_height = int(user_image_pil.height * ratio)
            user_image_pil = user_image_pil.resize((new_width, new_height), Image.LANCZOS)
            print(f"Resized to: {new_width}x{new_height}")

        # Card dimensions and style
        card_width = 1000
        card_height = 600
        # off-white background (will be masked by swatch and image)
        bg_color = (250, 250, 250)
        # Left swatch covers 45%, right image 55%
        color_swatch_width = int(card_width * 0.45)
        image_panel_x_start = color_swatch_width

        # Create canvas with alpha for rounding
        canvas = Image.new('RGBA', (card_width, card_height), bg_color + (255,))
        draw = ImageDraw.Draw(canvas)

        # Draw the color swatch on the left
        draw.rectangle([(0, 0), (color_swatch_width, card_height)], fill=rgb_color)

        # Determine contrasting text color for swatch
        text_brightness_threshold = 128 * 3
        text_color = (20, 20, 20) if sum(rgb_color) > text_brightness_threshold else (245, 245, 245)

        # Fonts updated to match sample proportions
        font_brand = get_font(80, bold=False)       # shadenfreude title (biggest)
        font_id = get_font(36, bold=False)          # unique ID (normal size)
        font_main_name = get_font(52, bold=True)    # color name (normal size, bold)
        font_color_codes_label = get_font(20, bold=True) # HEX, CMYK, RGB labels (small)
        font_color_codes_value = get_font(20, bold=False) # color values (small)

        # Text positioning - Start from bottom and work our way up
        text_padding_left = 50  # Left padding
        bottom_padding = 50     # Bottom padding

        # Calculate starting Y position from bottom
        # Start with color codes (smallest text at the bottom)
        line_height_codes = (font_color_codes_value.getbbox("ABC")[3] - font_color_codes_value.getbbox("ABC")[1]) + 10
        
        # Calculate position for color codes section (at the bottom)
        label_x = text_padding_left
        value_x = text_padding_left + 70
        
        # Calculate starting y-position from bottom for RGB (last line)
        current_y = card_height - bottom_padding - line_height_codes
        
        # Draw RGB (last line)
        draw.text((label_x, current_y), "RGB", font=font_color_codes_label, fill=text_color)
        draw.text((value_x, current_y), f"{rgb_color[0]} {rgb_color[1]} {rgb_color[2]}", font=font_color_codes_value, fill=text_color)
        
        # Move up for CMYK
        current_y -= line_height_codes
        draw.text((label_x, current_y), "CMYK", font=font_color_codes_label, fill=text_color)
        draw.text((value_x, current_y), f"{cmyk_color[0]} {cmyk_color[1]} {cmyk_color[2]} {cmyk_color[3]}", font=font_color_codes_value, fill=text_color)
        
        # Move up for HEX
        current_y -= line_height_codes
        draw.text((label_x, current_y), "HEX", font=font_color_codes_label, fill=text_color)
        draw.text((value_x, current_y), hex_color_input.upper(), font=font_color_codes_value, fill=text_color)
        
        # Add empty space before color codes
        current_y -= 40
        
        # Draw color name (bold)
        color_name_height = font_main_name.getbbox(color_name.upper())[3] - font_main_name.getbbox(color_name.upper())[1]
        current_y -= color_name_height
        draw.text((text_padding_left, current_y), color_name.upper(), font=font_main_name, fill=text_color)
        
        # Draw sequential ID above color name
        id_height = font_id.getbbox("#00000001 F")[3] - font_id.getbbox("#00000001 F")[1]
        current_y -= id_height + 15
        draw.text((text_padding_left, current_y), "#00000001 F", font=font_id, fill=text_color)
        
        # Draw shadenfreude title at the top of the text block
        brand_height = font_brand.getbbox("shadenfreude")[3] - font_brand.getbbox("shadenfreude")[1]
        current_y -= brand_height + 15
        draw.text((text_padding_left, current_y), "shadenfreude", font=font_brand, fill=text_color)

        # Prepare and paste the right image panel
        print("Preparing and fitting user image for right panel...")
        image_panel_target_width = card_width - image_panel_x_start
        image_panel_target_height = card_height

        user_image_fitted = ImageOps.fit(user_image_pil, 
                                         (image_panel_target_width, image_panel_target_height), 
                                         Image.Resampling.LANCZOS)
        
        # Paste user image
        canvas.paste(user_image_fitted, (image_panel_x_start, 0))
        print("User image pasted onto canvas.")

        # Apply rounded corners to entire card
        print("Applying rounded corners...")
        radius = 40
        mask = Image.new('L', (card_width, card_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (card_width, card_height)], radius=radius, fill=255)
        # Add alpha channel and apply mask
        canvas.putalpha(mask)

        # Save as PNG with transparency
        img_byte_arr = io.BytesIO()
        canvas.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        print("Canvas saved to byte array as PNG.")
        
        print("Sending composed Shadenfreude card image.")
        return StreamingResponse(img_byte_arr, media_type='image/png')

    except HTTPException as e: # Re-raise HTTPException
        raise e
    except Exception as e:
        print(f"Error during image composition: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to compose image: {str(e)}")

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
