import io
import base64
from typing import Tuple, Dict, Any, Optional

from api.utils.logger import log, debug, error
from PIL import Image, ImageDraw, ImageFont, ImageOps
from datetime import datetime
import os
import math
import random
import qrcode

from api.utils.color_utils import hex_to_rgb, rgb_to_cmyk, desaturate_hex_color, adjust_hls

# --- Font Loading ---
ASSETS_BASE_PATH = "assets"
LOGO_PATH = "public/sf-icon.png"

# --- Card Dimensions (Exact 1:2 ratio for print quality) ---
# PNG dimensions (web quality)
CARD_WIDTH_PNG = 700   # Base width for vertical orientation (PNG)
CARD_HEIGHT_PNG = 1400  # Base height for vertical orientation (PNG)

# TIFF dimensions (print quality) 
CARD_WIDTH_TIFF = 900   # Base width for vertical orientation (TIFF)
CARD_HEIGHT_TIFF = 1800  # Base height for vertical orientation (TIFF)

# --- Print Quality Constants ---
PRINT_DPI = 300  # High resolution for professional printing

def get_card_dimensions(output_format: str = "PNG") -> tuple:
    """
    Get card dimensions based on output format.
    
    Args:
        output_format: "PNG" for web quality, "TIFF" for print quality
        
    Returns:
        Tuple of (width, height) for the specified format
    """
    if output_format.upper() == "TIFF":
        return CARD_WIDTH_TIFF, CARD_HEIGHT_TIFF
    else:
        return CARD_WIDTH_PNG, CARD_HEIGHT_PNG

# --- Image Saving Helper Function ---
def save_card_image(canvas: Image.Image, output_format: str = "PNG", request_id: Optional[str] = None) -> bytes:
    """
    Save card image in specified format with appropriate settings.
    
    Args:
        canvas: PIL Image to save
        output_format: "PNG" or "TIFF" 
        request_id: Request tracking ID
        
    Returns:
        bytes: Image data in specified format
    """
    img_byte_arr = io.BytesIO()
    
    if output_format.upper() == "TIFF":
        # For TIFF (print quality): Convert RGBA to RGB with white background
        if canvas.mode == 'RGBA':
            # Create white background
            rgb_image = Image.new('RGB', canvas.size, 'white')
            # Paste RGBA image onto white background using alpha as mask
            rgb_image.paste(canvas, mask=canvas.split()[-1])
            canvas = rgb_image
        
        # Save as TIFF with professional print settings
        canvas.save(
            img_byte_arr, 
            format='TIFF',
            compression='lzw',  # Lossless compression ideal for print
            dpi=(PRINT_DPI, PRINT_DPI)  # Embed 300 DPI metadata
        )
        debug(f"Saved as TIFF with LZW compression at {PRINT_DPI} DPI", request_id=request_id)
    else:
        # Default PNG (web quality): Preserve RGBA with transparency
        canvas.save(
            img_byte_arr, 
            format='PNG', 
            compress_level=2  # Light compression for web
        )
        debug(f"Saved as PNG with compression level 2", request_id=request_id)
    
    return img_byte_arr.getvalue()

def get_font(size: int, weight: str = "Regular", style: str = "Normal", font_family: str = "Inter", request_id: Optional[str] = None):
    import os
    font_style_suffix = "Italic" if style.lower() == "italic" else ""

    font_path = ""
    if font_family == "Mono":
        ibm_plex_weight = "Light" if weight == "Light" else ("Medium" if weight in ["Medium", "Bold", "SemiBold"] else "Regular")
        font_path = os.path.join(ASSETS_BASE_PATH, "fonts", "mono", f"IBMPlexMono-{ibm_plex_weight}.ttf")
    elif font_family == "Caveat":
        font_path = os.path.join(ASSETS_BASE_PATH, "fonts", "caveat", f"Caveat-{weight}.ttf") 
    elif font_family == "IBMPlexSerif":
        if weight == "Regular" and style.lower() == "italic":
            serif_font_filename = "IBMPlexSerif-Italic.ttf"
        else:
            serif_font_filename = f"IBMPlexSerif-{weight}{font_style_suffix}.ttf"
        font_path = os.path.join(ASSETS_BASE_PATH, "fonts", "serif", serif_font_filename)
    elif font_family == "Inter":
        pt_suffix = "18pt" if size <= 20 else ("24pt" if size <= 25 else "28pt")
        inter_font_filename = ""
        if style.lower() == "italic":
            specific_italic_variations = [
                f"Inter-{weight}Italic.ttf",
                f"Inter-Italic.ttf",
                f"Inter_{pt_suffix}-{weight}Italic.ttf",
                f"Inter_{pt_suffix}-Italic.ttf"
            ]
            for fname_candidate in specific_italic_variations:
                potential_path = os.path.join(ASSETS_BASE_PATH, "fonts", "inter", fname_candidate)
                if os.path.exists(potential_path):
                    inter_font_filename = fname_candidate
                    debug(f"Found specific Inter Italic font: {inter_font_filename}", request_id=request_id)
                    break
            if not inter_font_filename:
                inter_font_filename = f"Inter_{pt_suffix}-{weight}{font_style_suffix}.ttf"
        else:
            inter_font_filename = f"Inter_{pt_suffix}-{weight}.ttf"
        
        font_path = os.path.join(ASSETS_BASE_PATH, "fonts", "inter", inter_font_filename)
    else:
        pt_suffix = "18pt" if size <= 20 else ("24pt" if size <= 25 else "28pt")
        font_path = os.path.join(ASSETS_BASE_PATH, "fonts", "inter", f"Inter_{pt_suffix}-{weight}{font_style_suffix}.ttf")

    try:
        loaded_font = ImageFont.truetype(font_path, size)
        debug(f"Successfully loaded font: {font_path} for family: {font_family}, weight: {weight}, style: {style}", request_id=request_id)
        return loaded_font
    except IOError as e:
        log(f"Failed to load font '{font_path}': {e}. Falling back. (Details: Family='{font_family}', Weight='{weight}', Style='{style}')", level="WARNING", request_id=request_id)
        try:
            generic_inter_fallback_path = os.path.join(ASSETS_BASE_PATH, "fonts", "inter", "Inter-Regular.ttf") 
            if os.path.exists(generic_inter_fallback_path):
                log(f"Attempting Inter-Regular fallback: {generic_inter_fallback_path}", level="DEBUG", request_id=request_id)
                return ImageFont.truetype(generic_inter_fallback_path, size)
            else:
                log(f"Inter-Regular fallback not found at {generic_inter_fallback_path}. Proceeding to Pillow default.", level="WARNING", request_id=request_id)
        except IOError as fallback_e:
            log(f"Inter-Regular fallback also failed: {fallback_e}. Using ImageFont.load_default().", level="WARNING", request_id=request_id)
        
        return ImageFont.load_default(size)

