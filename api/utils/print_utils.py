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

# Target card dimensions: 8×16cm landscape (rotated from portrait)
TARGET_CARD_WIDTH_MM = 160  # 16cm wide in landscape
TARGET_CARD_HEIGHT_MM = 80  # 8cm tall in landscape  
TARGET_CARD_WIDTH_PX = int(TARGET_CARD_WIDTH_MM * MM_TO_PIXELS)  # 1890px
TARGET_CARD_HEIGHT_PX = int(TARGET_CARD_HEIGHT_MM * MM_TO_PIXELS)  # 945px

# Guillotine considerations - MINIMAL 1mm spacing for maximum card size
TOTAL_SPACING_MM = 1  # 1mm total spacing (ultra-minimal for guillotine)
SPACING_PX = int(TOTAL_SPACING_MM * MM_TO_PIXELS)  # ~12px

# Cutting guide appearance  
CUTTING_LINE_COLOR = "#333333"  # Much darker gray for visibility
CUTTING_LINE_WIDTH = 1  # pixels - thicker lines
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
        
        # NEW: Calculate exact landscape card dimensions for 8×16cm target
        # Current portrait card: 708×1416px → rotated to 1416×708px landscape
        current_landscape_w = CARD_HEIGHT  # 1416px (rotated width)
        current_landscape_h = CARD_WIDTH   # 708px (rotated height)
        
        # Scale to achieve target 8×16cm (1890×945px) landscape size
        scale_factor_w = TARGET_CARD_WIDTH_PX / current_landscape_w   # 1890/1416 ≈ 1.335
        scale_factor_h = TARGET_CARD_HEIGHT_PX / current_landscape_h  # 945/708 ≈ 1.335
        scale_factor = min(scale_factor_w, scale_factor_h)  # Use smaller to maintain aspect ratio
        
        # Final card dimensions after scaling rotated cards
        self.card_width = int(current_landscape_w * scale_factor)   # ~1888px
        self.card_height = int(current_landscape_h * scale_factor)  # ~944px
        
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
        debug(f"Target: {TARGET_CARD_WIDTH_PX}×{TARGET_CARD_HEIGHT_PX}px ({TARGET_CARD_WIDTH_MM}×{TARGET_CARD_HEIGHT_MM}mm)", request_id=self.request_id)
        debug(f"ACTUAL card size: {self.card_width}×{self.card_height}px ({self.card_width*25.4/300:.1f}×{self.card_height*25.4/300:.1f}mm)", request_id=self.request_id)
        debug(f"Scale factor: {scale_factor:.3f} (rotated {CARD_WIDTH}×{CARD_HEIGHT} → {self.card_width}×{self.card_height})", request_id=self.request_id)
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
        Place a card image at the specified grid position with rotation and optional passepartout.
        
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
        
        # STEP 2: Scale rotated card to target landscape dimensions (1888×944)
        if rotated_card.size != (self.card_width, self.card_height):
            scaled_card = rotated_card.resize((self.card_width, self.card_height), Image.Resampling.LANCZOS)
            debug(f"Scaled rotated card from {rotated_card.size} to target {self.card_width}×{self.card_height}px", request_id=self.request_id)
        else:
            scaled_card = rotated_card
        
        x, y = self.get_card_position(grid_x, grid_y)
        
        # Convert RGBA to RGB if needed (for TIFF compatibility)
        if scaled_card.mode == 'RGBA':
            rgb_image = Image.new('RGB', scaled_card.size, 'white')
            rgb_image.paste(scaled_card, mask=scaled_card.split()[-1])
            scaled_card = rgb_image
        
        # Apply passepartout if specified
        if self.passepartout_mm > 0:
            final_card = self._apply_passepartout_to_card(scaled_card)
            debug(f"Applied {self.passepartout_mm}mm passepartout to card at [{grid_x},{grid_y}]", request_id=self.request_id)
        else:
            final_card = scaled_card
        
        self.canvas.paste(final_card, (x, y))
        debug(f"Placed landscape card at grid [{grid_x},{grid_y}] → pixel ({x}, {y})", request_id=self.request_id)
    
    def _apply_passepartout_to_card(self, card_image: Image.Image) -> Image.Image:
        """
        Apply EXACTLY equal passepartout borders on all sides.
        
        Args:
            card_image: Original card image
            
        Returns:
            Card image with precisely equal passepartout borders
        """
        # Get current card dimensions (layout space allocated for this card)
        card_width, card_height = card_image.size
        
        # Calculate content area (space inside passepartout borders)
        content_width = card_width - (2 * self.passepartout_px)
        content_height = card_height - (2 * self.passepartout_px)
        
        # Ensure content area is positive
        if content_width <= 0 or content_height <= 0:
            debug(f"Passepartout too large: {self.passepartout_px}px borders on {card_width}×{card_height}px card", request_id=self.request_id)
            return card_image
        
        # Scale card to fit exactly within content area, maintaining aspect ratio
        scale_x = content_width / card_width
        scale_y = content_height / card_height
        scale_factor = min(scale_x, scale_y)  # Use smaller scale to ensure it fits
        
        # Calculate final scaled dimensions
        final_width = int(card_width * scale_factor)
        final_height = int(card_height * scale_factor)
        
        # Scale the card
        scaled_card = card_image.resize((final_width, final_height), Image.Resampling.LANCZOS)
        
        # Create white background canvas (full card space)
        white_canvas = Image.new('RGB', (card_width, card_height), 'white')
        
        # Position to create EXACTLY equal borders on all sides
        # Calculate borders to be exactly passepartout_px on all sides
        border_x = self.passepartout_px
        border_y = self.passepartout_px
        
        # Place scaled card with exact borders
        white_canvas.paste(scaled_card, (border_x, border_y))
        
        # Verify actual borders
        actual_border_right = card_width - border_x - final_width
        actual_border_bottom = card_height - border_y - final_height
        
        debug(f"EXACT passepartout: L={border_x}px R={actual_border_right}px T={border_y}px B={actual_border_bottom}px, scale={scale_factor:.3f}", request_id=self.request_id)
        return white_canvas
    
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
                               layout_title: Optional[str] = None,
                               output_format: str = "TIFF",
                               passepartout_mm: float = 0,
                               request_id: Optional[str] = None) -> bytes:
    """
    Create an A4 layout with up to 3 landscape card images (8×16cm each) and optional passepartout.
    
    Args:
        card_images: List of PIL Images (up to 3 cards - portrait cards will be rotated to landscape)
        layout_title: Optional title for the layout
        output_format: "TIFF" for print, "PNG" for preview
        passepartout_mm: White border around each card in millimeters (0 = no passepartout)
        request_id: Request tracking ID
        
    Returns:
        A4 layout image bytes with 3 landscape cards in 1×3 grid
    """
    max_cards = GRID_COLS * GRID_ROWS  # 1×3 = 3 cards max
    
    if len(card_images) > max_cards:
        log(f"Too many cards provided: {len(card_images)}. Maximum is {max_cards} for {GRID_COLS}×{GRID_ROWS} layout.", level="WARNING", request_id=request_id)
        card_images = card_images[:max_cards]
    
    log(f"Creating NEW A4 layout: {len(card_images)} landscape cards ({TARGET_CARD_WIDTH_MM}×{TARGET_CARD_HEIGHT_MM}mm each), passepartout: {passepartout_mm}mm", request_id=request_id)
    
    # Create layout with passepartout and guillotine considerations
    layout = A4Layout(request_id=request_id, passepartout_mm=passepartout_mm)
    layout.create_canvas()
    
    # Place cards in 1×3 grid (single column, top-to-bottom)
    for i, card_image in enumerate(card_images):
        grid_x = 0  # Always column 0 (single column)
        grid_y = i  # Row index (0, 1, 2)
        layout.place_card(card_image, grid_x, grid_y)
    
    # Add guillotine cutting guides
    layout.draw_cutting_guides()
    
    # No print information text - removed per user request
    
    # Save and return
    return layout.save_layout(output_format) 