import io
import base64
from typing import Tuple, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageOps
from datetime import datetime
import os # Added for path joining

from api.utils.logger import log, debug, error # Ensure error is imported if used
from api.utils.color_utils import hex_to_rgb, rgb_to_cmyk, desaturate_hex_color, adjust_hls

# --- Font Loading ---
# Corrected path assuming api/utils/card_utils.py is run in context of api/index.py
# and assets folder is at the project root (sf/assets)
ASSETS_BASE_PATH = "assets"
# Define project root for robust path construction, assuming 'api' is a top-level dir or similar
# This might need adjustment based on actual execution context.
# For now, we\'ll construct the logo path directly.
# PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# LOGO_PATH = os.path.join(PROJECT_ROOT, "public", "sf-icon.png")
# Simpler approach for now, assuming execution context allows relative path from project root:
LOGO_PATH = "public/sf-icon.png"

def get_font(size: int, weight: str = "Regular", style: str = "Normal", font_family: str = "Inter", request_id: Optional[str] = None):
    import os # Keep os import here as it might check paths
    font_style_suffix = "Italic" if style.lower() == "italic" else ""
    # pt_suffix = "18pt" if size <= 20 else ("24pt" if size <= 25 else "28pt") # Only for Inter

    font_path = ""
    if font_family == "Mono":
        ibm_plex_weight = "Light" if weight == "Light" else ("Medium" if weight in ["Medium", "Bold", "SemiBold"] else "Regular")
        font_path = os.path.join(ASSETS_BASE_PATH, "fonts", "mono", f"IBMPlexMono-{ibm_plex_weight}.ttf")
    elif font_family == "Caveat":
        font_path = os.path.join(ASSETS_BASE_PATH, "fonts", "caveat", f"Caveat-{weight}.ttf") 
        # font_style_suffix = "" # Caveat is naturally cursive, Italic suffix might not be in filenames, ensure `weight` includes any style variant if needed e.g. Caveat-Bold might be only option
    elif font_family == "IBMPlexSerif":
        if weight == "Regular" and style.lower() == "italic":
            # Handle the specific case where "Regular" is omitted for standard italic
            serif_font_filename = "IBMPlexSerif-Italic.ttf"
        else:
            serif_font_filename = f"IBMPlexSerif-{weight}{font_style_suffix}.ttf"
        font_path = os.path.join(ASSETS_BASE_PATH, "fonts", "serif", serif_font_filename)
    elif font_family == "Inter":
        pt_suffix = "18pt" if size <= 20 else ("24pt" if size <= 25 else "28pt") # Specific to Inter
        inter_font_filename = ""
        if style.lower() == "italic":
            # Try specific italic files first (e.g., Inter-Italic.ttf, Inter-MediumItalic.ttf)
            # This covers cases where pt_suffix might not be part of the filename for some italic fonts
            specific_italic_variations = [
                f"Inter-{weight}Italic.ttf", # Inter-BoldItalic.ttf
                f"Inter-Italic.ttf", # Generic Italic, often Regular weight
                f"Inter_{pt_suffix}-{weight}Italic.ttf", # Inter_18pt-BoldItalic.ttf
                f"Inter_{pt_suffix}-Italic.ttf" # Inter_18pt-Italic.ttf
            ]
            for fname_candidate in specific_italic_variations:
                potential_path = os.path.join(ASSETS_BASE_PATH, "fonts", "inter", fname_candidate)
                if os.path.exists(potential_path):
                    inter_font_filename = fname_candidate
                    debug(f"Found specific Inter Italic font: {inter_font_filename}", request_id=request_id)
                    break
            if not inter_font_filename: # Fallback to original pattern if specific not found
                inter_font_filename = f"Inter_{pt_suffix}-{weight}{font_style_suffix}.ttf"
        else: # Non-italic Inter
            inter_font_filename = f"Inter_{pt_suffix}-{weight}.ttf" # Removed font_style_suffix for non-italic
        
        font_path = os.path.join(ASSETS_BASE_PATH, "fonts", "inter", inter_font_filename)
    else: # Default to Inter if family is unknown, or use a truly generic fallback
        font_path = os.path.join(ASSETS_BASE_PATH, "fonts", "inter", f"Inter_{pt_suffix}-{weight}{font_style_suffix}.ttf")

    try:
        loaded_font = ImageFont.truetype(font_path, size)
        debug(f"Successfully loaded font: {font_path} for family: {font_family}, weight: {weight}, style: {style}", request_id=request_id)
        return loaded_font
    except IOError as e:
        log(f"Failed to load font '{font_path}': {e}. Falling back. (Details: Family='{font_family}', Weight='{weight}', Style='{style}')", level="WARNING", request_id=request_id)
        # Try a more generic Inter fallback first
        try:
            # Fallback to a very common Inter font if the requested one fails
            # This might not be the desired style, but better than a bitmap default usually
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
    request_id: Optional[str] = None
) -> bytes:
    log(f"Starting card image generation. Orientation: {orientation}, Color: {hex_color_input}", request_id=request_id)
    
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

    # Card dimensions (reduced for better file size)
    VERTICAL_CARD_W, VERTICAL_CARD_H = 700, 1400
    HORIZONTAL_CARD_W, HORIZONTAL_CARD_H = 1400, 700
    bg_color_tuple = (0, 0, 0, 0) # Fully Transparent RGBA

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
    
    base_font_scale = swatch_w / 750
    current_y = pad_t

    # Fonts (Final fine-tuning of base sizes)
    f_title = get_font(int(40 * base_font_scale), "Bold", request_id=request_id)
    f_phonetic = get_font(int(30 * base_font_scale), "Light", "Italic", request_id=request_id)
    f_article = get_font(int(30 * base_font_scale), "Light", request_id=request_id)
    f_desc = get_font(int(27 * base_font_scale), "Light", request_id=request_id)
    f_brand = get_font(int(64 * base_font_scale), "Bold", request_id=request_id)
    f_id = get_font(int(38 * base_font_scale), "Light", font_family="Mono", request_id=request_id)
    f_metrics_label = get_font(int(26 * base_font_scale), "Light", font_family="Mono", request_id=request_id)
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
    id_display_for_height_calc = card_details["extendedId"]
    _, id_h = get_text_dimensions(id_display_for_height_calc, f_id)
    _, h_metric_label = get_text_dimensions("XYZ", f_metrics_label) # Approx height for metric lines

    # Define vertical spacing (increased spacing between bottom elements)
    space_between_brand_id = int(swatch_h * 0.03) # Reduced from 0.035
    space_between_id_metrics = int(swatch_h * 0.05) # Reduced from 0.065
    line_spacing_metrics = int(swatch_h * 0.02) # Reduced from 0.025

    # --- Y-Positioning Logic for Bottom Elements ---

    # 1. Position Brand ("shadefreude") higher up - moved from 63% to 58% to move text higher
    brand_y_pos = int(swatch_h * 0.62) # Moved up from 0.63 to add more padding at bottom

    # 2. Position Card ID below the brand
    id_y_pos = brand_y_pos + brand_h + space_between_brand_id

    # 3. Position Metrics block below the Card ID
    metrics_start_y = id_y_pos + id_h + space_between_id_metrics

    # --- End Y-Positioning Logic ---

    for i, line_d in enumerate(wrapped_desc):
        # Ensure description does not overlap with the new, higher brand position
        if i < 5 and (current_y + desc_line_h < brand_y_pos - int(swatch_h * 0.06)):
            draw.text((pad_l, current_y), line_d, font=f_desc, fill=text_color)
            current_y += desc_line_h + int(swatch_h * 0.004)
        else: break

    # Draw Brand, ID, Metrics with new Y positions
    draw.text((pad_l, brand_y_pos), brand_text, font=f_brand, fill=text_color)
    
    id_display = card_details["extendedId"]
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
    
    debug("Text rendering complete", request_id=request_id)

    # Rounded corners and save
    radius = 40
    mask = Image.new('L', (card_w * 2, card_h * 2), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0,0), (card_w*2-1, card_h*2-1)], radius=radius*2, fill=255)
    mask = mask.resize((card_w, card_h), Image.Resampling.LANCZOS)
    canvas.putalpha(mask)
    debug("Applied rounded corners", request_id=request_id)

    img_byte_arr = io.BytesIO()
    # Save as PNG with compression to reduce file size, preserving RGBA
    canvas.save(img_byte_arr, format='PNG', compress_level=2)
    image_bytes = img_byte_arr.getvalue()
    log(f"Card image generated ({orientation}). Size: {len(image_bytes)/1024:.2f}KB", request_id=request_id)
    return image_bytes 

