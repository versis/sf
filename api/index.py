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
def get_font(size: int, weight: str = "Regular", style: str = "Normal"):
    """
    Loads an Inter font variant.
    Weight: "Regular", "Bold", "Light", "Medium", "SemiBold", "ExtraBold", "Black", "Thin", "ExtraLight"
    Style: "Normal", "Italic"
    """
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
    
    # Match the filename pattern: Inter_XXpt-WeightStyle.ttf
    font_name = f"Inter_{pt_suffix}-{weight}{font_style_suffix}.ttf"
    
    font_paths_to_try = [
        f"api/fonts/{font_name}",          # Primary path where fonts are located
        font_name,                          # Direct name (fallback)
        f"api/{font_name}",                 # In api/ folder (fallback)
        f"assets/fonts/{font_name}",        # In assets/fonts/ folder (fallback)
    ]

    for path_attempt in font_paths_to_try:
        try:
            print(f"Attempting to load font: {path_attempt}")
            return ImageFont.truetype(path_attempt, size)
        except IOError:
            continue # Try next path
    
    # Fallback if all attempts fail
    print(f"Warning: Font '{font_name}' not found in expected paths. Using PIL default for size {size}.")
    try:
        # Try to get a generic PIL default font of a given size
        return ImageFont.truetype("arial.ttf", size) # Common fallback, may not be available
    except IOError:
        return ImageFont.load_default() # Absolute fallback
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

class ImageGenerationRequest(BaseModel):
    croppedImageDataUrl: str
    hexColor: str
    colorName: str
    orientation: str
    # New text fields for the card, all optional for now
    cardName: Optional[str] = "OLIVE ALPINE SENTINEL" # Placeholder
    phoneticName: Optional[str] = "['ɒlɪv 'ælpaɪn 'sɛntɪnəl]" # Placeholder
    article: Optional[str] = "[noun]" # Placeholder
    description: Optional[str] = "A steadfast guardian of high mountain terrain, its resilience mirrored in a deep olive-brown hue. Conveys calm vigilance, endurance, and earthy warmth at altitude." # Placeholder
    cardId: Optional[str] = "00000001 F" # Placeholder

