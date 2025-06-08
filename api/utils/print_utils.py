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

# Layout specifications
GRID_COLS = 3  # 3 cards wide
GRID_ROWS = 2  # 2 cards tall
A4_MARGINS_MM = 15          # Outer A4 margins
CUTTING_ZONE_MM = 13.5      # Top/bottom cutting areas

# Convert to pixels
A4_MARGINS_PX = int(A4_MARGINS_MM * MM_TO_PIXELS)
CUTTING_ZONE_PX = int(CUTTING_ZONE_MM * MM_TO_PIXELS)

# Cutting guide appearance
CUTTING_LINE_COLOR = "#CCCCCC"
CUTTING_LINE_WIDTH = 2  # pixels
CUTTING_LINE_DASH_LENGTH = 6  # pixels

# Card spacing (tight layout for maximum efficiency)
CARD_SPACING_MM = 0  # No spacing between cards
CARD_SPACING_PX = int(CARD_SPACING_MM * MM_TO_PIXELS)

def mm_to_px(mm: float) -> int:
    """Convert millimeters to pixels at 300 DPI"""
    return int(mm * MM_TO_PIXELS)

def px_to_mm(px: int) -> float:
    """Convert pixels to millimeters at 300 DPI"""
    return px / MM_TO_PIXELS

class A4Layout:
    """
    A4 layout engine for professional postcard printing.
    Handles exact positioning, cutting guides, and print alignment.
    """
    
    def __init__(self, request_id: Optional[str] = None):
        self.request_id = request_id
        self.canvas = None
        self.draw = None
        
        # Calculate layout dimensions
        self.layout_width = GRID_COLS * CARD_WIDTH + (GRID_COLS - 1) * CARD_SPACING_PX
        self.layout_height = GRID_ROWS * CARD_HEIGHT + (GRID_ROWS - 1) * CARD_SPACING_PX
        
        # Calculate centering offsets
        self.offset_x = (A4_WIDTH_PX - self.layout_width) // 2
        self.offset_y = (A4_HEIGHT_PX - self.layout_height) // 2
        
        debug(f"A4 Layout initialized: {A4_WIDTH_PX}×{A4_HEIGHT_PX}px", request_id=self.request_id)
        debug(f"Card layout: {self.layout_width}×{self.layout_height}px", request_id=self.request_id)
        debug(f"Centering offset: {self.offset_x}, {self.offset_y}", request_id=self.request_id)
    
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
        
        x = self.offset_x + grid_x * (CARD_WIDTH + CARD_SPACING_PX)
        y = self.offset_y + grid_y * (CARD_HEIGHT + CARD_SPACING_PX)
        
        debug(f"Card position [{grid_x},{grid_y}]: ({x}, {y})", request_id=self.request_id)
        return x, y
    
    def place_card(self, card_image: Image.Image, grid_x: int, grid_y: int) -> None:
        """
        Place a card image at the specified grid position.
        
        Args:
            card_image: PIL Image of the card (should be CARD_WIDTH × CARD_HEIGHT)
            grid_x: Column position (0-2)
            grid_y: Row position (0-1)
        """
        if not self.canvas:
            raise RuntimeError("Canvas not created. Call create_canvas() first.")
        
        # Verify card dimensions
        if card_image.size != (CARD_WIDTH, CARD_HEIGHT):
            log(f"Warning: Card image size {card_image.size} doesn't match expected {CARD_WIDTH}×{CARD_HEIGHT}", 
                level="WARNING", request_id=self.request_id)
        
        x, y = self.get_card_position(grid_x, grid_y)
        
        # Convert RGBA to RGB if needed (for TIFF compatibility)
        if card_image.mode == 'RGBA':
            rgb_image = Image.new('RGB', card_image.size, 'white')
            rgb_image.paste(card_image, mask=card_image.split()[-1])
            card_image = rgb_image
        
        self.canvas.paste(card_image, (x, y))
        debug(f"Placed card at grid [{grid_x},{grid_y}] → pixel ({x}, {y})", request_id=self.request_id)
    
    def draw_cutting_guides(self) -> None:
        """Draw cutting guide lines around the card layout area"""
        if not self.draw:
            raise RuntimeError("Canvas not created. Call create_canvas() first.")
        
        # Calculate cutting zone boundaries
        top_cutting_y = self.offset_y - CUTTING_ZONE_PX
        bottom_cutting_y = self.offset_y + self.layout_height + CUTTING_ZONE_PX
        left_cutting_x = self.offset_x - CUTTING_ZONE_PX
        right_cutting_x = self.offset_x + self.layout_width + CUTTING_ZONE_PX
        
        # Ensure boundaries are within A4 canvas
        top_cutting_y = max(A4_MARGINS_PX, top_cutting_y)
        bottom_cutting_y = min(A4_HEIGHT_PX - A4_MARGINS_PX, bottom_cutting_y)
        left_cutting_x = max(A4_MARGINS_PX, left_cutting_x)
        right_cutting_x = min(A4_WIDTH_PX - A4_MARGINS_PX, right_cutting_x)
        
        # Draw horizontal cutting lines (top and bottom)
        self._draw_dashed_line(
            (left_cutting_x, top_cutting_y), 
            (right_cutting_x, top_cutting_y), 
            CUTTING_LINE_COLOR, CUTTING_LINE_WIDTH
        )
        self._draw_dashed_line(
            (left_cutting_x, bottom_cutting_y), 
            (right_cutting_x, bottom_cutting_y), 
            CUTTING_LINE_COLOR, CUTTING_LINE_WIDTH
        )
        
        # Draw vertical cutting lines (left and right)
        self._draw_dashed_line(
            (left_cutting_x, top_cutting_y), 
            (left_cutting_x, bottom_cutting_y), 
            CUTTING_LINE_COLOR, CUTTING_LINE_WIDTH
        )
        self._draw_dashed_line(
            (right_cutting_x, top_cutting_y), 
            (right_cutting_x, bottom_cutting_y), 
            CUTTING_LINE_COLOR, CUTTING_LINE_WIDTH
        )
        
        log(f"Added cutting guides at margins: {px_to_mm(CUTTING_ZONE_PX):.1f}mm", request_id=self.request_id)
    
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
        
        # Position text
        if position == "bottom_right":
            x = A4_WIDTH_PX - A4_MARGINS_PX - text_width
            y = A4_HEIGHT_PX - A4_MARGINS_PX - text_height
        elif position == "bottom_left":
            x = A4_MARGINS_PX
            y = A4_HEIGHT_PX - A4_MARGINS_PX - text_height
        else:
            x = A4_MARGINS_PX
            y = A4_MARGINS_PX
        
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

