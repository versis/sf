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
def get_font(size: int, weight: str = "Regular", style: str = "Normal", font_family: str = "Inter"):
    """
    Loads a font variant.
    font_family: "Inter" (default) or "Mono" for monospace
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
    
    if font_family == "Mono":
        # Try common monospace fonts that support IPA symbols
        monospace_fonts = ["DejaVu Sans Mono", "Courier New", "Consolas", "Liberation Mono"]
        for mono_font in monospace_fonts:
            try:
                return ImageFont.truetype(mono_font, size)
            except IOError:
                continue
    
    # Match the filename pattern: Inter_XXpt-WeightStyle.ttf
    font_name = f"Inter_{pt_suffix}-{weight}{font_style_suffix}.ttf"
    
    font_paths_to_try = [
        f"api/fonts/{font_name}",          # Primary path where fonts are located
        font_name,                          # Direct name (fallback)
        f"api/{font_name}",                 # In api/ folder (fallback)
        f"assets/fonts/{font_name}",        # In assets/fonts/ folder (fallback)
    ]

    loaded_font = None
    for path_attempt in font_paths_to_try:
        try:
            print(f"Attempting to load font: {path_attempt}")
            loaded_font = ImageFont.truetype(path_attempt, size)
            print(f"Successfully loaded font: {path_attempt}")
            return loaded_font
        except IOError as e:
            print(f"Failed to load font {path_attempt}: {e}")
            continue # Try next path
    
    # Fallback if all attempts fail - try to find any Inter font
    if not loaded_font:
        generic_inter_paths = [
            "api/fonts/Inter.ttf",
            "api/fonts/Inter-Regular.ttf",
            "assets/fonts/Inter.ttf"
        ]
        
        for path in generic_inter_paths:
            try:
                print(f"Trying generic Inter font: {path}")
                return ImageFont.truetype(path, size)
            except IOError:
                continue
    
    # Last resort - system fonts
    print(f"Warning: Font '{font_name}' not found in any expected paths. Using system fallback.")
    try:
        # Try common system fonts that support IPA
        for system_font in ["Arial Unicode MS", "DejaVu Sans", "Arial", "Helvetica", "Tahoma"]:
            try:
                print(f"Trying system font: {system_font}")
                return ImageFont.truetype(system_font, size)
            except IOError:
                continue
                
        # Last resort - PIL default
        print("Using PIL default font as last resort")
        return ImageFont.load_default()
    except Exception as e:
        print(f"Error loading any font: {e}")
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

        # Card dimensions and style
        VERTICAL_CARD_W, VERTICAL_CARD_H = 900, 1800 # Adjusted Vertical Card Dimensions
        HORIZONTAL_CARD_W, HORIZONTAL_CARD_H = 1800, 900 # Adjusted Horizontal Card Dimensions
        bg_color = (250, 250, 250)

        if orientation.lower() == "horizontal":
            card_width, card_height = HORIZONTAL_CARD_W, HORIZONTAL_CARD_H
            print(f"Creating HORIZONTAL card: {card_width}x{card_height}")

            swatch_panel_width = int(card_width * 0.50)  # 900px
            swatch_panel_height = card_height          # 900px (full height for left panel)
            image_panel_width = card_width - swatch_panel_width # 900px
            image_panel_height = card_height         # 900px (full height for right panel)
            print(f" HORIZONTAL Swatch: {swatch_panel_width}x{swatch_panel_height}, Image Panel: {image_panel_width}x{image_panel_height}")

        elif orientation.lower() == "vertical":
            card_width, card_height = VERTICAL_CARD_W, VERTICAL_CARD_H # 900x1800
            print(f"Creating VERTICAL card: {card_width}x{card_height}")

            # Vertical: Top Swatch, Bottom Image
            swatch_panel_width = card_width # Full width: 900px
            swatch_panel_height = int(card_height * 0.50) # Top half: 900px height
            image_panel_width = card_width  # Full width: 900px
            image_panel_height = card_height - swatch_panel_height # Bottom half: 900px height
            print(f" VERTICAL Swatch: {swatch_panel_width}x{swatch_panel_height}, Image Panel: {image_panel_width}x{image_panel_height}")
        else:
            raise HTTPException(status_code=400, detail=f"Invalid orientation specified: {orientation}. Must be 'horizontal' or 'vertical'.")

        canvas = Image.new('RGBA', (card_width, card_height), bg_color + (255,))
        draw = ImageDraw.Draw(canvas)
        
        # Draw swatch panel based on orientation
        if orientation.lower() == "horizontal":
            # Horizontal: Swatch is on the LEFT
            draw.rectangle([(0, 0), (swatch_panel_width, swatch_panel_height)], fill=rgb_color)
        else: # Vertical: Swatch is on the TOP
            draw.rectangle([(0, 0), (swatch_panel_width, swatch_panel_height)], fill=rgb_color)

        text_color_on_swatch = (20, 20, 20) if sum(rgb_color) > 128 * 3 else (245, 245, 245)

        # --- Text Layout for Swatch Panel ---
        # This logic is now applied to the swatch panel which is either left (horizontal) or top (vertical)
        # swatch_panel_width and swatch_panel_height define the area for text.
        text_padding_top = int(swatch_panel_height * 0.05) 
        text_padding_left = int(swatch_panel_width * 0.1)
        text_padding_bottom = int(swatch_panel_height * 0.05)
        line_spacing_major_scale = 0.015 
        line_spacing_minor_scale = 0.008

        if swatch_panel_width == 0: swatch_panel_width = 1 # Avoid division by zero for base_font_size_scale
        if swatch_panel_width >= 900: 
            base_font_size_scale = swatch_panel_width / 750 # Adjusted for wider horizontal swatch
        elif swatch_panel_width >= 450: 
            base_font_size_scale = swatch_panel_width / 450 # For vertical swatch (width 900 -> scale becomes 2)
                                                          # Or horizontal swatch if it was narrower (width 750 -> scale ~1.6)
        else: 
            base_font_size_scale = swatch_panel_width / 350

        current_y = text_padding_top

        # --- Top Section: Color Name, Phonetic/Noun, Description ---
        font_color_name = get_font(int(45 * base_font_size_scale), weight="Bold") # Reduce title size to match goal design
        font_phonetic_noun = get_font(int(18 * base_font_size_scale), weight="Regular", font_family="Mono", style="Italic") # Use italic for phonetic
        font_article = get_font(int(18 * base_font_size_scale), weight="Regular", font_family="Mono") # Regular style for article
        font_description = get_font(int(16 * base_font_size_scale), weight="Regular") # Smaller description

        # Define brand-related fonts early
        font_brand_main = get_font(int(60 * base_font_size_scale), weight="Bold") # Smaller brand text to match goal
        font_id_main = get_font(int(26 * base_font_size_scale), weight="Regular") # Slightly smaller ID text
        font_metrics_label_main = get_font(int(16 * base_font_size_scale), weight="Bold", font_family="Mono") # Monospace metrics labels
        font_metrics_value_main = get_font(int(16 * base_font_size_scale), weight="Regular", font_family="Mono") # Monospace metrics values

        # Pre-calculate brand position to determine space available for other elements
        brand_text = "shadefreude"
        id_text = data.cardId if data.cardId and data.cardId.strip() else "00000001 F"
        brand_w, brand_h = get_text_dimensions(brand_text, font_brand_main)
        id_h = get_text_dimensions(id_text, font_id_main)[1]
        metrics_line_spacing = int(swatch_panel_height * 0.015) # Slightly increase line spacing for metrics

        # Position brand at bottom left, closer to bottom
        brand_y = swatch_panel_height - text_padding_bottom - id_h - metrics_line_spacing - brand_h - int(swatch_panel_height * 0.01)

        # Now handle the title formatting
        main_color_name_str = color_name.upper()
        words = main_color_name_str.split()

        # Add spacing between lines
        current_y += int(swatch_panel_height * 0.04) # Push title down a bit

        # Handle each word separately, one per line
        for word in words:
            draw.text((text_padding_left, current_y), word, font=font_color_name, fill=text_color_on_swatch)
            current_y += get_text_dimensions(word, font_color_name)[1] + int(swatch_panel_height * 0.01)

        # Extra spacing after title
        current_y += int(swatch_panel_height * 0.02)

        # Format phonetic text to match monospaced italic style in goal design
        phonetic_str = data.phoneticName.strip() if data.phoneticName and data.phoneticName.strip() else "[ɒlɪv ælpaɪn sɛntɪnəl]"
        if not phonetic_str.startswith('['):
            phonetic_str = f"[{phonetic_str.strip('[]')}]"

        # Ensure consistent article formatting
        article_str = data.article.strip() if data.article and data.article.strip() else "[noun]"

        # Draw phonetic text in italic with proper spacing
        draw.text((text_padding_left, current_y), phonetic_str, font=font_phonetic_noun, fill=text_color_on_swatch)
        current_y += get_text_dimensions(phonetic_str, font_phonetic_noun)[1] + int(swatch_panel_height * 0.008)

        # Draw article text in regular style
        draw.text((text_padding_left, current_y), article_str, font=font_article, fill=text_color_on_swatch)
        current_y += get_text_dimensions(article_str, font_article)[1] + int(swatch_panel_height * 0.02)

        # Description text with proper spacing and formatting
        description_to_draw = data.description if data.description and data.description.strip() else "A steadfast guardian of high mountain terrain, its resilience mirrored in a deep olive-brown hue. Conveys calm vigilance, endurance, and earthy warmth at altitude."

        # Add more spacing before description
        current_y += int(swatch_panel_height * 0.01)

        # Increase line height for better readability
        desc_line_height = get_text_dimensions("Tg", font_description)[1] * 1.1 # Slightly less than before
        max_desc_width = swatch_panel_width - (2 * text_padding_left)

        # Wrap description text with better spacing
        wrapped_desc_lines = []
        current_desc_line = ""
        for word in description_to_draw.split(' '):
            if get_text_dimensions(current_desc_line + word, font_description)[0] <= max_desc_width:
                current_desc_line += word + " "
            else:
                wrapped_desc_lines.append(current_desc_line.strip())
                current_desc_line = word + " "
        wrapped_desc_lines.append(current_desc_line.strip())

        # Limit number of description lines to avoid pushing metrics off
        max_desc_lines = 5 
        for i, line in enumerate(wrapped_desc_lines):
            if i < max_desc_lines:
                # Check remaining space to ensure we don't overlap with bottom section
                if current_y + desc_line_height < brand_y - int(swatch_panel_height * 0.05):
                    draw.text((text_padding_left, current_y), line, font=font_description, fill=text_color_on_swatch)
                    current_y += desc_line_height + int(swatch_panel_height * 0.005) # Tighter line spacing
                else:
                    break 
            else:
                break

        # --- Bottom Section: Brand, ID, Metrics ---
        # Now draw the brand and metrics (positions already calculated above)
        draw.text((text_padding_left, brand_y), brand_text, font=font_brand_main, fill=text_color_on_swatch)

        # Position ID below brand with consistent spacing
        id_y = brand_y + brand_h + metrics_line_spacing * 0.7
        draw.text((text_padding_left, id_y), id_text, font=font_id_main, fill=text_color_on_swatch)

        # Position metrics for better alignment
        metrics_start_x = text_padding_left + int(swatch_panel_width * 0.55) # Move slightly right to match goal design
        metrics_start_y = brand_y # Align with brand text

        # Calculate alignment for metrics with more precise right-alignment
        metrics_labels = ["HEX", "CMYK", "RGB"]
        max_label_width = max(get_text_dimensions(label, font_metrics_label_main)[0] for label in metrics_labels)
        metrics_value_x_offset = max_label_width + int(swatch_panel_width * 0.05) # More spacing between label and value

        current_metrics_y = metrics_start_y

        # HEX value
        hex_val_str = hex_color_input.upper()
        draw.text((metrics_start_x, current_metrics_y), "HEX", font=font_metrics_label_main, fill=text_color_on_swatch)
        draw.text((metrics_start_x + metrics_value_x_offset, current_metrics_y), hex_val_str, font=font_metrics_value_main, fill=text_color_on_swatch)
        current_metrics_y += get_text_dimensions("HEX", font_metrics_label_main)[1] + metrics_line_spacing

        # CMYK value with consistent spacing
        cmyk_val_str = f"{cmyk_color_tuple[0]} {cmyk_color_tuple[1]} {cmyk_color_tuple[2]} {cmyk_color_tuple[3]}"
        draw.text((metrics_start_x, current_metrics_y), "CMYK", font=font_metrics_label_main, fill=text_color_on_swatch)
        draw.text((metrics_start_x + metrics_value_x_offset, current_metrics_y), cmyk_val_str, font=font_metrics_value_main, fill=text_color_on_swatch)
        current_metrics_y += get_text_dimensions("CMYK", font_metrics_label_main)[1] + metrics_line_spacing
        
        # RGB value with consistent spacing
        rgb_val_str = f"{rgb_color[0]} {rgb_color[1]} {rgb_color[2]}"
        draw.text((metrics_start_x, current_metrics_y), "RGB", font=font_metrics_label_main, fill=text_color_on_swatch)
        draw.text((metrics_start_x + metrics_value_x_offset, current_metrics_y), rgb_val_str, font=font_metrics_value_main, fill=text_color_on_swatch)
        
        # Image panel placement
        user_image_fitted = ImageOps.fit(user_image_pil, (image_panel_width, image_panel_height), Image.Resampling.LANCZOS)
        if orientation.lower() == "horizontal":
            # Horizontal: Image is on the RIGHT
            canvas.paste(user_image_fitted, (swatch_panel_width, 0), user_image_fitted if user_image_fitted.mode == 'RGBA' else None)
        else: # Vertical: Image is on the BOTTOM
            canvas.paste(user_image_fitted, (0, swatch_panel_height), user_image_fitted if user_image_fitted.mode == 'RGBA' else None)
    
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