@app.post("/api/generate-image")
@limiter.limit("10/minute")
async def generate_image_route(data: ImageGenerationRequest, request: FastAPIRequest):
    cropped_image_data_url = data.croppedImageDataUrl
    hex_color_input = data.hexColor
    color_name = data.colorName
    orientation = data.orientation

    if not cropped_image_data_url or not hex_color_input or not color_name or not orientation:
        raise HTTPException(status_code=400, detail="Missing required data: croppedImageDataUrl, hexColor, colorName, or orientation")

    # Check payload size
    payload_size_mb = len(cropped_image_data_url) / (1024 * 1024)
    if payload_size_mb > 4.5:  # Limit to 4.5MB to stay under 5MB Vercel limit
        raise HTTPException(
            status_code=413, 
            detail=f"Image too large ({payload_size_mb:.1f}MB). Please reduce image size to under 4.5MB."
        )
    
    print(f"Received image data URL size: {payload_size_mb:.2f}MB")
    print(f"Color Name: {color_name}")
    print(f"Requested Card Orientation: {orientation}")
    
    rgb_color = hex_to_rgb(hex_color_input)
    if rgb_color is None:
        raise HTTPException(status_code=400, detail=f"Invalid HEX color format: {hex_color_input}")
    
    cmyk_color_tuple = rgb_to_cmyk(rgb_color[0], rgb_color[1], rgb_color[2])
    
    print(f"Input HEX: {hex_color_input}")
    print(f"Converted RGB: {rgb_color}")
    print(f"Converted CMYK: {cmyk_color_tuple}")

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
            max_dim = 4000
            ratio = min(max_dim / user_image_pil.width, max_dim / user_image_pil.height)
            new_width = int(user_image_pil.width * ratio)
            new_height = int(user_image_pil.height * ratio)
            user_image_pil = user_image_pil.resize((new_width, new_height), Image.LANCZOS)
            print(f"Resized to: {new_width}x{new_height}")

        bg_color = (250, 250, 250)
        card_width, card_height = 0, 0
        swatch_panel_width, swatch_panel_height = 0, 0
        image_panel_width, image_panel_height = 0, 0

        if orientation.lower() == "horizontal":
            card_width, card_height = 1500, 900
            swatch_panel_width = int(card_width * 0.50)  # 750px
            swatch_panel_height = card_height          # 900px (full height for left panel)
            image_panel_width = card_width - swatch_panel_width # 750px
            image_panel_height = card_height         # 900px (full height for right panel)
            print(f"Generating HORIZONTAL card ({card_width}x{card_height}) -> Swatch: {swatch_panel_width}x{swatch_panel_height}, Image: {image_panel_width}x{image_panel_height}")
        elif orientation.lower() == "vertical":
            card_width, card_height = 750, 1800
            swatch_panel_width = int(card_width * 0.50) # 375px
            swatch_panel_height = card_height         # 1800px (full height for left panel)
            image_panel_width = card_width - swatch_panel_width # 375px
            image_panel_height = card_height        # 1800px (full height for right panel)
            print(f"Generating VERTICAL card ({card_width}x{card_height}) -> Swatch: {swatch_panel_width}x{swatch_panel_height}, Image: {image_panel_width}x{image_panel_height}")
        else:
            raise HTTPException(status_code=400, detail=f"Invalid orientation specified: {orientation}. Must be 'horizontal' or 'vertical'.")

        canvas = Image.new('RGBA', (card_width, card_height), bg_color + (255,))
        draw = ImageDraw.Draw(canvas)
        # Swatch is always on the left
        draw.rectangle([(0, 0), (swatch_panel_width, swatch_panel_height)], fill=rgb_color)

        text_color_on_swatch = (20, 20, 20) if sum(rgb_color) > 128 * 3 else (245, 245, 245)

        # --- Text Layout for Swatch Panel (Left side) ---
        # This logic needs to be adaptable to swatch_panel_width and swatch_panel_height
        # For simplicity, using generic padding and font scaling. Refine as needed.
        
        text_padding_top = int(swatch_panel_height * 0.05) # Relative padding
        text_padding_left = int(swatch_panel_width * 0.1)
        text_padding_bottom = int(swatch_panel_height * 0.05)
        line_spacing_major_scale = 0.015 # Scale factor for line spacing based on swatch height
        line_spacing_minor_scale = 0.008

        # Dynamically adjust font sizes based on swatch panel width (more critical dimension for text lines)
        base_font_size_scale = swatch_panel_width / 400 # Adjust 400 to find a good base

        current_y = text_padding_top
        font_color_name = get_font(int(50 * base_font_size_scale), weight="Bold")
        font_noun = get_font(int(22 * base_font_size_scale), weight="Regular")
        font_description = get_font(int(18 * base_font_size_scale), weight="Regular")

        main_color_name_str = color_name.upper()
        # Basic text wrapping for main_color_name_str
        wrapped_color_name_lines = []
        temp_line_color = ""
        for word in main_color_name_str.split(' '):
            if font_color_name.getmask(temp_line_color + word).size[0] <= (swatch_panel_width - 2 * text_padding_left):
                temp_line_color += word + " "
            else:
                wrapped_color_name_lines.append(temp_line_color.strip())
                temp_line_color = word + " "
        wrapped_color_name_lines.append(temp_line_color.strip())
        
        for line in wrapped_color_name_lines:
            draw.text((text_padding_left, current_y), line, font=font_color_name, fill=text_color_on_swatch)
            current_y += font_color_name.getmask(line).size[1] + int(swatch_panel_height * line_spacing_minor_scale)

        noun_str = "[noun]"
        if color_name.upper() == "OLIVE ALPINE SENTINEL":
            noun_str = "[ɒlɪv ælpaɪn sɛntɪnəl]"
        draw.text((text_padding_left, current_y), noun_str, font=font_noun, fill=text_color_on_swatch)
        current_y += font_noun.getmask(noun_str).size[1] + int(swatch_panel_height * line_spacing_major_scale)

        description_text = "A steadfast guardian of high mountain terrain, its resilience mirrored in a deep olive-brown hue. Conveys calm vigilance, endurance, and earthy warmth at altitude."
        desc_line_height = font_description.getmask("Tg").size[1]
        max_desc_width = swatch_panel_width - (2 * text_padding_left)
        wrapped_desc_lines = []
        current_desc_line = ""
        for word in description_text.split(' '):
            if font_description.getmask(current_desc_line + word).size[0] <= max_desc_width:
                current_desc_line += word + " "
            else:
                wrapped_desc_lines.append(current_desc_line.strip())
                current_desc_line = word + " "
        wrapped_desc_lines.append(current_desc_line.strip())
        
        for line in wrapped_desc_lines:
            if current_y + desc_line_height < swatch_panel_height - text_padding_bottom - (swatch_panel_height * 0.15): # Reserve ~15% bottom for metrics etc
                draw.text((text_padding_left, current_y), line, font=font_description, fill=text_color_on_swatch)
                current_y += desc_line_height + int(swatch_panel_height * line_spacing_minor_scale)
            else:
                break 

        # Bottom-aligned text: Brand, ID, Metrics
        font_brand_bottom = get_font(int(30 * base_font_size_scale), weight="Bold" if orientation.lower()!="horizontal" else "Regular") # Bold for vertical, Regular for horizontal 
        font_id_bottom = get_font(int(30 * base_font_size_scale), weight="Regular")
        font_metrics_label = get_font(int(16 * base_font_size_scale), weight="Bold")
        font_metrics_value = get_font(int(16 * base_font_size_scale), weight="Regular")
        metrics_line_height = font_metrics_value.getmask("Tg").size[1] + int(swatch_panel_height * 0.005) # Small gap

        brand_text = "shadefreude"
        id_text = "00000001F"
        
        # Metrics are drawn from bottom up
        current_metrics_y = swatch_panel_height - text_padding_bottom - font_metrics_value.getmask("Tg").size[1]
        metrics_label_x = text_padding_left
        metrics_value_x = text_padding_left + int(swatch_panel_width * 0.2) # Offset values from labels

        draw.text((metrics_label_x, current_metrics_y), "RGB", font=font_metrics_label, fill=text_color_on_swatch)
        draw.text((metrics_value_x, current_metrics_y), f"{rgb_color[0]} {rgb_color[1]} {rgb_color[2]}", font=font_metrics_value, fill=text_color_on_swatch)
        current_metrics_y -= metrics_line_height
        draw.text((metrics_label_x, current_metrics_y), "CMYK", font=font_metrics_label, fill=text_color_on_swatch)
        draw.text((metrics_value_x, current_metrics_y), f"{cmyk_color_tuple[0]} {cmyk_color_tuple[1]} {cmyk_color_tuple[2]} {cmyk_color_tuple[3]}", font=font_metrics_value, fill=text_color_on_swatch)
        current_metrics_y -= metrics_line_height
        draw.text((metrics_label_x, current_metrics_y), "HEX", font=font_metrics_label, fill=text_color_on_swatch)
        draw.text((metrics_value_x, current_metrics_y), hex_color_input.upper(), font=font_metrics_value, fill=text_color_on_swatch)

        # ID text above metrics
        id_y_pos = current_metrics_y - metrics_line_height - font_id_bottom.getmask(id_text).size[1] 
        draw.text((text_padding_left, id_y_pos), id_text, font=font_id_bottom, fill=text_color_on_swatch)

        # Brand text above ID
        brand_actual_height = font_brand_bottom.getmask(brand_text).size[1]
        brand_y_pos = id_y_pos - brand_actual_height - int(swatch_panel_height * 0.01) # Small gap
        draw.text((text_padding_left, brand_y_pos), brand_text, font=font_brand_bottom, fill=text_color_on_swatch)
        
        # Image panel is always on the right of the swatch panel
        user_image_fitted = ImageOps.fit(user_image_pil, (image_panel_width, image_panel_height), Image.Resampling.LANCZOS)
        canvas.paste(user_image_fitted, (swatch_panel_width, 0), user_image_fitted if user_image_fitted.mode == 'RGBA' else None)
    
        print("User image pasted onto canvas.")
        # Apply rounded corners to entire card
        print("Applying rounded corners...")
        radius = 40
        
        # Create a high-quality anti-aliased mask
        mask = Image.new('L', (card_width * 2, card_height * 2), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0,0), ((card_width*2)-1, (card_height*2)-1)], radius=radius*2, fill=255)
        mask = mask.resize((card_width, card_height), Image.Resampling.LANCZOS)
        
        # Apply mask to the canvas
        # Ensure canvas is RGBA before putting alpha mask
        if canvas.mode != 'RGBA':
            canvas = canvas.convert('RGBA')
        canvas.putalpha(mask)
        
        # Save as PNG with transparency
        img_byte_arr = io.BytesIO()
        # Use higher quality settings for PNG
        canvas.save(img_byte_arr, format='PNG', compress_level=1)
        img_byte_arr.seek(0)
        print("Canvas saved to byte array as PNG with improved edge quality.")
        
        print("Sending composed Shadefreude card image.")
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
