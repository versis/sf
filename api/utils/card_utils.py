import io
import re
import base64
from typing import Tuple, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageOps

from api.utils.logger import log # Corrected import path

# --- Color Conversion Utilities ---
def hex_to_rgb(hex_color: str, request_id: Optional[str] = None) -> Optional[Tuple[int, int, int]]:
    hex_color = hex_color.lstrip('#')
    if not re.match(r"^[0-9a-fA-F]{6}$", hex_color) and not re.match(r"^[0-9a-fA-F]{3}$", hex_color):
        log(f"Invalid HEX format: {hex_color}", request_id=request_id)
        return None
    if len(hex_color) == 3:
        r, g, b = int(hex_color[0]*2, 16), int(hex_color[1]*2, 16), int(hex_color[2]*2, 16)
    else:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return (r, g, b)

def rgb_to_cmyk(r: int, g: int, b: int) -> Tuple[int, int, int, int]:
    if (r, g, b) == (0, 0, 0): return 0, 0, 0, 100
    c = 1 - (r / 255.0)
    m = 1 - (g / 255.0)
    y = 1 - (b / 255.0)
    min_cmy = min(c, m, y)
    if min_cmy == 1.0: return 0, 0, 0, 0
    c = (c - min_cmy) / (1 - min_cmy)
    m = (m - min_cmy) / (1 - min_cmy)
    y = (y - min_cmy) / (1 - min_cmy)
    return round(c * 100), round(m * 100), round(y * 100), round(min_cmy * 100)

# --- Font Loading --- (Assuming assets path is relative to where api/index.py runs)
ASSETS_BASE_PATH = "assets" # If api/index.py is in /api, this path is relative to /api
# If running from root, this should be "api/assets"
# For now, let's assume it is called from api/index.py context

