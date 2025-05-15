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
    orientation: str = "vertical"
    # New text fields for the card, all optional for now
    cardName: Optional[str] = "OLIVE ALPINE SENTINEL" # Placeholder
    phoneticName: Optional[str] = "['ɒlɪv 'ælpaɪn 'sɛntɪnəl]" # Placeholder
    article: Optional[str] = "[noun]" # Placeholder
    description: Optional[str] = "A steadfast guardian of high mountain terrain, its resilience mirrored in a deep olive-brown hue. Conveys calm vigilance, endurance, and earthy warmth at altitude." # Placeholder
    cardId: Optional[str] = "00000001 F" # Placeholder
    # colorName is effectively cardName now, but we keep it for compatibility if frontend sends it
    colorName: Optional[str] = "DARK EMBER"

@app.post("/api/generate-image")
@limiter.limit("10/minute") # Apply rate limit: 10 requests per minute per IP
async def generate_image_route(data: ImageGenerationRequest, request: FastAPIRequest):
    cropped_image_data_url = data.croppedImageDataUrl
    hex_color_input = data.hexColor
    orientation = data.orientation

    # Use new text fields from request or fallback to existing colorName for the main name
    card_name_text = data.cardName if data.cardName else data.colorName
    phonetic_name_text = data.phoneticName
    article_text = data.article
    description_text = data.description
    card_id_text = data.cardId
    
    if not cropped_image_data_url or not hex_color_input:
        raise HTTPException(status_code=400, detail="Missing required data: croppedImageDataUrl or hexColor")

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
    
    cmyk_color_tuple = rgb_to_cmyk(rgb_color[0], rgb_color[1], rgb_color[2])
    
    print(f"Input HEX: {hex_color_input}")
    print(f"Converted RGB: {rgb_color}")
    print(f"Converted CMYK: {cmyk_color_tuple}")
    print(f"Color Name: {card_name_text}")

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

        # Card dimensions and style
        # Define base dimensions
        BASE_CARD_WIDTH = 1500
        BASE_CARD_HEIGHT = 900
        
        # IMPORTANT: Set correct dimensions based on orientation
        if orientation.lower() == "horizontal":
            # For horizontal card: 1500x900
            card_width = BASE_CARD_HEIGHT  # 1500
            card_height = BASE_CARD_WIDTH  # 900

            # Top 50% is color swatch with text, Bottom 50% is image
            text_panel_width = card_width
            text_panel_height = card_height // 2
            text_panel_x_offset = 0
            text_panel_y_offset = 0
            image_panel_width = card_width
            image_panel_height = card_height - text_panel_height
            image_panel_x_offset = 0
            image_panel_y_offset = text_panel_height

            print(f"Creating HORIZONTAL card: {card_width}x{card_height}")
        else:  # vertical or default
            # For vertical card: 900x1500
            card_width = BASE_CARD_WIDTH  # 900
            card_height = BASE_CARD_HEIGHT  # 1500

            # Left 50% is color swatch with text, Right 50% is image
            text_panel_width = card_width // 2
            text_panel_height = card_height
            text_panel_x_offset = 0
            text_panel_y_offset = 0
            image_panel_width = card_width - text_panel_width
            image_panel_height = card_height
            image_panel_x_offset = text_panel_width
            image_panel_y_offset = 0

            print(f"Creating VERTICAL card: {card_width}x{card_height}")
            
        # off-white background (will be masked by swatch and image)
        bg_color = (250, 250, 250) # This is for the canvas before rounded corners only

        # Create canvas with the correct dimensions
        canvas = Image.new('RGBA', (card_width, card_height), (250, 250, 250, 255)) # Use bg_color for canvas base
        draw = ImageDraw.Draw(canvas)
        
        # 1. Draw the color swatch panel (uses the selected rgb_color)
        draw.rectangle(
            [(text_panel_x_offset, text_panel_y_offset), 
             (text_panel_x_offset + text_panel_width, text_panel_y_offset + text_panel_height)], 
            fill=rgb_color
        )

        # Determine text color based on background brightness
        text_color_on_swatch = (20, 20, 20) if sum(rgb_color) > 128 * 3 else (245, 245, 245)

        # Adjust the text drawing based on orientation
        if orientation.lower() == "horizontal":
            # For horizontal card text layout
            font_brand_h = get_font(70, weight="Bold") 
            font_id_h = get_font(32, weight="Bold")
            font_name_h = get_font(48, weight="Bold")
            font_metrics_label_h = get_font(18, weight="Bold")
            font_metrics_value_h = get_font(18, weight="Regular")
            
            text_padding_left_h = 40
            bottom_padding_h = 30 # Padding from the bottom of the text_panel_height
            line_height_metrics_h = get_text_dimensions("X", font_metrics_value_h)[1] + 10
            
            label_x_h = text_panel_x_offset + text_padding_left_h
            value_x_h = text_panel_x_offset + text_padding_left_h + 60 
            
            current_y_h = text_panel_y_offset + text_panel_height - bottom_padding_h - get_text_dimensions("X", font_metrics_value_h)[1]
            
            draw.text((label_x_h, current_y_h), "RGB", font=font_metrics_label_h, fill=text_color_on_swatch)
            draw.text((value_x_h, current_y_h), f"{rgb_color[0]} {rgb_color[1]} {rgb_color[2]}", font=font_metrics_value_h, fill=text_color_on_swatch)
            current_y_h -= line_height_metrics_h
            
            draw.text((label_x_h, current_y_h), "CMYK", font=font_metrics_label_h, fill=text_color_on_swatch)
            draw.text((value_x_h, current_y_h), f"{cmyk_color_tuple[0]} {cmyk_color_tuple[1]} {cmyk_color_tuple[2]} {cmyk_color_tuple[3]}", font=font_metrics_value_h, fill=text_color_on_swatch)
            current_y_h -= line_height_metrics_h
            
            draw.text((label_x_h, current_y_h), "HEX", font=font_metrics_label_h, fill=text_color_on_swatch)
            draw.text((value_x_h, current_y_h), hex_color_input.upper(), font=font_metrics_value_h, fill=text_color_on_swatch)
            
            current_y_h -= 30 
            
            color_name_text_h = card_name_text.upper()
            # Check fit for color name, adjust font if necessary
            available_text_width_h = text_panel_width - (2 * text_padding_left_h)
            if get_text_dimensions(color_name_text_h, font_name_h)[0] > available_text_width_h:
                font_name_h = get_font(40, weight="Bold")
                if get_text_dimensions(color_name_text_h, font_name_h)[0] > available_text_width_h:
                    font_name_h = get_font(36, weight="Bold")
            color_name_height_h = get_text_dimensions(color_name_text_h, font_name_h)[1]
            current_y_h -= color_name_height_h
            draw.text((text_panel_x_offset + text_padding_left_h, current_y_h), color_name_text_h, font=font_name_h, fill=text_color_on_swatch)
            
            id_text_h = card_id_text
            id_height_h = get_text_dimensions(id_text_h, font_id_h)[1]
            current_y_h -= (id_height_h + 12) 
            draw.text((text_panel_x_offset + text_padding_left_h, current_y_h), id_text_h, font=font_id_h, fill=text_color_on_swatch)
            
            brand_text_h = "shadefreude"
            brand_height_h = get_text_dimensions(brand_text_h, font_brand_h)[1]
            current_y_h -= (brand_height_h + 12) 
            draw.text((text_panel_x_offset + text_padding_left_h, current_y_h), brand_text_h, font=font_brand_h, fill=text_color_on_swatch)

            # Also add phonetic name and article text if provided
            if phonetic_name_text:
                current_y_h -= 20  # Some extra spacing
                draw.text((text_panel_x_offset + text_padding_left_h, current_y_h), phonetic_name_text, 
                          font=get_font(30, weight="Regular", style="Italic"), fill=text_color_on_swatch)
                if article_text:
                    current_y_h += get_text_dimensions(phonetic_name_text, get_font(30, weight="Regular", style="Italic"))[1] + 10
                    draw.text((text_panel_x_offset + text_padding_left_h, current_y_h), article_text,
                              font=get_font(30, weight="Regular"), fill=text_color_on_swatch)
            
            # Add description if provided
            if description_text:
                font_desc = get_font(24, weight="Regular")
                desc_y = text_panel_y_offset + 50  # Start from top with padding
                
                # Word wrap description
                words = description_text.split()
                line = ""
                for word in words:
                    test_line = line + (" " if line else "") + word
                    if get_text_dimensions(test_line, font_desc)[0] <= available_text_width_h:
                        line = test_line
                    else:
                        draw.text((text_panel_x_offset + text_padding_left_h, desc_y), line, font=font_desc, fill=text_color_on_swatch)
                        desc_y += get_text_dimensions(line, font_desc)[1] + 5  # Line spacing
                        line = word
                
                # Draw last line
                if line:
                    draw.text((text_panel_x_offset + text_padding_left_h, desc_y), line, font=font_desc, fill=text_color_on_swatch)
        else:
            # For vertical card text layout
            font_brand_v = get_font(80, weight="Bold")
            font_id_v = get_font(36, weight="Bold")
            font_name_v = get_font(52, weight="Bold")
            font_metrics_label_v = get_font(20, weight="Bold")
            font_metrics_value_v = get_font(20, weight="Regular")
            
            text_padding_left_v = 30  # Decreased for narrower panel (50%)
            bottom_padding_v = 50
            line_height_metrics_v = get_text_dimensions("X", font_metrics_value_v)[1] + 10
            
            label_x_v = text_panel_x_offset + text_padding_left_v
            value_x_v = text_panel_x_offset + text_padding_left_v + 70
            
            current_y_v = text_panel_y_offset + text_panel_height - bottom_padding_v - get_text_dimensions("X", font_metrics_value_v)[1]
            
            draw.text((label_x_v, current_y_v), "RGB", font=font_metrics_label_v, fill=text_color_on_swatch)
            draw.text((value_x_v, current_y_v), f"{rgb_color[0]} {rgb_color[1]} {rgb_color[2]}", font=font_metrics_value_v, fill=text_color_on_swatch)
            current_y_v -= line_height_metrics_v
            
            draw.text((label_x_v, current_y_v), "CMYK", font=font_metrics_label_v, fill=text_color_on_swatch)
            draw.text((value_x_v, current_y_v), f"{cmyk_color_tuple[0]} {cmyk_color_tuple[1]} {cmyk_color_tuple[2]} {cmyk_color_tuple[3]}", font=font_metrics_value_v, fill=text_color_on_swatch)
            current_y_v -= line_height_metrics_v
            
            draw.text((label_x_v, current_y_v), "HEX", font=font_metrics_label_v, fill=text_color_on_swatch)
            draw.text((value_x_v, current_y_v), hex_color_input.upper(), font=font_metrics_value_v, fill=text_color_on_swatch)
            
            current_y_v -= 40
            
            color_name_text_v = card_name_text.upper()
            available_text_width_v = text_panel_width - (2 * text_padding_left_v)
            
            # Check if name fits, use smaller font if needed
            if get_text_dimensions(color_name_text_v, font_name_v)[0] > available_text_width_v:
                font_name_v = get_font(42, weight="Bold")
                if get_text_dimensions(color_name_text_v, font_name_v)[0] > available_text_width_v:
                    font_name_v = get_font(36, weight="Bold")
            
            color_name_height_v = get_text_dimensions(color_name_text_v, font_name_v)[1]
            current_y_v -= color_name_height_v
            draw.text((text_panel_x_offset + text_padding_left_v, current_y_v), color_name_text_v, font=font_name_v, fill=text_color_on_swatch)
            
            id_text_v = card_id_text
            id_height_v = get_text_dimensions(id_text_v, font_id_v)[1]
            current_y_v -= (id_height_v + 15)
            draw.text((text_panel_x_offset + text_padding_left_v, current_y_v), id_text_v, font=font_id_v, fill=text_color_on_swatch)
            
            brand_text_v = "shadefreude"
            brand_height_v = get_text_dimensions(brand_text_v, font_brand_v)[1]
            current_y_v -= (brand_height_v + 15)
            draw.text((text_panel_x_offset + text_padding_left_v, current_y_v), brand_text_v, font=font_brand_v, fill=text_color_on_swatch)

            # Also add phonetic name and article text if provided
            if phonetic_name_text:
                current_y_v -= 20  # Some extra spacing
                phonetic_font = get_font(32, weight="Regular", style="Italic")
                draw.text((text_panel_x_offset + text_padding_left_v, current_y_v), phonetic_name_text, 
                          font=phonetic_font, fill=text_color_on_swatch)
                if article_text:
                    current_y_v += get_text_dimensions(phonetic_name_text, phonetic_font)[1] + 10
                    draw.text((text_panel_x_offset + text_padding_left_v, current_y_v), article_text,
                              font=get_font(32, weight="Regular"), fill=text_color_on_swatch)
            
            # Add description if provided
            if description_text:
                font_desc = get_font(26, weight="Regular")
                desc_y = text_panel_y_offset + 50  # Start from top with padding
                
                # Word wrap description
                words = description_text.split()
                line = ""
                for word in words:
                    test_line = line + (" " if line else "") + word
                    if get_text_dimensions(test_line, font_desc)[0] <= available_text_width_v:
                        line = test_line
                    else:
                        draw.text((text_panel_x_offset + text_padding_left_v, desc_y), line, font=font_desc, fill=text_color_on_swatch)
                        desc_y += get_text_dimensions(line, font_desc)[1] + 5  # Line spacing
                        line = word
                
                # Draw last line
                if line:
                    draw.text((text_panel_x_offset + text_padding_left_v, desc_y), line, font=font_desc, fill=text_color_on_swatch)

        # 2. Paste the user image into the image panel
        user_image_fitted = ImageOps.fit(
            user_image_pil, 
            (image_panel_width, image_panel_height),
            Image.Resampling.LANCZOS
        )
        canvas.paste(user_image_fitted, (image_panel_x_offset, image_panel_y_offset), user_image_fitted if user_image_fitted.mode == 'RGBA' else None)

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