# --- Helper Function for Font Measurements ---
def get_text_dimensions(text: str, font):
    if hasattr(font, 'getbbox'):
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    elif hasattr(font, 'getsize'): # older Pillow
        return font.getsize(text)
    return len(text) * (font.size // 2), font.size # Basic fallback

# --- Main Card Generation Logic ---
async def generate_card_image_bytes(
    cropped_image_data_url: str,
    card_details: Dict[str, Any],
    hex_color_input: str,
    orientation: str,
    request_id: Optional[str] = None,
    photo_date: Optional[str] = None,
    photo_location: Optional[str] = None,
    output_format: str = "PNG"
) -> bytes:
    log(f"Starting card image generation. Orientation: {orientation}, Color: {hex_color_input}, Photo Date: {photo_date}, Photo Location: {photo_location}", request_id=request_id)
    
    rgb_color = hex_to_rgb(hex_color_input, request_id)
    if rgb_color is None:
        log(f"Invalid hex color for card generation: {hex_color_input}", level="ERROR", request_id=request_id)
        raise ValueError(f"Invalid hex color format: {hex_color_input}")

    # Decode image
    if ';base64,' not in cropped_image_data_url:
        log(f"Invalid image data URL format - missing base64 delimiter.", level="ERROR", request_id=request_id)
        raise ValueError("Invalid image data URL format")
    try:
        header, encoded = cropped_image_data_url.split(';base64,', 1)
        image_data = base64.b64decode(encoded)
        img_buffer = io.BytesIO(image_data)
        user_image_pil = Image.open(img_buffer).convert("RGBA")
        debug(f"User image decoded. Mode: {user_image_pil.mode}, Size: {user_image_pil.size}", request_id=request_id)
    except Exception as e:
        log(f"Error decoding/opening base64 image: {e}", level="ERROR", request_id=request_id)
        raise ValueError(f"Failed to process image data: {str(e)}")

    # Resize large images
    if user_image_pil.width > 2000 or user_image_pil.height > 2000:
        debug(f"Resizing image from {user_image_pil.size} to max 2000px side", request_id=request_id)
        user_image_pil.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
        debug(f"Resized image to: {user_image_pil.size}", request_id=request_id)

    # Get format-specific card dimensions
    base_card_w, base_card_h = get_card_dimensions(output_format)
    bg_color_tuple = (0, 0, 0, 0) # Fully Transparent RGBA

    if orientation == "horizontal":
        card_w, card_h = base_card_h, base_card_w  # Swap for horizontal
        swatch_w, swatch_h = int(card_w * 0.5), card_h
        img_panel_w, img_panel_h = card_w - swatch_w, card_h
        img_paste_pos = (swatch_w, 0)
    else: # vertical
        card_w, card_h = base_card_w, base_card_h
        swatch_w, swatch_h = card_w, int(card_h * 0.5)
        img_panel_w, img_panel_h = card_w, card_h - swatch_h
        img_paste_pos = (0, swatch_h)
    
    log(f"Card dims: {card_w}x{card_h}, Swatch: {swatch_w}x{swatch_h}, ImgPanel: {img_panel_w}x{img_panel_h}", request_id=request_id)

    canvas = Image.new('RGBA', (card_w, card_h), bg_color_tuple)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([(0,0), (swatch_w, swatch_h)], fill=rgb_color)

    # Resize and crop the image to fill the panel
    user_image_fitted = ImageOps.fit(user_image_pil, (img_panel_w, img_panel_h), Image.Resampling.LANCZOS)
    
    # Paste the fitted image directly at the panel's origin (img_paste_pos)
    canvas.paste(user_image_fitted, img_paste_pos, user_image_fitted if user_image_fitted.mode == 'RGBA' else None)

    debug(f"Image panel size: {img_panel_w}x{img_panel_h}, Fitted image size: {user_image_fitted.width}x{user_image_fitted.height}", request_id=request_id)
    debug(f"Image pasted at: {img_paste_pos}", request_id=request_id)

    # Text rendering
    text_color = (20, 20, 20) if sum(rgb_color) > 384 else (245, 245, 245) # 128*3 = 384
    pad_l = int(swatch_w * 0.09)
    pad_t = int(swatch_h * 0.02)
    pad_b = int(swatch_h * 0.08)
    
    base_font_scale = swatch_w / CARD_WIDTH_PNG  # Scale relative to PNG baseline for consistent proportions
    current_y = pad_t

    # Fonts (Final fine-tuning of base sizes)
    f_title = get_font(int(40 * base_font_scale), "Bold", request_id=request_id)
    f_phonetic = get_font(int(30 * base_font_scale), "Light", "Italic", request_id=request_id)
    f_article = get_font(int(30 * base_font_scale), "Light", request_id=request_id)
    f_desc = get_font(int(27 * base_font_scale), "Light", request_id=request_id)
    f_id = get_font(int(38 * base_font_scale), "Light", font_family="Mono", request_id=request_id)
    f_brand = get_font(int(40 * base_font_scale), "Semibold", request_id=request_id)  # User updated
    f_metrics_val = get_font(int(26 * base_font_scale), "Light", font_family="Mono", request_id=request_id)

    # Color Name (from AI or default)
    color_name_display = card_details.get("colorName", "MISSING NAME").upper()
    current_y += int(swatch_h * 0.07)
    x_pos = pad_l
    for char_cn in color_name_display:
        draw.text((x_pos, current_y), char_cn, font=f_title, fill=text_color)
        char_w_cn, _ = get_text_dimensions(char_cn, f_title)
        x_pos += char_w_cn + int(swatch_w * 0.002)
    _, h_title = get_text_dimensions(color_name_display, f_title)
    current_y += h_title + int(swatch_h * 0.03)

    # Phonetic & Article
    phonetic_display = card_details.get("phoneticName", "[phonetic]")
    article_display = card_details.get("article", "[article]")
    
    p_bracket_w, _ = get_text_dimensions("[", f_phonetic)
    draw.text((pad_l, current_y), "[", font=f_phonetic, fill=text_color)
    x_pos = pad_l + p_bracket_w
    for char_ph in phonetic_display.strip("[]"):
        draw.text((x_pos, current_y), char_ph, font=f_phonetic, fill=text_color)
        char_w_ph, _ = get_text_dimensions(char_ph, f_phonetic)
        x_pos += char_w_ph + int(swatch_w * 0.005)
    draw.text((x_pos, current_y), "]", font=f_phonetic, fill=text_color)
    x_pos += p_bracket_w # Approx for closing bracket
    
    article_x = x_pos + int(swatch_w * 0.02)
    draw.text((article_x, current_y), article_display, font=f_article, fill=text_color)
    _, h_phonetic = get_text_dimensions(phonetic_display, f_phonetic)
    current_y += h_phonetic + int(swatch_h * 0.05)

    # Description
    desc_display = card_details.get("description", "Missing description.")
    desc_line_h = get_text_dimensions("Tg", f_desc)[1] * 1.08
    max_desc_w = swatch_w - (2 * pad_l)
    wrapped_desc = []
    current_line = ""
    for word in desc_display.split(' '):
        if get_text_dimensions(current_line + word, f_desc)[0] <= max_desc_w:
            current_line += word + " "
        else:
            wrapped_desc.append(current_line.strip())
            current_line = word + " "
    wrapped_desc.append(current_line.strip())
    
    brand_text = "shadefreude"
    # Get font heights for layout
    _, brand_h = get_text_dimensions(brand_text, f_brand)
    id_display_for_height_calc = card_details["extendedId"]
    _, id_h = get_text_dimensions(id_display_for_height_calc, f_id)
    _, h_new_metric_line = get_text_dimensions("United States", f_metrics_val)

    # Define vertical spacing
    space_between_brand_id = int(swatch_h * 0.02) # between brand, id AND metrics
    space_between_id_metrics = int(swatch_h * 0.06) # User adjusted
    line_spacing_new_metrics = int(swatch_h * 0.02) # between EACH metric

    # --- Y-Positioning Logic for Bottom Elements (Revised) ---
    # Calculate height of the new metrics block dynamically based on available data
    num_metric_lines = 0
    if photo_location: num_metric_lines += 1
    if photo_date: num_metric_lines += 1

    if num_metric_lines > 0:
        total_new_metrics_block_height = (num_metric_lines * h_new_metric_line) + ((num_metric_lines - 1) * line_spacing_new_metrics if num_metric_lines > 1 else 0)
        # Total height of the entire bottom text block (Brand + ID + New Metrics)
        total_bottom_block_height = brand_h + space_between_brand_id + id_h + space_between_id_metrics + total_new_metrics_block_height
    else: # No metrics lines
        total_new_metrics_block_height = 0
        total_bottom_block_height = brand_h + space_between_brand_id + id_h
    
    # Start Y position for the entire bottom block, aiming to keep a similar bottom margin (pad_b)
    bottom_elements_start_y_overall = swatch_h - pad_b - total_bottom_block_height

    # 1. Position Brand ("shadefreude")
    brand_y_pos = bottom_elements_start_y_overall 

    # 2. Position Card ID below the brand
    id_y_pos = brand_y_pos + brand_h + space_between_brand_id

    # 3. Position New Metrics block below the Card ID
    new_metrics_start_y = id_y_pos + id_h + space_between_id_metrics
    # --- End Y-Positioning Logic (Revised) ---

    for i, line_d in enumerate(wrapped_desc):
        # Ensure description does not overlap with the new, higher brand position
        # Adjusted condition to check against brand_y_pos
        if i < 5 and (current_y + desc_line_h < brand_y_pos - int(swatch_h * 0.04)):
            draw.text((pad_l, current_y), line_d, font=f_desc, fill=text_color)
            current_y += desc_line_h + int(swatch_h * 0.004)
        else: break

    # Draw Brand, ID, Metrics with new Y positions
    draw.text((pad_l, brand_y_pos), brand_text, font=f_brand, fill=text_color)
    
    id_display = card_details["extendedId"]
    draw.text((pad_l, id_y_pos), id_display, font=f_id, fill=text_color)

    # --- New Metrics Rendering (PNG Icon + Text, Dynamic Alignment) ---
    metric_items_to_render = []
    if photo_location:
        metric_items_to_render.append({"type": "pin", "value": photo_location})
    if photo_date:
        metric_items_to_render.append({"type": "calendar", "value": photo_date})

    if metric_items_to_render:
        current_y_for_metric_line = new_metrics_start_y
        icon_start_x = pad_l
        
        # General gap, icon-specific sizes will determine text_start_x in the loop
        gap_after_icon = int(swatch_w * 0.02)

        # Load icon images once
        icon_pin_img_orig, icon_calendar_img_orig = None, None
        try:
            icon_pin_img_orig = Image.open("public/icon_pin.png").convert("RGBA")
        except Exception as e:
            log(f"Error loading public/icon_pin.png: {e}", level="ERROR", request_id=request_id)
        try:
            icon_calendar_img_orig = Image.open("public/icon_calendar.png").convert("RGBA")
        except Exception as e:
            log(f"Error loading public/icon_calendar.png: {e}", level="ERROR", request_id=request_id)

        for item_info in metric_items_to_render:
            icon_type = item_info["type"]
            text_value = item_info["value"]
            
            current_icon_image_to_use = None
            current_icon_size = 0 # Default/placeholder

            if icon_type == "pin" and icon_pin_img_orig:
                current_icon_image_to_use = icon_pin_img_orig
                current_icon_size = int(base_font_scale * 20) # Pin icon size
            elif icon_type == "calendar" and icon_calendar_img_orig:
                current_icon_image_to_use = icon_calendar_img_orig
                current_icon_size = int(base_font_scale * 22) # Calendar icon size
            
            # Dynamically calculate text_start_x based on current icon size
            text_start_x = icon_start_x + current_icon_size + gap_after_icon

            # Draw the text first to get its dimensions and position
            draw.text((text_start_x, current_y_for_metric_line), text_value, font=f_metrics_val, fill=text_color)
            
            _text_w, text_h = get_text_dimensions(text_value, f_metrics_val)
            
            if current_icon_image_to_use and current_icon_size > 0:
                resized_icon = current_icon_image_to_use.resize((current_icon_size, current_icon_size), Image.Resampling.LANCZOS)
                icon_paste_y = current_y_for_metric_line + (text_h / 1.0) - (current_icon_size / 1.6)
                
                # Create a solid color image with the text_color
                color_fill_temp = Image.new('RGBA', resized_icon.size, text_color)
                
                # Paste the solid color image, using the original resized icon's alpha as the mask
                # This effectively recolors the icon shape with text_color
                canvas.paste(color_fill_temp, (icon_start_x, int(icon_paste_y)), resized_icon)
            
            current_y_for_metric_line += h_new_metric_line + line_spacing_new_metrics
            
    # --- End New Metrics Rendering ---
    
    debug("Text rendering complete", request_id=request_id)

    # Rounded corners and save
    radius = 40
    mask = Image.new('L', (card_w * 2, card_h * 2), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0,0), (card_w*2-1, card_h*2-1)], radius=radius*2, fill=255)
    mask = mask.resize((card_w, card_h), Image.Resampling.LANCZOS)
    canvas.putalpha(mask)
    debug("Applied rounded corners", request_id=request_id)

    # Save card image in requested format (PNG for web, TIFF for print)
    image_bytes = save_card_image(canvas, output_format, request_id)
    log(f"Card image generated ({orientation}, {output_format}). Size: {len(image_bytes)/1024:.2f}KB", request_id=request_id)
    return image_bytes 

