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
    c = (c - min_cmy) / (1 - min_cmy)
    m = (m - min_cmy) / (1 - min_cmy)
    y = (y - min_cmy) / (1 - min_cmy)
    k = min_cmy

    return round(c * 100), round(m * 100), round(y * 100), round(k * 100)
# --- End Color Conversion Utilities ---

# --- Font Loading (from shadefreude) ---
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
    orientation: str = "vertical"  # Default to vertical if not specified

@app.post("/api/generate-image")
@limiter.limit("10/minute") # Apply rate limit: 10 requests per minute per IP
async def generate_image_route(data: ImageGenerationRequest, request: FastAPIRequest):
    cropped_image_data_url = data.croppedImageDataUrl
    hex_color_input = data.hexColor
    color_name = data.colorName
    orientation = data.orientation

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
    print(f"Orientation: {orientation}")
    
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
        # Define base dimensions
        BASE_CARD_WIDTH = 1000
        BASE_CARD_HEIGHT = 600
        
        # IMPORTANT: Set correct dimensions based on orientation
        if orientation.lower() == "horizontal":
            # For horizontal card: 600 width x 1000 height
            card_width = BASE_CARD_HEIGHT  # 600
            card_height = BASE_CARD_WIDTH  # 1000
            print(f"Creating HORIZONTAL card: {card_width}x{card_height}")
        else:  # vertical or default
            # For vertical card: 1000 width x 600 height
            card_width = BASE_CARD_WIDTH   # 1000
            card_height = BASE_CARD_HEIGHT # 600
            print(f"Creating VERTICAL card: {card_width}x{card_height}")
            
        # off-white background (will be masked by swatch and image)
        bg_color = (250, 250, 250) # This is for the canvas before rounded corners only

        # Create canvas with the correct dimensions
        canvas = Image.new('RGBA', (card_width, card_height), bg_color + (255,)) # Use bg_color for canvas base
        draw = ImageDraw.Draw(canvas)
        
        if orientation.lower() == "horizontal":
            # HORIZONTAL CARD: 600px width x 1000px height
            # Top section: Color swatch with all text (similar to vertical's left panel)
            # Bottom section: User image

            # Define height for the top color/text panel (e.g., 45% of total card height)
            top_panel_height = int(card_height * 0.45) # 45% of 1000px = 450px
            image_panel_y_start = top_panel_height

            # 1. Top Color/Text Panel Background (uses the selected rgb_color)
            draw.rectangle([(0, 0), (card_width, top_panel_height)], fill=rgb_color)

            # --- Text for Top Panel (similar to vertical's swatch text) ---
            text_color_on_swatch = (20, 20, 20) if sum(rgb_color) > 128 * 3 else (245, 245, 245)
            
            # Adjust font sizes for the 600px width of this panel
            font_brand_h = get_font(70, bold=False) 
            font_id_h = get_font(32, bold=False)
            font_name_h = get_font(48, bold=True)
            font_metrics_label_h = get_font(18, bold=True)
            font_metrics_value_h = get_font(18, bold=False)
            
            text_padding_left_h = 40
            bottom_padding_h = 30 # Padding from the bottom of the top_panel_height
            line_height_metrics_h = font_metrics_value_h.getmask("A").size[1] + 10
            
            label_x_h = text_padding_left_h
            value_x_h = text_padding_left_h + 60 
            
            current_y_h = top_panel_height - bottom_padding_h - font_metrics_value_h.getmask("A").size[1]
            
            draw.text((label_x_h, current_y_h), "RGB", font=font_metrics_label_h, fill=text_color_on_swatch)
            draw.text((value_x_h, current_y_h), f"{rgb_color[0]} {rgb_color[1]} {rgb_color[2]}", font=font_metrics_value_h, fill=text_color_on_swatch)
            current_y_h -= line_height_metrics_h
            
            draw.text((label_x_h, current_y_h), "CMYK", font=font_metrics_label_h, fill=text_color_on_swatch)
            draw.text((value_x_h, current_y_h), f"{cmyk_color[0]} {cmyk_color[1]} {cmyk_color[2]} {cmyk_color[3]}", font=font_metrics_value_h, fill=text_color_on_swatch)
            current_y_h -= line_height_metrics_h
            
            draw.text((label_x_h, current_y_h), "HEX", font=font_metrics_label_h, fill=text_color_on_swatch)
            draw.text((value_x_h, current_y_h), hex_color_input.upper(), font=font_metrics_value_h, fill=text_color_on_swatch)
            
            current_y_h -= 30 
            
            color_name_text_h = color_name.upper()
            # Check fit for color name, adjust font if necessary
            available_text_width_h = card_width - (2 * text_padding_left_h)
            if font_name_h.getmask(color_name_text_h).size[0] > available_text_width_h:
                font_name_h = get_font(40, bold=True)
                if font_name_h.getmask(color_name_text_h).size[0] > available_text_width_h:
                    font_name_h = get_font(36, bold=True)
            color_name_height_h = font_name_h.getmask(color_name_text_h).size[1]
            current_y_h -= color_name_height_h
            draw.text((text_padding_left_h, current_y_h), color_name_text_h, font=font_name_h, fill=text_color_on_swatch)
            
            id_text_h = "#00000001 F"
            id_height_h = font_id_h.getmask(id_text_h).size[1]
            current_y_h -= (id_height_h + 12) 
            draw.text((text_padding_left_h, current_y_h), id_text_h, font=font_id_h, fill=text_color_on_swatch)
            
            brand_text_h = "shadefreude"
            brand_height_h = font_brand_h.getmask(brand_text_h).size[1]
            current_y_h -= (brand_height_h + 12) 
            draw.text((text_padding_left_h, current_y_h), brand_text_h, font=font_brand_h, fill=text_color_on_swatch)
            # --- End Text for Top Panel ---

            # 2. Bottom Image Panel
            image_panel_width = card_width # Full width of the card (600px)
            image_panel_height = card_height - top_panel_height # Remaining height (1000 - 450 = 550px)
            
            if image_panel_height <=0: 
                image_panel_height = int(card_height * 0.5) 
                image_panel_y_start = card_height - image_panel_height

            user_image_fitted = ImageOps.fit(
                user_image_pil, 
                (image_panel_width, image_panel_height),
                Image.Resampling.LANCZOS
            )
            # Paste image into the bottom panel
            canvas.paste(user_image_fitted, (0, image_panel_y_start), user_image_fitted if user_image_fitted.mode == 'RGBA' else None)

        else:  # VERTICAL CARD (1000x600)
            # Left panel: color swatch with all text 
            # Right panel: full image
            color_swatch_width = int(card_width * 0.45)
            image_panel_x_start = color_swatch_width

            # Draw the color swatch on the left (uses the selected rgb_color)
            draw.rectangle([(0, 0), (color_swatch_width, card_height)], fill=rgb_color)

            text_color_on_swatch = (20, 20, 20) if sum(rgb_color) > 128 * 3 else (245, 245, 245)

            font_brand_v = get_font(80, bold=False)
            font_id_v = get_font(36, bold=False)
            font_name_v = get_font(52, bold=True)
            font_metrics_label_v = get_font(20, bold=True)
            font_metrics_value_v = get_font(20, bold=False)
            
            text_padding_left_v = 50
            bottom_padding_v = 50
            line_height_metrics_v = font_metrics_value_v.getmask("A").size[1] + 10
            
            label_x_v = text_padding_left_v
            value_x_v = text_padding_left_v + 70
            
            current_y_v = card_height - bottom_padding_v - font_metrics_value_v.getmask("A").size[1]
            
            draw.text((label_x_v, current_y_v), "RGB", font=font_metrics_label_v, fill=text_color_on_swatch)
            draw.text((value_x_v, current_y_v), f"{rgb_color[0]} {rgb_color[1]} {rgb_color[2]}", font=font_metrics_value_v, fill=text_color_on_swatch)
            current_y_v -= line_height_metrics_v
            
            draw.text((label_x_v, current_y_v), "CMYK", font=font_metrics_label_v, fill=text_color_on_swatch)
            draw.text((value_x_v, current_y_v), f"{cmyk_color[0]} {cmyk_color[1]} {cmyk_color[2]} {cmyk_color[3]}", font=font_metrics_value_v, fill=text_color_on_swatch)
            current_y_v -= line_height_metrics_v
            
            draw.text((label_x_v, current_y_v), "HEX", font=font_metrics_label_v, fill=text_color_on_swatch)
            draw.text((value_x_v, current_y_v), hex_color_input.upper(), font=font_metrics_value_v, fill=text_color_on_swatch)
            
            current_y_v -= 40
            
            color_name_text_v = color_name.upper()
            color_name_height_v = font_name_v.getmask(color_name_text_v).size[1]
            current_y_v -= color_name_height_v
            draw.text((text_padding_left_v, current_y_v), color_name_text_v, font=font_name_v, fill=text_color_on_swatch)
            
            id_text_v = "#00000001 F"
            id_height_v = font_id_v.getmask(id_text_v).size[1]
            current_y_v -= (id_height_v + 15)
            draw.text((text_padding_left_v, current_y_v), id_text_v, font=font_id_v, fill=text_color_on_swatch)
            
            brand_text_v = "shadefreude"
            brand_height_v = font_brand_v.getmask(brand_text_v).size[1]
            current_y_v -= (brand_height_v + 15)
            draw.text((text_padding_left_v, current_y_v), brand_text_v, font=font_brand_v, fill=text_color_on_swatch)

            # Image panel for vertical
            image_panel_width_v = card_width - color_swatch_width
            image_panel_height_v = card_height
            
            user_image_fitted_v = ImageOps.fit(
                user_image_pil,
                (image_panel_width_v, image_panel_height_v),
                Image.Resampling.LANCZOS
            )
            canvas.paste(user_image_fitted_v, (image_panel_x_start, 0), user_image_fitted_v if user_image_fitted_v.mode == 'RGBA' else None)
        
        print("User image pasted onto canvas.")

        # Apply rounded corners to entire card
        print("Applying rounded corners...")
        radius = 40
        
        # Create a high-quality anti-aliased mask with double resolution for better edge quality
        scale_factor = 2
        mask_size = (card_width * scale_factor, card_height * scale_factor)
        mask = Image.new('L', mask_size, 0)
        mask_draw = ImageDraw.Draw(mask)
        
        # Draw the rounded rectangle with scaled radius
        mask_draw.rounded_rectangle([(0, 0), (mask_size[0] - 1, mask_size[1] - 1)], 
                                    radius=radius * scale_factor, 
                                    fill=255)
        
        # Resize back to original dimensions with high-quality anti-aliasing
        mask = mask.resize((card_width, card_height), Image.Resampling.LANCZOS)
        
        # Apply mask with improved edge quality by using a pre-multiplied alpha technique
        r, g, b, a = canvas.split()
        rgba = Image.merge('RGBA', (r, g, b, mask))
        
        # This premultiplied alpha blending yields sharper edges
        canvas = rgba.copy()
        
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