# --- Back Card Generation Logic ---
async def generate_back_card_image_bytes(
    note_text: Optional[str],
    hex_color_input: str, 
    orientation: str,
    created_at_iso_str: Optional[str] = None, 
    request_id: Optional[str] = None
) -> bytes:
    log(f"Starting back card image generation. Orientation: {orientation}", request_id=request_id)

    # --- TOGGLE for background effect ---
    apply_60_percent_opacity_effect_to_back_bg = False 
    # --- END TOGGLE ---

    original_rgb = hex_to_rgb(hex_color_input, request_id=request_id)
    if not original_rgb:
        log(f"Invalid hex_color_input '{hex_color_input}' for card back. Using fallback grey.", level="WARNING", request_id=request_id)
        original_rgb = (200, 200, 200) 
    
    # 1. Determine card dimensions and base font sizes
    if orientation == "horizontal":
        card_w, card_h = 1400, 700
        note_font_size_val = 32
        date_below_note_font_size_val = 26
    else: # vertical
        card_w, card_h = 700, 1400
        note_font_size_val = 32
        date_below_note_font_size_val = 22

    # 2. Calculate effective background color
    r_orig_bg, g_orig_bg, b_orig_bg = original_rgb
    alpha_blend_factor_for_bg = 1.0
    if apply_60_percent_opacity_effect_to_back_bg:
        alpha_blend_factor_for_bg = 0.60
    
    r_white_blend, g_white_blend, b_white_blend = 255, 255, 255
    r_blended_bg = round(r_orig_bg * alpha_blend_factor_for_bg + r_white_blend * (1 - alpha_blend_factor_for_bg))
    g_blended_bg = round(g_orig_bg * alpha_blend_factor_for_bg + g_white_blend * (1 - alpha_blend_factor_for_bg))
    b_blended_bg = round(b_orig_bg * alpha_blend_factor_for_bg + b_white_blend * (1 - alpha_blend_factor_for_bg))
    
    solid_lightened_bg_rgb = (
        max(0, min(255, r_blended_bg)),
        max(0, min(255, g_blended_bg)),
        max(0, min(255, b_blended_bg))
    )
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
    # f_date_below_note will be defined just before date rendering

    # 6. Define Stamp Area Dimensions (needed for note area calculation)
    main_stamp_area_size = int(min(card_w, card_h) * 0.20)
    main_stamp_padding = int(main_stamp_area_size * 0.1)
    main_stamp_x_start = card_w - pad_x - main_stamp_area_size
    main_stamp_y_start = pad_y
    scallop_circle_radius = max(1, int(main_stamp_area_size * 0.004))
    # scallop_step is used only in stamp drawing section

    # 7. Define Note Text Area Boundaries
    note_text_area_start_x = pad_x
    note_text_area_end_x = main_stamp_x_start - pad_x 
    available_width_for_note = note_text_area_end_x - note_text_area_start_x

    # 8. Prepare Note Text (Wrapping)
    note_line_h = get_text_dimensions("Tg", f_note)[1] * 1.65 # Increased from 1.45 for more spacing
    lines = []
    if note_text and note_text.strip():
        words = note_text.split(' ')
        current_line_for_note = ""
        for word in words:
            word_width, _ = get_text_dimensions(word, f_note)
            # Check if word itself is wider than available space (edge case for very long words)
            if current_line_for_note == "" and word_width > available_width_for_note:
                # For simplicity, we'll append it and let it overflow or be clipped by PIL
                # A more complex solution would hyphenate or break the word.
                lines.append(word)
                current_line_for_note = "" 
            elif get_text_dimensions(current_line_for_note + word, f_note)[0] <= available_width_for_note:
                current_line_for_note += word + " "
            else:
                lines.append(current_line_for_note.strip())
                current_line_for_note = word + " "
        if current_line_for_note.strip():
            lines.append(current_line_for_note.strip())
        lines = [line for line in lines if line] 

    # 9. Calculate Text Block Horizontal Start (for centering lines)
    text_block_x_start = note_text_area_start_x # Always align to the start of the note area

    # 10. Calculate Vertical Positioning for the entire Note & Lines Block
    total_note_block_height = 0
    if lines:
        total_note_block_height = (len(lines) * note_line_h)
    total_note_block_height += (2 * note_line_h) # Add height for the two extra rule lines
    if total_note_block_height > 0 and lines: # Only adjust if there were text lines
         total_note_block_height -= (note_line_h * 0.45) # Remove most of the leading from the last text line
    elif total_note_block_height > 0 and not lines: # Only extra lines
         total_note_block_height -= (note_line_h * 0.45) # Remove most of the leading from the first extra line

    available_height_for_elements = card_h - pad_y - pad_y 
    current_elements_y = pad_y # This is the top of the note/rule block
    if total_note_block_height < available_height_for_elements:
        current_elements_y = pad_y + (available_height_for_elements - total_note_block_height) / 2
    current_elements_y = max(pad_y, current_elements_y) # Ensure it doesn't go above top padding

    # 11. Define Rule Line Properties
    if text_color == (20, 20, 20): # Dark text
        rule_line_color = (80, 80, 80)  # Darker grey lines, was (190,190,190)
    else: # Light text (white)
        rule_line_color = (210, 210, 210)  # Remains a darker grey for contrast on dark card backgrounds
    rule_line_thickness = 1
    rule_x_start = note_text_area_start_x 
    rule_x_end = note_text_area_end_x
    
    ascent, _ = f_note.getmetrics() 
    y_cursor = current_elements_y # This is where the first line of text (or first rule) will be drawn from top

    # --- DRAWING SECTION ---

    # 12. Draw Stamp (Background, Border, Logo) - Moved here after canvas is ready
    stamp_bg_color = (240, 240, 240)
    stamp_fill_x1 = main_stamp_x_start + scallop_circle_radius
    stamp_fill_y1 = main_stamp_y_start + scallop_circle_radius
    stamp_fill_x2 = main_stamp_x_start + main_stamp_area_size - scallop_circle_radius
    stamp_fill_y2 = main_stamp_y_start + main_stamp_area_size - scallop_circle_radius
    draw.rectangle([(stamp_fill_x1, stamp_fill_y1), (stamp_fill_x2, stamp_fill_y2)], fill=stamp_bg_color)

    scallop_step = max(1, int(scallop_circle_radius * 4.5)) # Define scallop_step here
    s_edges = [
        (main_stamp_x_start, main_stamp_y_start, main_stamp_x_start + main_stamp_area_size, main_stamp_y_start, True),
        (main_stamp_x_start, main_stamp_y_start + main_stamp_area_size, main_stamp_x_start + main_stamp_area_size, main_stamp_y_start + main_stamp_area_size, True),
        (main_stamp_x_start, main_stamp_y_start, main_stamp_x_start, main_stamp_y_start + main_stamp_area_size, False),
        (main_stamp_x_start + main_stamp_area_size, main_stamp_y_start, main_stamp_x_start + main_stamp_area_size, main_stamp_y_start + main_stamp_area_size, False)
    ]
    for x1_s, y1_s, x2_s, y2_s, is_horizontal_edge in s_edges:
        current_pos_val = 0; length_val = x2_s - x1_s if is_horizontal_edge else y2_s - y1_s
        if length_val <= 0: continue
        while current_pos_val <= length_val:
            px_val = x1_s + current_pos_val if is_horizontal_edge else x1_s
            py_val = y1_s + current_pos_val if not is_horizontal_edge else y1_s
            draw.ellipse([(px_val - scallop_circle_radius, py_val - scallop_circle_radius), (px_val + scallop_circle_radius, py_val + scallop_circle_radius)], fill=solid_lightened_bg_rgb)
            current_pos_val += scallop_step
        px_end = x2_s if is_horizontal_edge else x1_s
        py_end = y2_s if not is_horizontal_edge else y1_s
        draw.ellipse([(px_end - scallop_circle_radius, py_end - scallop_circle_radius), (px_end + scallop_circle_radius, py_end + scallop_circle_radius)], fill=solid_lightened_bg_rgb)
    try:
        logo_img_original = Image.open(LOGO_PATH).convert("RGBA")
        logo_max_dim_main = main_stamp_area_size - (2 * main_stamp_padding)
        logo_img_main = logo_img_original.copy(); logo_img_main.thumbnail((logo_max_dim_main, logo_max_dim_main), Image.Resampling.LANCZOS)
        logo_main_x = main_stamp_x_start + main_stamp_padding + (logo_max_dim_main - logo_img_main.width) // 2
        logo_main_y = main_stamp_y_start + main_stamp_padding + (logo_max_dim_main - logo_img_main.height) // 2
        canvas.paste(logo_img_main, (logo_main_x, logo_main_y), logo_img_main)
    except Exception as e: log(f"Error with main stamp logo: {e}", level="ERROR", request_id=request_id)

    # 13. Render Note Text and Ruled Lines
    # y_cursor is already set from current_elements_y
    if lines:
        for line_idx, line_content in enumerate(lines):
            if y_cursor + note_line_h <= card_h - pad_y: 
                draw.text((text_block_x_start, y_cursor), line_content, font=f_note, fill=text_color)
                rule_y_position = y_cursor + ascent + 3 
                if rule_y_position < card_h - pad_y - 1:
                     draw.line([(rule_x_start, rule_y_position), (rule_x_end, rule_y_position)], 
                               fill=rule_line_color, width=rule_line_thickness)
                y_cursor += note_line_h
            else:
                log(f"Note text and rules truncated at line {line_idx + 1}", request_id=request_id)
                break
    
    # 14. Draw two additional Ruled Lines
    for i in range(2):
        rule_y_position = y_cursor + ascent + 3 
        # Ensure the rule line itself fits, and also check against bottom card padding
        if rule_y_position < (card_h - pad_y - rule_line_thickness): 
            draw.line([(rule_x_start, rule_y_position), (rule_x_end, rule_y_position)], 
                      fill=rule_line_color, width=rule_line_thickness)
            y_cursor += note_line_h 
        else:
            break 

    # 15. Render Date
    if created_at_iso_str:
        f_date_below_note = get_font(date_below_note_font_size_val, weight="Light", style="Italic", font_family="Inter", request_id=request_id)
        try:
            dt_object = datetime.fromisoformat(created_at_iso_str.replace('Z', '+00:00'))
            date_str = dt_object.strftime('%B %d, %Y')
            date_w, date_h = get_text_dimensions(date_str, f_date_below_note)
            gap_below_stamp = int(card_h * (0.015 if orientation == 'vertical' else 0.03)) 
            date_y = main_stamp_y_start + main_stamp_area_size + gap_below_stamp
            date_x = main_stamp_x_start + (main_stamp_area_size - date_w) // 2
            date_x = max(pad_x, date_x) 
            if date_y + date_h < card_h - pad_y:
                 draw.text((date_x, date_y), date_str, font=f_date_below_note, fill=text_color)
            else:
                 log(f"Date does not fit on card at new position below stamp. Y: {date_y}", request_id=request_id)
        except ValueError:
            log(f"Could not parse date for date string: {created_at_iso_str}", level="WARNING", request_id=request_id)

    # 16. Finalize Image (Rounded Corners, Save)
    radius = 40
    mask = Image.new('L', (card_w * 2, card_h * 2), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0,0), (card_w*2-1, card_h*2-1)], radius=radius*2, fill=255)
    mask = mask.resize((card_w, card_h), Image.Resampling.LANCZOS)
    canvas.putalpha(mask)
    debug("Applied rounded corners to back card", request_id=request_id)

    img_byte_arr = io.BytesIO()
    canvas.save(img_byte_arr, format='PNG', compress_level=2)
    image_bytes = img_byte_arr.getvalue()
    log(f"Back card image generated ({orientation}). Size: {len(image_bytes)/1024:.2f}KB", request_id=request_id)
    return image_bytes 