# --- Back Card Generation Logic ---
async def generate_back_card_image_bytes(
    note_text: Optional[str],
    hex_color_input: str, 
    orientation: str,
    created_at_iso_str: Optional[str] = None, 
    request_id: Optional[str] = None,
    output_format: str = "PNG"
) -> bytes:
    log(f"Starting back card image generation. Orientation: {orientation}", request_id=request_id)

    # Define the fixed background color for the card back
    FIXED_BACK_CARD_COLOR_HEX = "#e9e9eb"  # "#E9EFF1" # Blue-Grey Card 6
    fixed_back_card_rgb = hex_to_rgb(FIXED_BACK_CARD_COLOR_HEX, request_id=request_id)
    if not fixed_back_card_rgb:
        log(f"Failed to convert FIXED_BACK_CARD_COLOR_HEX '{FIXED_BACK_CARD_COLOR_HEX}'. Using fallback.", level="ERROR", request_id=request_id)
        fixed_back_card_rgb = (233, 233, 235)  #(233, 237, 241)

    # 1. Determine card dimensions and proportional font sizes (format-specific)
    base_card_w, base_card_h = get_card_dimensions(output_format)
    
    if orientation == "horizontal":
        card_w, card_h = base_card_h, base_card_w  # Swap for horizontal
        # Use smaller dimension for consistent scaling across orientations
        base_scale = min(card_w, card_h) / CARD_WIDTH_PNG  # Use PNG baseline for consistent proportions
        note_font_size_val = int(32 * base_scale)
    else: # vertical
        card_w, card_h = base_card_w, base_card_h
        # Use smaller dimension for consistent scaling across orientations
        base_scale = min(card_w, card_h) / CARD_WIDTH_PNG  # Use PNG baseline for consistent proportions
        note_font_size_val = int(32 * base_scale)

    # 2. Calculate effective background color
    solid_lightened_bg_rgb = fixed_back_card_rgb # Use the fixed color directly
    bg_color_tuple = (*solid_lightened_bg_rgb, 255)

    # 3. Initialize Canvas and Draw objects
    canvas = Image.new('RGBA', (card_w, card_h), bg_color_tuple)
    draw = ImageDraw.Draw(canvas)

    # 4. Determine Text Color (based on the final solid background)
    text_color = (20, 20, 20) if sum(solid_lightened_bg_rgb) > 384 else (255, 255, 255)

    # 5. Define Paddings and Font Objects
    pad_x = int(card_w * 0.05) 
    pad_y = int(card_h * 0.05)
    
    f_note = get_font(note_font_size_val, weight="Light", style="Italic", font_family="IBMPlexSerif", request_id=request_id)

    # --- RECTANGULAR POSTAGE STAMP (Top-Right with LOGO) ---
    stamp_base_width = int(min(card_w, card_h) * 0.20) 
    stamp_height = int(stamp_base_width * 4/3) # Height is 1/3 more than width
    stamp_width = stamp_base_width # Keep original width calculation method

    stamp_padding_internal = int(min(stamp_width, stamp_height) * 0.1) # Padding based on smaller dimension of stamp
    stamp_x_start = card_w - pad_x - stamp_width
    stamp_y_start = pad_y

    # Draw rectangular stamp background (the actual stamp face)
    stamp_bg_color = (248, 249, 250) # App Background Color (#F8F9FA)
    draw.rectangle([
        (stamp_x_start, stamp_y_start), 
        (stamp_x_start + stamp_width, stamp_y_start + stamp_height)
    ], fill=stamp_bg_color)

    # Draw rectangular stamp perforation dots
    perf_reference_size = min(stamp_width, stamp_height)
    perf_dot_radius = max(2, int(perf_reference_size * 0.035)) 
    perf_dot_step = int(perf_dot_radius * 2.2)
    perf_color = fixed_back_card_rgb # Perforations match the card back
    
    # Use reusable perforation function
    draw_perforation_dots(draw, stamp_x_start, stamp_y_start, stamp_width, stamp_height,
                         perf_dot_radius, perf_dot_step, perf_color)
    
    # Draw Logo in rectangular stamp
    try:
        logo_img_original = Image.open(LOGO_PATH).convert("RGBA")
        # Logo fits within the padded area, scaled by the smaller of stamp_width/stamp_height
        logo_max_dim_w = stamp_width - (2 * stamp_padding_internal)
        logo_max_dim_h = stamp_height - (2 * stamp_padding_internal)
        logo_img_main = logo_img_original.copy()
        logo_img_main.thumbnail((logo_max_dim_w, logo_max_dim_h), Image.Resampling.LANCZOS)
        
        logo_x = stamp_x_start + (stamp_width - logo_img_main.width) // 2 # Centered horizontally
        logo_y = stamp_y_start + (stamp_height - logo_img_main.height) // 2 # Centered vertically
        canvas.paste(logo_img_main, (logo_x, logo_y), logo_img_main)
    except Exception as e: log(f"Error with rectangular stamp logo: {e}", level="ERROR", request_id=request_id)
    # --- END RECTANGULAR POSTAGE STAMP ---

    # --- CIRCULAR POSTMARK (Straight Text, Randomized Rotation & Position) ---
    postmark_diameter = int(min(card_w, card_h) * 0.13)
    postmark_radius = postmark_diameter // 2
    postmark_red_color = (204, 0, 0)

    # Base position for the center of the circular postmark (bottom-left of NEW rectangular stamp)
    base_postmark_cx = stamp_x_start
    base_postmark_cy = stamp_y_start + stamp_height # Use new stamp_height

    # Create a temporary canvas for the circular postmark to allow rotation
    # Size needs to be large enough for the rotated postmark (diagonal of its bounding box)
    temp_canvas_size = int(postmark_diameter * 1.5) # A bit larger to be safe
    temp_postmark_canvas = Image.new('RGBA', (temp_canvas_size, temp_canvas_size), (0,0,0,0)) # Transparent background
    temp_draw = ImageDraw.Draw(temp_postmark_canvas)
    temp_cx = temp_canvas_size // 2 # Center of temporary canvas
    temp_cy = temp_canvas_size // 2

    # Draw postmark elements (borders, straight text) onto the temporary canvas
    temp_draw.ellipse([(temp_cx - postmark_radius, temp_cy - postmark_radius), (temp_cx + postmark_radius, temp_cy + postmark_radius)], outline=postmark_red_color, width=max(1, int(postmark_radius * 0.06)))
    pm_inner_radius_offset = int(postmark_radius * 0.15)
    if postmark_radius - pm_inner_radius_offset > 0:
        temp_draw.ellipse([(temp_cx - postmark_radius + pm_inner_radius_offset, temp_cy - postmark_radius + pm_inner_radius_offset), (temp_cx + postmark_radius - pm_inner_radius_offset, temp_cy + postmark_radius - pm_inner_radius_offset)], outline=postmark_red_color, width=max(1, int(postmark_radius * 0.04)))

    pm_stamped_text = "STAMPED"
    pm_stamped_font_size = max(8, int(postmark_radius * 0.31))
    f_pm_stamped_text = get_font(pm_stamped_font_size, weight="Regular", font_family="Inter")
    stamped_text_w, stamped_text_h = get_text_dimensions(pm_stamped_text, f_pm_stamped_text)
    temp_draw.text((temp_cx - stamped_text_w / 2, temp_cy - postmark_radius + int(postmark_radius * 0.28)), pm_stamped_text, font=f_pm_stamped_text, fill=postmark_red_color)

    if created_at_iso_str:
        try:
            dt = datetime.fromisoformat(created_at_iso_str.replace('Z', '+00:00'))
            pm_date_str = dt.strftime('%Y-%m-%d')
            pm_date_font_size = max(8, int(postmark_radius * 0.28))
            f_pm_date = get_font(pm_date_font_size, weight="Regular", font_family="Inter")
            date_text_w, date_text_h = get_text_dimensions(pm_date_str, f_pm_date)
            temp_draw.text((temp_cx - date_text_w / 2, temp_cy + postmark_radius - int(postmark_radius * 0.38) - date_text_h), pm_date_str, font=f_pm_date, fill=postmark_red_color)
        except ValueError: log(f"Could not parse date for circular postmark: {created_at_iso_str}",level="WARNING")

    # Random rotation
    random_angle = random.uniform(0, 360)
    rotated_postmark = temp_postmark_canvas.rotate(random_angle, expand=True, resample=Image.Resampling.BICUBIC)

    # Random position jitter
    max_jitter = postmark_diameter / 4
    x_jitter = random.uniform(-max_jitter, max_jitter)
    y_jitter = random.uniform(-max_jitter, max_jitter)

    final_postmark_center_x = base_postmark_cx + x_jitter
    final_postmark_center_y = base_postmark_cy + y_jitter

    # Calculate top-left for pasting the rotated image so its center aligns with final_postmark_center_x/y
    paste_x = int(final_postmark_center_x - rotated_postmark.width / 2)
    paste_y = int(final_postmark_center_y - rotated_postmark.height / 2)

    canvas.paste(rotated_postmark, (paste_x, paste_y), rotated_postmark) # Paste using alpha channel
    # --- END CIRCULAR POSTMARK ---

    # --- QR CODE (Bottom-Right, Same Column as Stamp, Same Style as Stamp) ---
    qr_width = stamp_width  # Same width as stamp
    qr_height = stamp_height  # Same height as stamp  
    qr_x_start = stamp_x_start  # Same X position as stamp (aligned in column)
    qr_y_start = card_h - pad_y - qr_height  # Position at bottom of card

    # Draw QR code background (same style as stamp)
    qr_bg_color = stamp_bg_color  # Use same background color as stamp
    draw.rectangle([
        (qr_x_start, qr_y_start), 
        (qr_x_start + qr_width, qr_y_start + qr_height)
    ], fill=qr_bg_color)

    # Draw QR code perforation dots (same style as stamp)
    draw_perforation_dots(draw, qr_x_start, qr_y_start, qr_width, qr_height,
                         perf_dot_radius, perf_dot_step, perf_color)

    # Generate and place QR code image inside the "stamp"
    try:
        # Calculate inner area (like stamp padding) for QR code placement
        qr_padding_internal = int(min(qr_width, qr_height) * 0.1)  # Same padding logic as stamp
        qr_inner_width = qr_width - (2 * qr_padding_internal)
        qr_inner_height = qr_height - (2 * qr_padding_internal)
        
        # QR codes must be square - use the smaller dimension to fit within stamp
        qr_square_size = min(qr_inner_width, qr_inner_height)
        
        # Generate QR code dynamically with the same grey background as stamp
        qr_data = "https://shadefreude.com"
        qr_img_generated = generate_qr_code_image(
            data=qr_data,
            size=(qr_square_size, qr_square_size),  # Always square
            background_color=qr_bg_color,  # Use same background as stamp
            request_id=request_id
        )
        
        # Center QR code within the "stamp" area
        qr_inner_x = qr_x_start + (qr_width - qr_img_generated.width) // 2
        qr_inner_y = qr_y_start + (qr_height - qr_img_generated.height) // 2
        
        # Paste QR code onto the canvas
        canvas.paste(qr_img_generated, (qr_inner_x, qr_inner_y), qr_img_generated)
        debug(f"QR code stamp added at position ({qr_x_start}, {qr_y_start}) with stamp size {qr_width}x{qr_height}, QR data: {qr_data}, QR image: {qr_img_generated.width}x{qr_img_generated.height} (square)", request_id=request_id)
    except Exception as e: 
        log(f"Error generating QR code: {e}", level="ERROR", request_id=request_id)
        debug("QR code will not be displayed on this card", request_id=request_id)
    # --- END QR CODE ---

    # Adjust Note Area based on the RECTANGULAR stamp (top-right)
    note_text_area_start_x = pad_x
    note_text_area_end_x = stamp_x_start - pad_x # Notes to the left of rectangular stamp
    available_width_for_note = note_text_area_end_x - note_text_area_start_x

    # --- Start of Note and Rule Drawing Logic (Integrate from previous version if needed) ---
    if note_text:
        lines = []
        max_chars_per_line = int(available_width_for_note / (f_note.size * 0.45)) # Approx char width
        
        # Split note_text into paragraphs first, then wrap each paragraph
        paragraphs = note_text.split('\n')
        for paragraph in paragraphs:
            if not paragraph.strip(): # Handle empty lines (e.g., double newlines)
                lines.append("") # Add an empty line to preserve paragraph spacing
                continue

            words = paragraph.split(' ')
            current_line = ''
            for word in words:
                test_line = current_line + word + ' '
                line_width, _ = get_text_dimensions(test_line.strip(), f_note)
                if line_width <= available_width_for_note:
                    current_line = test_line
                else:
                    lines.append(current_line.strip())
                    current_line = word + ' '
            lines.append(current_line.strip()) # Add the last line of the paragraph
            
        # Remove trailing empty lines that might result from splitting/wrapping
        while lines and not lines[-1]:
            lines.pop()
            
        # Vertical Centering Logic for Text Block and Ruled Lines
        note_line_h_approx, _ = get_text_dimensions("Tg", f_note) # Height of a single line of text
        # Get ascent for more precise vertical alignment to baseline
        try:
            ascent, _ = f_note.getmetrics() # (ascent, descent)
        except AttributeError:
            ascent = int(f_note.size * 0.75) # Fallback if getmetrics not available

        num_lines = len(lines)
        total_text_height = num_lines * note_line_h_approx
        
        # Calculate total block height including rules (fixed spacing between text and rule)
        rule_spacing_above_text = int(note_font_size_val * 0.2) # Space above text line before rule
        rule_spacing_below_text = int(note_font_size_val * 0.3) # Space below text baseline after rule
        # The effective height of one ruled line including text and spacing for rules
        single_ruled_line_effective_height = note_line_h_approx + rule_spacing_above_text + rule_spacing_below_text
        total_ruled_block_height = num_lines * single_ruled_line_effective_height

        # Calculate starting Y position to center the block in the available vertical space
        # The available vertical space is from pad_y to (card_h - pad_y)
        available_vertical_space_for_note = card_h - (2 * pad_y)
        
        # If the stamp is on the right, the note area might be constrained vertically if horizontal card.
        # Here, we assume note area has full vertical space from top to bottom padding.
        # If text block is taller than available space, it will just start from pad_y.
        y_cursor_start_centered = pad_y + (available_vertical_space_for_note - total_ruled_block_height) / 2
        y_cursor_start_centered = max(pad_y, y_cursor_start_centered) # Ensure it doesn't go above top padding

        y_cursor = y_cursor_start_centered
        
        text_block_x_start = note_text_area_start_x # Text starts at the beginning of its allowed area

        # Use text_color for rule lines instead of user's chosen color for better contrast
        rule_line_color = text_color  # Use the same color as text for consistency and readability

        rule_x_start = text_block_x_start
        rule_x_end = note_text_area_end_x # Rules span the full available note width
        
        for line_text in lines:
            # Calculate the Y for the TOP of the text line
            text_top_y = y_cursor + rule_spacing_above_text
            
            # The baseline is text_top_y + ascent
            current_text_baseline_y = text_top_y + ascent
            
            if line_text: # Draw text only if line is not empty
                 # Pilar draw.text uses the top-left coordinate.
                 # To align text so its baseline is at current_text_baseline_y, we draw at (current_text_baseline_y - ascent), which is text_top_y.
                 draw.text((text_block_x_start, text_top_y), line_text, font=f_note, fill=text_color)

            # Draw the rule line associated with this text line
            # The rule line should be slightly below the text baseline (current_text_baseline_y)
            current_rule_y = current_text_baseline_y + rule_spacing_below_text
            draw.line([(rule_x_start, current_rule_y), (rule_x_end, current_rule_y)], fill=rule_line_color, width=1)
            
            y_cursor += single_ruled_line_effective_height # Move to the start of the next line block

    log(f"Back card note processing complete. Request ID: {request_id if request_id else 'N/A'}", request_id=request_id)
    # --- End of Note and Rule Drawing Logic ---

    # Rounded corners and save
    radius = 40
    mask = Image.new('L', (card_w * 2, card_h * 2), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0,0), (card_w*2-1, card_h*2-1)], radius=radius*2, fill=255)
    mask = mask.resize((card_w, card_h), Image.Resampling.LANCZOS)
    canvas.putalpha(mask)
    debug("Applied rounded corners to back card", request_id=request_id)

    # Save back card image in requested format (PNG for web, TIFF for print)
    image_bytes = save_card_image(canvas, output_format, request_id)
    log(f"Back card image generated ({orientation}, {output_format}). Size: {len(image_bytes)/1024:.2f}KB", request_id=request_id)
    return image_bytes 

