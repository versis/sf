"""
Print utilities for professional postcard printing at 300 DPI.
Handles A4 layout generation with exact positioning and cutting guides.
"""

from PIL import Image, ImageDraw
from typing import List, Dict, Tuple, Optional, Any
import io
from .logger import log, debug
from .card_utils import CARD_WIDTH, CARD_HEIGHT, PRINT_DPI

# --- A4 Print Layout Constants (300 DPI) ---
A4_WIDTH_MM = 210
A4_HEIGHT_MM = 297
MM_TO_PIXELS = PRINT_DPI / 25.4  # 300 DPI = 11.811 pixels per mm

# A4 dimensions in pixels at 300 DPI  
A4_WIDTH_PX = int(A4_WIDTH_MM * MM_TO_PIXELS + 0.5)  # 2480 pixels (rounded)
A4_HEIGHT_PX = int(A4_HEIGHT_MM * MM_TO_PIXELS + 0.5)  # 3508 pixels (rounded)

# Card dimensions in mm (for print calculations) - based on actual pixel dimensions
CARD_WIDTH_MM = CARD_WIDTH / MM_TO_PIXELS   # ~59.95mm (708px at 300 DPI)
CARD_HEIGHT_MM = CARD_HEIGHT / MM_TO_PIXELS  # ~119.90mm (1416px at 300 DPI)

# NEW Layout specifications for 8×16cm landscape cards
GRID_COLS = 1  # 1 card wide (single column)
GRID_ROWS = 3  # 3 cards tall (3 rows)
A4_MARGINS_MM = 0           # No margins - use full page area

# Target CONTENT size (always 2:1 ratio for card content)
# This is now controlled by a parameter in the main A4Layout class

# Guillotine considerations - MINIMAL 1mm spacing for maximum card size
TOTAL_SPACING_MM = 1  # 1mm total spacing (ultra-minimal for guillotine)
SPACING_PX = int(TOTAL_SPACING_MM * MM_TO_PIXELS)  # ~12px

# Cutting guide appearance  
CUTTING_LINE_COLOR = "#888888"  # Light gray for subtle cutting guides
CUTTING_LINE_WIDTH = 1  # pixels - thinnest possible for precision
CUTTING_LINE_DASH_LENGTH = 12  # pixels - longer dashes

def mm_to_px(mm: float) -> int:
    """Convert millimeters to pixels at 300 DPI"""
    return int(mm * MM_TO_PIXELS)

def px_to_mm(px: int) -> float:
    """Convert pixels to millimeters at 300 DPI"""
    return px / MM_TO_PIXELS