# Grid position constants for easy reference
GRID_POSITIONS = {
    'top_left': (0, 0),     'top_center': (1, 0),     'top_right': (2, 0),
    'bottom_left': (0, 1),  'bottom_center': (1, 1),  'bottom_right': (2, 1)
}

def create_a4_layout_with_cards(card_images: List[Image.Image], 
                               layout_title: Optional[str] = None,
                               output_format: str = "TIFF",
                               request_id: Optional[str] = None) -> bytes:
    """
    Create an A4 layout with up to 6 card images.
    
    Args:
        card_images: List of PIL Images (up to 6 cards)
        layout_title: Optional title for the layout
        output_format: "TIFF" for print, "PNG" for preview
        request_id: Request tracking ID
        
    Returns:
        A4 layout image bytes
    """
    if len(card_images) > 6:
        log(f"Too many cards provided: {len(card_images)}. Maximum is 6.", level="WARNING", request_id=request_id)
        card_images = card_images[:6]
    
    log(f"Creating A4 layout with {len(card_images)} cards", request_id=request_id)
    
    # Create layout
    layout = A4Layout(request_id=request_id)
    layout.create_canvas()
    
    # Place cards in grid (left-to-right, top-to-bottom)
    for i, card_image in enumerate(card_images):
        grid_x = i % GRID_COLS
        grid_y = i // GRID_COLS
        layout.place_card(card_image, grid_x, grid_y)
    
    # Add cutting guides
    layout.draw_cutting_guides()
    
    # Add print information
    if layout_title:
        layout.add_print_info(f"{layout_title} | 300 DPI | A4", "bottom_right")
    else:
        layout.add_print_info("ShadeFreude Postcards | 300 DPI | A4", "bottom_right")
    
    # Save and return
    return layout.save_layout(output_format) 