# --- Helper Functions for Drawing Postage Elements ---
def draw_perforation_dots(draw, x_start: int, y_start: int, width: int, height: int, 
                         perf_dot_radius: int, perf_dot_step: int, perf_color: tuple):
    """
    Draw perforation dots around a rectangular area (reusable for stamps and QR codes).
    
    Args:
        draw: PIL ImageDraw object
        x_start, y_start: Top-left corner of the rectangle
        width, height: Dimensions of the rectangle
        perf_dot_radius: Radius of each perforation dot
        perf_dot_step: Distance between perforation dots
        perf_color: Color tuple for the dots
    """
    edges_coords = [
        (x_start, y_start, x_start + width, y_start, True),  # Top
        (x_start, y_start + height, x_start + width, y_start + height, True),  # Bottom
        (x_start, y_start, x_start, y_start + height, False),  # Left
        (x_start + width, y_start, x_start + width, y_start + height, False)  # Right
    ]
    
    for x1, y1, x2, y2, is_horiz in edges_coords:
        length = (x2 - x1) if is_horiz else (y2 - y1)
        num_dots = max(1, int(length / perf_dot_step))
        actual_step = length / num_dots if num_dots > 0 else length
        for i in range(num_dots + 1):
            curr_pos = i * actual_step
            px, py = (x1 + curr_pos, y1) if is_horiz else (x1, y1 + curr_pos)
            draw.ellipse([(px - perf_dot_radius, py - perf_dot_radius), 
                         (px + perf_dot_radius, py + perf_dot_radius)], fill=perf_color)