class A4Layout:
    """
    A4 layout engine for professional postcard printing.
    Handles exact positioning, cutting guides, print alignment, and passepartout.
    """
    
    def __init__(self, request_id: Optional[str] = None, passepartout_mm: float = 0):
        self.request_id = request_id
        self.passepartout_mm = passepartout_mm
        self.passepartout_px = int(passepartout_mm * MM_TO_PIXELS) if passepartout_mm > 0 else 0
        self.canvas = None
        self.draw = None
        
        # Calculate final card size: content + passepartout
        # Content is always 14.6×7.3cm (2:1 ratio), final size depends on passepartout
        final_card_width_px = TARGET_CONTENT_WIDTH_PX + (2 * self.passepartout_px)
        final_card_height_px = TARGET_CONTENT_HEIGHT_PX + (2 * self.passepartout_px)
        
        self.card_width = final_card_width_px
        self.card_height = final_card_height_px
        
        # Spacing with guillotine kerf consideration
        self.actual_spacing_x = SPACING_PX  # ~59px (5mm total)
        self.actual_spacing_y = SPACING_PX  # ~59px (5mm total)
        
        # Calculate ACTUAL layout dimensions for 1×3 grid
        self.layout_width = GRID_COLS * self.card_width + (GRID_COLS - 1) * self.actual_spacing_x
        self.layout_height = GRID_ROWS * self.card_height + (GRID_ROWS - 1) * self.actual_spacing_y
        
        # Layout starts at page edge (no offset) 
        self.offset_x = 0
        self.offset_y = 0
        
        # Calculate exact usage and display metrics
        unused_width = A4_WIDTH_PX - self.layout_width
        unused_height = A4_HEIGHT_PX - self.layout_height
        
        debug(f"A4 Canvas: {A4_WIDTH_PX}×{A4_HEIGHT_PX}px (210×297mm)", request_id=self.request_id)
        debug(f"Content size: {TARGET_CONTENT_WIDTH_MM}×{TARGET_CONTENT_HEIGHT_MM}mm (2:1 ratio, no white space)", request_id=self.request_id)
        debug(f"Final card size: {self.card_width*25.4/300:.1f}×{self.card_height*25.4/300:.1f}mm (content + {passepartout_mm}mm passepartout)", request_id=self.request_id)
        debug(f"Layout: {GRID_COLS}×{GRID_ROWS} grid = {self.layout_width}×{self.layout_height}px", request_id=self.request_id)
        debug(f"UNUSED space: {unused_width}×{unused_height}px ({unused_width*25.4/300:.1f}×{unused_height*25.4/300:.1f}mm)", request_id=self.request_id)
        debug(f"Guillotine spacing: {self.actual_spacing_x}px = {TOTAL_SPACING_MM}mm (minimal for guillotine)", request_id=self.request_id)
        if passepartout_mm > 0:
            debug(f"Passepartout: {passepartout_mm}mm = {self.passepartout_px}px (equal on all sides)", request_id=self.request_id)
    
    def create_canvas(self, background_color: str = "#FFFFFF") -> None:
        """Create A4 canvas with proper dimensions"""
        self.canvas = Image.new('RGB', (A4_WIDTH_PX, A4_HEIGHT_PX), background_color)
        self.draw = ImageDraw.Draw(self.canvas)
        log(f"Created A4 canvas: {A4_WIDTH_PX}×{A4_HEIGHT_PX}px ({A4_WIDTH_MM}×{A4_HEIGHT_MM}mm)", request_id=self.request_id)
    
    def get_card_position(self, grid_x: int, grid_y: int) -> Tuple[int, int]:
        """
        Calculate exact pixel position for a card in the 3×2 grid.
        
        Args:
            grid_x: Column position (0-2)
            grid_y: Row position (0-1)
            
        Returns:
            Tuple of (x, y) pixel coordinates for top-left corner
        """
        if not (0 <= grid_x < GRID_COLS and 0 <= grid_y < GRID_ROWS):
            raise ValueError(f"Invalid grid position: ({grid_x}, {grid_y}). Valid range: (0-{GRID_COLS-1}, 0-{GRID_ROWS-1})")
        
        x = self.offset_x + grid_x * (self.card_width + self.actual_spacing_x)
        y = self.offset_y + grid_y * (self.card_height + self.actual_spacing_y)
        
        debug(f"Card position [{grid_x},{grid_y}]: ({x}, {y})", request_id=self.request_id)
        return x, y
    
    def place_card(self, card_image: Image.Image, grid_x: int, grid_y: int) -> None:
        """
        Place a card with your approach: content size + passepartout = final size.
        
        Args:
            card_image: PIL Image of the card (original portrait CARD_WIDTH × CARD_HEIGHT)
            grid_x: Column position (0 for single column)
            grid_y: Row position (0-2 for 3 rows)
        """
        if not self.canvas:
            raise RuntimeError("Canvas not created. Call create_canvas() first.")
        
        # STEP 1: Rotate portrait card to landscape (90° counter-clockwise)
        if card_image.size == (CARD_WIDTH, CARD_HEIGHT):  # Portrait 708×1416
            rotated_card = card_image.rotate(90, expand=True)  # Now 1416×708 landscape
            debug(f"Rotated card from {card_image.size} portrait to {rotated_card.size} landscape", request_id=self.request_id)
        else:
            rotated_card = card_image  # Already correct size/orientation
            debug(f"Using card as-is: {card_image.size}", request_id=self.request_id)
        
        # STEP 2: Scale rotated card to EXACT target content size (14.6×7.3cm)
        # This ensures 2:1 ratio with no white space around content
        scaled_card = rotated_card.resize((TARGET_CONTENT_WIDTH_PX, TARGET_CONTENT_HEIGHT_PX), Image.Resampling.LANCZOS)
        
        scale_factor = TARGET_CONTENT_WIDTH_PX / rotated_card.size[0]  # Calculate for debug
        debug(f"Scaled to EXACT content size: {rotated_card.size} → {scaled_card.size} (scale={scale_factor:.3f})", request_id=self.request_id)
        
        # STEP 3: Create final card with passepartout (if specified)
        # Create canvas for final card size (content + passepartout)
        final_card = Image.new('RGB', (self.card_width, self.card_height), 'white')
        
        if self.passepartout_mm > 0:
            # Place content with exact passepartout borders
            paste_x = self.passepartout_px
            paste_y = self.passepartout_px
            debug(f"Placing content with {self.passepartout_mm}mm ({self.passepartout_px}px) passepartout borders", request_id=self.request_id)
        else:
            # No passepartout - content fills entire final card (same size)
            paste_x = 0
            paste_y = 0
            debug(f"No passepartout - content fills entire card", request_id=self.request_id)
        
        # Convert RGBA to RGB if needed (for TIFF compatibility)
        if scaled_card.mode == 'RGBA':
            rgb_image = Image.new('RGB', scaled_card.size, 'white')
            rgb_image.paste(scaled_card, mask=scaled_card.split()[-1])
            scaled_card = rgb_image
        
        final_card.paste(scaled_card, (paste_x, paste_y))
        
        # STEP 5: Place final card on A4 canvas
        x, y = self.get_card_position(grid_x, grid_y)
        self.canvas.paste(final_card, (x, y))
        
        # Calculate final size in cm for verification
        final_width_cm = self.card_width * 25.4 / 300
        final_height_cm = self.card_height * 25.4 / 300
        content_width_cm = TARGET_CONTENT_WIDTH_MM / 10  # Convert mm to cm
        content_height_cm = TARGET_CONTENT_HEIGHT_MM / 10
        
        debug(f"Placed card at [{grid_x},{grid_y}]: final size {final_width_cm:.1f}×{final_height_cm:.1f}cm, content {content_width_cm:.1f}×{content_height_cm:.1f}cm", request_id=self.request_id)
    
    # Passepartout logic moved to place_card() method for correct calculation approach
    
    def draw_cutting_guides(self) -> None:
        """Draw guillotine cutting guides for 1×3 landscape layout with kerf considerations"""
        if not self.draw:
            raise RuntimeError("Canvas not created. Call create_canvas() first.")
        
        cutting_lines_added = []
        
        # For 1×3 grid: NO vertical cuts needed (single column)
        # Only horizontal cuts between rows
        
        # Draw horizontal cutting lines between rows (for guillotine)
        for grid_y in range(GRID_ROWS - 1):  # Between rows only (2 cuts for 3 rows)
            # Get positions of adjacent cards
            top_card_x, top_card_y = self.get_card_position(0, grid_y)
            bottom_card_x, bottom_card_y = self.get_card_position(0, grid_y + 1)
            
            # Guillotine cut position - center of spacing between cards
            cut_y = top_card_y + self.card_height + (self.actual_spacing_y // 2)
            
            # Draw horizontal cut line across full width
            self._draw_dashed_line(
                (0, cut_y), 
                (A4_WIDTH_PX, cut_y), 
                CUTTING_LINE_COLOR, 
                CUTTING_LINE_WIDTH
            )
            
            cutting_lines_added.append(f"Row {grid_y+1}-{grid_y+2} at {cut_y}px")
            debug(f"Guillotine cut between row {grid_y+1}-{grid_y+2} at y={cut_y}px", request_id=self.request_id)
        
        # OUTER CUTTING LINES: Show where to trim unused areas
        unused_width = A4_WIDTH_PX - self.layout_width
        unused_height = A4_HEIGHT_PX - self.layout_height
        
        # Right edge trim line (if significant unused width)
        if unused_width > 10:  # >0.8mm
            right_trim_x = self.offset_x + self.layout_width
            self._draw_dashed_line(
                (right_trim_x, 0), 
                (right_trim_x, A4_HEIGHT_PX), 
                CUTTING_LINE_COLOR, 
                CUTTING_LINE_WIDTH
            )
            cutting_lines_added.append(f"Right trim at {right_trim_x}px")
            debug(f"RIGHT trim line at {right_trim_x}px (unused: {unused_width}px = {unused_width*25.4/300:.1f}mm)", request_id=self.request_id)
        
        # Bottom edge trim line (if significant unused height)
        if unused_height > 10:  # >0.8mm
            bottom_trim_y = self.offset_y + self.layout_height
            self._draw_dashed_line(
                (0, bottom_trim_y), 
                (A4_WIDTH_PX, bottom_trim_y), 
                CUTTING_LINE_COLOR, 
                CUTTING_LINE_WIDTH
            )
            cutting_lines_added.append(f"Bottom trim at {bottom_trim_y}px")
            debug(f"BOTTOM trim line at {bottom_trim_y}px (unused: {unused_height}px = {unused_height*25.4/300:.1f}mm)", request_id=self.request_id)
        
        # Summary
        num_horizontal_cuts = GRID_ROWS - 1  # 2 cuts for 3 rows
        total_cuts = num_horizontal_cuts + (1 if unused_height > 10 else 0)
        
        log(f"Guillotine cutting guides: {num_horizontal_cuts} horizontal cuts + bottom trim = {total_cuts} total cuts", request_id=self.request_id)
        log(f"Cuts added: {'; '.join(cutting_lines_added)}", request_id=self.request_id)
    
    def _draw_cutting_rectangle(self, left: int, top: int, right: int, bottom: int, width: int = None) -> None:
        """Draw a dashed rectangle for cutting guides"""
        if width is None:
            width = CUTTING_LINE_WIDTH
            
        # Draw four sides of rectangle
        self._draw_dashed_line((left, top), (right, top), CUTTING_LINE_COLOR, width)      # Top
        self._draw_dashed_line((right, top), (right, bottom), CUTTING_LINE_COLOR, width)  # Right  
        self._draw_dashed_line((right, bottom), (left, bottom), CUTTING_LINE_COLOR, width) # Bottom
        self._draw_dashed_line((left, bottom), (left, top), CUTTING_LINE_COLOR, width)    # Left
    
    def _draw_crop_marks(self, left: int, top: int, right: int, bottom: int) -> None:
        """Draw corner crop marks for precision cutting"""
        mark_length = 20  # Length of crop marks in pixels
        
        # Top-left corner
        self.draw.line([(left - mark_length, top), (left + mark_length, top)], fill=CUTTING_LINE_COLOR, width=2)
        self.draw.line([(left, top - mark_length), (left, top + mark_length)], fill=CUTTING_LINE_COLOR, width=2)
        
        # Top-right corner  
        self.draw.line([(right - mark_length, top), (right + mark_length, top)], fill=CUTTING_LINE_COLOR, width=2)
        self.draw.line([(right, top - mark_length), (right, top + mark_length)], fill=CUTTING_LINE_COLOR, width=2)
        
        # Bottom-left corner
        self.draw.line([(left - mark_length, bottom), (left + mark_length, bottom)], fill=CUTTING_LINE_COLOR, width=2)
        self.draw.line([(left, bottom - mark_length), (left, bottom + mark_length)], fill=CUTTING_LINE_COLOR, width=2)
        
        # Bottom-right corner
        self.draw.line([(right - mark_length, bottom), (right + mark_length, bottom)], fill=CUTTING_LINE_COLOR, width=2)
        self.draw.line([(right, bottom - mark_length), (right, bottom + mark_length)], fill=CUTTING_LINE_COLOR, width=2)
    
    def _draw_dashed_line(self, start: Tuple[int, int], end: Tuple[int, int], 
                         color: str, width: int) -> None:
        """Draw a dashed line between two points"""
        x1, y1 = start
        x2, y2 = end
        
        # Calculate line length and direction
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if length == 0:
            return
        
        # Unit vector
        dx = (x2 - x1) / length
        dy = (y2 - y1) / length
        
        # Draw dashed segments
        current_pos = 0
        while current_pos < length:
            # Dash segment
            dash_end = min(current_pos + CUTTING_LINE_DASH_LENGTH, length)
            dash_x1 = x1 + dx * current_pos
            dash_y1 = y1 + dy * current_pos
            dash_x2 = x1 + dx * dash_end
            dash_y2 = y1 + dy * dash_end
            
            self.draw.line([(dash_x1, dash_y1), (dash_x2, dash_y2)], fill=color, width=width)
            
            # Move to next dash (skip gap)
            current_pos += CUTTING_LINE_DASH_LENGTH * 2
    
    def add_print_info(self, text: str, position: str = "bottom_right") -> None:
        """
        Add small print information text to the layout.
        
        Args:
            text: Information text to display
            position: Where to place it ("bottom_right", "bottom_left", etc.)
        """
        if not self.draw:
            raise RuntimeError("Canvas not created. Call create_canvas() first.")
        
        from .card_utils import get_font
        
        # Small font for print info
        font = get_font(24, "Light", font_family="Mono", request_id=self.request_id)
        
        # Calculate text dimensions
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Position text (using 0 margins for full page usage)
        margin_px = int(A4_MARGINS_MM * MM_TO_PIXELS)  # 0px since A4_MARGINS_MM = 0
        
        if position == "bottom_right":
            x = A4_WIDTH_PX - margin_px - text_width
            y = A4_HEIGHT_PX - margin_px - text_height
        elif position == "bottom_left":
            x = margin_px
            y = A4_HEIGHT_PX - margin_px - text_height
        else:
            x = margin_px
            y = margin_px
        
        self.draw.text((x, y), text, fill="#666666", font=font)
        debug(f"Added print info at {position}: '{text}'", request_id=self.request_id)
    
    def save_layout(self, output_format: str = "TIFF") -> bytes:
        """
        Save the A4 layout as TIFF or PNG.
        
        Args:
            output_format: "TIFF" for print, "PNG" for preview
            
        Returns:
            Image bytes in specified format
        """
        if not self.canvas:
            raise RuntimeError("Canvas not created. Call create_canvas() first.")
        
        img_byte_arr = io.BytesIO()
        
        if output_format.upper() == "TIFF":
            # Save as TIFF with professional print settings
            self.canvas.save(
                img_byte_arr, 
                format='TIFF',
                compression='lzw',  # Lossless compression
                dpi=(PRINT_DPI, PRINT_DPI)  # 300 DPI metadata
            )
            debug(f"Saved A4 layout as TIFF with LZW compression at {PRINT_DPI} DPI", request_id=self.request_id)
        else:
            # Save as PNG for preview
            self.canvas.save(
                img_byte_arr, 
                format='PNG', 
                compress_level=2
            )
            debug(f"Saved A4 layout as PNG with compression level 2", request_id=self.request_id)
        
        layout_bytes = img_byte_arr.getvalue()
        log(f"A4 layout saved ({output_format}). Size: {len(layout_bytes)/1024:.2f}KB", request_id=self.request_id)
        return layout_bytes

# Grid position constants for 1×3 layout (single column, 3 rows)
GRID_POSITIONS = {
    'top': (0, 0),     # Top card
    'middle': (0, 1),  # Middle card  
    'bottom': (0, 2)   # Bottom card
}

def create_a4_layout_with_cards(card_images: List[Image.Image],
                               target_content_width_mm: float = 146,
                               passepartout_mm: float = 8,
                               request_id: Optional[str] = None) -> bytes:
    """
    Create an A4 layout with up to 3 landscape card images.

    Args:
        card_images: List of PIL Images (up to 3 cards - portrait cards will be rotated to landscape)
        target_content_width_mm: The desired width of the card's content in millimeters.
                                 Height will be calculated to maintain a 2:1 aspect ratio.
        passepartout_mm: White border to add around the content in millimeters.
        request_id: Request tracking ID.

    Returns:
        A4 layout image as TIFF bytes.
    """
    max_cards = GRID_COLS * GRID_ROWS
    if len(card_images) > max_cards:
        log(f"Too many cards provided: {len(card_images)}. Maximum is {max_cards}.", level="WARNING", request_id=request_id)
        card_images = card_images[:max_cards]

    log(f"Creating A4 layout for {len(card_images)} cards: "
        f"{target_content_width_mm}mm content width + {passepartout_mm}mm passepartout.",
        request_id=request_id)

    layout = A4Layout(
        target_content_width_mm=target_content_width_mm,
        passepartout_mm=passepartout_mm,
        request_id=request_id
    )
    layout.create_canvas()

    for i, card_image in enumerate(card_images):
        grid_x = i % GRID_COLS
        grid_y = i // GRID_COLS
        layout.place_card(card_image, grid_x, grid_y)

    layout.draw_cutting_guides()

    return layout.save_layout() 