def get_font(size: int, weight: str = "Regular", style: str = "Normal", font_family: str = "Inter", request_id: Optional[str] = None):
    import os # Keep os import here as it might check paths
    font_style_suffix = "Italic" if style.lower() == "italic" else ""
    pt_suffix = "18pt" if size <= 20 else ("24pt" if size <= 25 else "28pt")

    if font_family == "Mono":
        ibm_plex_weight = "Light" if weight == "Light" else ("Medium" if weight in ["Medium", "Bold", "SemiBold"] else "Regular")
        font_path = os.path.join(ASSETS_BASE_PATH, "fonts", "mono", f"IBMPlexMono-{ibm_plex_weight}.ttf")
    else:
        font_path = os.path.join(ASSETS_BASE_PATH, "fonts", "inter", f"Inter_{pt_suffix}-{weight}{font_style_suffix}.ttf")

    try:
        loaded_font = ImageFont.truetype(font_path, size)
        log(f"Successfully loaded font: {font_path}", request_id=request_id)
        return loaded_font
    except IOError as e:
        log(f"Failed to load font {font_path}: {e}. Falling back to default.", request_id=request_id)
        try: # Fallback to Inter Regular if specified font fails, then to default
            if font_family != "Inter" or weight != "Regular" or style != "Normal":
                fallback_path = os.path.join(ASSETS_BASE_PATH, "fonts", "inter", f"Inter_{pt_suffix}-Regular.ttf")
                log(f"Attempting fallback font: {fallback_path}", request_id=request_id)
                return ImageFont.truetype(fallback_path, size)
        except IOError:
            pass # If fallback also fails, load_default() is next
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
    request_id: Optional[str] = None
) -> bytes:
    log(f"Starting card image generation. Orientation: {orientation}, Color: {hex_color_input}", request_id=request_id)
    
    rgb_color = hex_to_rgb(hex_color_input, request_id)
    if rgb_color is None:
        log(f"Invalid hex color for card generation: {hex_color_input}", request_id=request_id)
        raise ValueError(f"Invalid hex color format: {hex_color_input}")

    # Decode image
    if ';base64,' not in cropped_image_data_url:
        log(f"Invalid image data URL format - missing base64 delimiter.", request_id=request_id)
        raise ValueError("Invalid image data URL format")
    try:
        header, encoded = cropped_image_data_url.split(';base64,', 1)
        image_data = base64.b64decode(encoded)
        img_buffer = io.BytesIO(image_data)
        user_image_pil = Image.open(img_buffer).convert("RGBA")
        log(f"User image decoded. Mode: {user_image_pil.mode}, Size: {user_image_pil.size}", request_id=request_id)
    except Exception as e:
        log(f"Error decoding/opening base64 image: {e}", request_id=request_id)
        raise ValueError(f"Failed to process image data: {str(e)}")

    # Resize large images
    if user_image_pil.width > 2000 or user_image_pil.height > 2000:
        log(f"Resizing image from {user_image_pil.size} to max 2000px side", request_id=request_id)
        user_image_pil.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
        log(f"Resized image to: {user_image_pil.size}", request_id=request_id)

    # Card dimensions (reduced for better file size)
    VERTICAL_CARD_W, VERTICAL_CARD_H = 900, 1800
    HORIZONTAL_CARD_W, HORIZONTAL_CARD_H = 1800, 900
    bg_color_tuple = (250, 250, 250, 255) # RGBA

    if orientation == "horizontal":
        card_w, card_h = HORIZONTAL_CARD_W, HORIZONTAL_CARD_H
        swatch_w, swatch_h = int(card_w * 0.5), card_h
        img_panel_w, img_panel_h = card_w - swatch_w, card_h
        img_paste_pos = (swatch_w, 0)
    else: # vertical
        card_w, card_h = VERTICAL_CARD_W, VERTICAL_CARD_H
        swatch_w, swatch_h = card_w, int(card_h * 0.5)
        img_panel_w, img_panel_h = card_w, card_h - swatch_h
        img_paste_pos = (0, swatch_h)
    
    log(f"Card dims: {card_w}x{card_h}, Swatch: {swatch_w}x{swatch_h}, ImgPanel: {img_panel_w}x{img_panel_h}", request_id=request_id)

    canvas = Image.new('RGBA', (card_w, card_h), bg_color_tuple)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([(0,0), (swatch_w, swatch_h)], fill=rgb_color)

    # Preserve original image proportions without cropping
    user_image_sized = user_image_pil.copy()
    user_image_sized.thumbnail((img_panel_w, img_panel_h), Image.Resampling.LANCZOS)

    # Center the image in its panel
    paste_x = img_paste_pos[0] + (img_panel_w - user_image_sized.width) // 2
    paste_y = img_paste_pos[1] + (img_panel_h - user_image_sized.height) // 2
    img_centered_pos = (paste_x, paste_y)
    canvas.paste(user_image_sized, img_centered_pos, user_image_sized if user_image_sized.mode == 'RGBA' else None)
    log(f"Image panel size: {img_panel_w}x{img_panel_h}, Image size: {user_image_sized.width}x{user_image_sized.height}", request_id=request_id)
    log(f"Image centered at: {img_centered_pos}", request_id=request_id)

    # Text rendering
    text_color = (20, 20, 20) if sum(rgb_color) > 384 else (245, 245, 245) # 128*3 = 384
    pad_l = int(swatch_w * 0.09)
    pad_t = int(swatch_h * 0.02)
    pad_b = int(swatch_h * 0.08)
    
    base_font_scale = swatch_w / (750 if swatch_w >= 900 else (450 if swatch_w >= 450 else 350))
    current_y = pad_t

    # Fonts (Final fine-tuning of base sizes)
    f_title = get_font(int(40 * base_font_scale), "Bold", request_id=request_id)
    f_phonetic = get_font(int(30 * base_font_scale), "Light", "Italic", request_id=request_id)
    f_article = get_font(int(30 * base_font_scale), "Light", request_id=request_id)
    f_desc = get_font(int(27 * base_font_scale), "Regular", request_id=request_id)
    f_brand = get_font(int(64 * base_font_scale), "Bold", request_id=request_id)
    f_id = get_font(int(38 * base_font_scale), "Light", font_family="Mono", request_id=request_id)
    f_metrics_label = get_font(int(24 * base_font_scale), "Light", font_family="Mono", request_id=request_id)
    f_metrics_val = get_font(int(24 * base_font_scale), "Light", font_family="Mono", request_id=request_id)

    # Card Name (from AI or default)
    card_name_display = card_details.get("cardName", "MISSING NAME").upper()
    current_y += int(swatch_h * 0.07)
    x_pos = pad_l
    for char_cn in card_name_display:
        draw.text((x_pos, current_y), char_cn, font=f_title, fill=text_color)
        char_w_cn, _ = get_text_dimensions(char_cn, f_title)
        x_pos += char_w_cn + int(swatch_w * 0.002)
    _, h_title = get_text_dimensions(card_name_display, f_title)
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
    current_y += h_phonetic + int(swatch_h * 0.03)

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
    id_display_for_height_calc = card_details.get("cardId", "0000000 XX X")
    _, id_h = get_text_dimensions(id_display_for_height_calc, f_id)
    _, h_metric_label = get_text_dimensions("XYZ", f_metrics_label) # Approx height for metric lines

    # Define vertical spacing (increased spacing between bottom elements)
    space_between_brand_id = int(swatch_h * 0.035) # Reduced from 0.045
    space_between_id_metrics = int(swatch_h * 0.065) # Increased from 0.045
    line_spacing_metrics = int(swatch_h * 0.025) # Increased from 0.018

    # --- New Y-Positioning Logic for Bottom Elements ---

    # 1. Position Brand ("shadefreude") higher up - moved from 70% to 63% for better bottom padding
    brand_y_pos = int(swatch_h * 0.63) # Moved up from 0.70 to add more padding at bottom

    # 2. Position Card ID below the brand
    id_y_pos = brand_y_pos + brand_h + space_between_brand_id # space_between_brand_id was already increased

    # 3. Position Metrics block below the Card ID
    metrics_start_y = id_y_pos + id_h + space_between_id_metrics

    # --- End New Y-Positioning Logic ---

    for i, line_d in enumerate(wrapped_desc):
        # Ensure description does not overlap with the new, higher brand position
        if i < 4 and (current_y + desc_line_h < brand_y_pos - int(swatch_h * 0.05)):
            draw.text((pad_l, current_y), line_d, font=f_desc, fill=text_color)
            current_y += desc_line_h + int(swatch_h * 0.004)
        else: break

    # Draw Brand, ID, Metrics with new Y positions
    draw.text((pad_l, brand_y_pos), brand_text, font=f_brand, fill=text_color)
    
    id_display = card_details.get("cardId", "0000000 XX X")
    draw.text((pad_l, id_y_pos), id_display, font=f_id, fill=text_color)

    # Align metrics to the left (pad_l)
    metrics_labels_start_x = pad_l # Changed from pad_l + metrics_x_offset
    
    # Check if metrics are provided in card_details, otherwise calculate them
    if "metrics" in card_details:
        hex_val = card_details["metrics"].get("hex", hex_color_input.upper())
        rgb_val = card_details["metrics"].get("rgb", f"{rgb_color[0]} {rgb_color[1]} {rgb_color[2]}")
        cmyk_val = card_details["metrics"].get("cmyk", "{} {} {} {}".format(*rgb_to_cmyk(rgb_color[0], rgb_color[1], rgb_color[2])))
    else:
        hex_val = hex_color_input.upper()
        cmyk_val = "{} {} {} {}".format(*rgb_to_cmyk(rgb_color[0], rgb_color[1], rgb_color[2]))
        rgb_val = f"{rgb_color[0]} {rgb_color[1]} {rgb_color[2]}"
    
    metric_data = [("HEX", hex_val), ("CMYK", cmyk_val), ("RGB", rgb_val)]
    # Calculate where the metric values start, to the right of the labels
    max_label_w = 0
    if metric_data: # Ensure metric_data is not empty
        max_label_w = max(get_text_dimensions(label_text[0], f_metrics_label)[0] for label_text in metric_data)
    
    val_x_start = metrics_labels_start_x + max_label_w + int(swatch_w * 0.06) # Increased gap after longest label
    
    current_metrics_y = metrics_start_y

    for label, value in metric_data:
        draw.text((metrics_labels_start_x, current_metrics_y), label, font=f_metrics_label, fill=text_color)
        draw.text((val_x_start, current_metrics_y), value, font=f_metrics_val, fill=text_color)
        # Use the actual height of the current label for incrementing Y
        _, h_current_metric_label = get_text_dimensions(label, f_metrics_label)
        current_metrics_y += h_current_metric_label + line_spacing_metrics
    
    log("Text rendering complete", request_id=request_id)

    # Rounded corners and save
    radius = 40
    mask = Image.new('L', (card_w * 2, card_h * 2), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0,0), (card_w*2-1, card_h*2-1)], radius=radius*2, fill=255)
    mask = mask.resize((card_w, card_h), Image.Resampling.LANCZOS)
    canvas.putalpha(mask)
    log("Applied rounded corners", request_id=request_id)

    img_byte_arr = io.BytesIO()
    # Convert to RGB for image saving
    final_image_rgb = Image.new("RGB", canvas.size, (255, 255, 255)) # White background
    final_image_rgb.paste(canvas, mask=canvas.split()[3] if canvas.mode == 'RGBA' else None)
    # Save as PNG with compression to reduce file size
    final_image_rgb.save(img_byte_arr, format='PNG', compress_level=2)
    image_bytes = img_byte_arr.getvalue()
    log(f"Card image generated ({orientation}). Size: {len(image_bytes)/1024:.2f}KB", request_id=request_id)
    return image_bytes 