def generate_qr_code_image(data: str, size: tuple, background_color: tuple = (248, 249, 250), 
                          request_id: Optional[str] = None) -> Image.Image:
    """
    Generate a QR code image with custom background color (matching stamp style).
    
    Args:
        data: The data to encode in the QR code (e.g., URL)
        size: Tuple of (width, height) for the final QR code image
        background_color: RGB tuple for background color (default: stamp grey)
        request_id: Request tracking ID
        
    Returns:
        PIL Image containing the QR code
    """
    try:
        # Create QR code
        qr = qrcode.QRCode(
            version=1,  # Controls the size of the QR code (1 = 21x21 modules)
            error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction
            box_size=10,  # Size of each box in pixels
            border=2,  # Border size in boxes
        )
        
        # Add data and generate
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create image with custom colors
        qr_img = qr.make_image(
            fill_color='black',  # QR code pattern color (black)
            back_color=background_color  # Background color (stamp grey)
        ).convert('RGBA')
        
        # Resize to match the requested size
        qr_img_resized = qr_img.resize(size, Image.Resampling.LANCZOS)
        
        debug(f"Generated QR code for data: {data[:50]}{'...' if len(data) > 50 else ''}, size: {size}", request_id=request_id)
        return qr_img_resized
        
    except Exception as e:
        log(f"Error generating QR code: {e}", level="ERROR", request_id=request_id)
        # Return a blank image with the background color as fallback
        fallback_img = Image.new('RGBA', size, background_color)
        return fallback_img

# --- Helper Functions for Drawing Custom Icons (REMOVED) ---
# draw_pin_icon and draw_calendar_icon functions are now removed.

def create_color_swatch_image_bytes(hex_color: str, width: int = 200, height: int = 200, request_id: Optional[str] = None) -> bytes:
    log(f"Creating color swatch for {hex_color}", request_id=request_id)
    # ... existing code ... 