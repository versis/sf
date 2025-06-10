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
A4_MARGINS_MM = 0           # No margins - use full page area
CUTTING_ZONE_MM = 3         # Reduced cutting areas for more card space

# Convert to pixels
A4_MARGINS_PX = int(A4_MARGINS_MM * MM_TO_PIXELS)
CUTTING_ZONE_PX = int(CUTTING_ZONE_MM * MM_TO_PIXELS)

# Cutting guide appearance
CUTTING_LINE_COLOR = "#333333"  # Much darker gray for visibility
CUTTING_LINE_WIDTH = 1  # pixels - thicker lines
CUTTING_LINE_DASH_LENGTH = 12  # pixels - longer dashes

# Card spacing (small gap for easier cutting)
CARD_SPACING_MM = 3  # 3mm spacing between cards for easier cutting
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
    Handles exact positioning, cutting guides, print alignment, and passepartout.
    """
    
    def __init__(self, request_id: Optional[str] = None, passepartout_mm: float = 0):
        self.request_id = request_id
        self.passepartout_mm = passepartout_mm
        self.passepartout_px = int(passepartout_mm * MM_TO_PIXELS) if passepartout_mm > 0 else 0
        self.canvas = None
        self.draw = None
        
        # Calculate optimal card size to maximize page usage
        desired_spacing_x = 40  # ~3.4mm spacing between cards
        desired_spacing_y = 40  # ~3.4mm spacing between rows
        
        # Calculate maximum card dimensions while maintaining 1:2 ratio
        available_width_for_cards = A4_WIDTH_PX - (GRID_COLS - 1) * desired_spacing_x
        available_height_for_cards = A4_HEIGHT_PX - (GRID_ROWS - 1) * desired_spacing_y
        
        # Calculate optimal card width/height maintaining 1:2 ratio (width:height = 1:2)
        max_card_width_from_width = available_width_for_cards // GRID_COLS
        max_card_width_from_height = available_height_for_cards // (GRID_ROWS * 2)  # height = 2*width for 1:2 ratio
        
        # Use the smaller constraint to ensure cards fit
        optimal_card_width = min(max_card_width_from_width, max_card_width_from_height)
        optimal_card_height = optimal_card_width * 2  # Maintain 1:2 ratio
        
        # Store optimal card dimensions
        self.card_width = optimal_card_width
        self.card_height = optimal_card_height
        
        # Calculate actual spacing with optimal card size
        self.actual_spacing_x = (A4_WIDTH_PX - GRID_COLS * self.card_width) // (GRID_COLS - 1) if GRID_COLS > 1 else 0
        self.actual_spacing_y = (A4_HEIGHT_PX - GRID_ROWS * self.card_height) // (GRID_ROWS - 1) if GRID_ROWS > 1 else 0
        
        # Layout fills entire page
        self.layout_width = A4_WIDTH_PX
        self.layout_height = A4_HEIGHT_PX
        self.offset_x = 0
        self.offset_y = 0
        
        debug(f"A4 Layout initialized: {A4_WIDTH_PX}×{A4_HEIGHT_PX}px (full page)", request_id=self.request_id)
        debug(f"Optimal card size: {self.card_width}×{self.card_height}px (vs original {CARD_WIDTH}×{CARD_HEIGHT}px)", request_id=self.request_id)
        debug(f"Card spacing: {self.actual_spacing_x}px×{self.actual_spacing_y}px", request_id=self.request_id)
        debug(f"Offset: {self.offset_x}, {self.offset_y} (no centering)", request_id=self.request_id)
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
        Place a card image at the specified grid position with optional passepartout.
        
        Args:
            card_image: PIL Image of the card (should be CARD_WIDTH × CARD_HEIGHT)
            grid_x: Column position (0-2)
            grid_y: Row position (0-1)
        """
        if not self.canvas:
            raise RuntimeError("Canvas not created. Call create_canvas() first.")
        
        # Resize card to optimal size (scale up from original size)
        if card_image.size != (self.card_width, self.card_height):
            debug(f"Resizing card from {card_image.size} to optimal {self.card_width}×{self.card_height}px", request_id=self.request_id)
            card_image = card_image.resize((self.card_width, self.card_height), Image.Resampling.LANCZOS)
        
        x, y = self.get_card_position(grid_x, grid_y)
        
        # Convert RGBA to RGB if needed (for TIFF compatibility)
        if card_image.mode == 'RGBA':
            rgb_image = Image.new('RGB', card_image.size, 'white')
            rgb_image.paste(card_image, mask=card_image.split()[-1])
            card_image = rgb_image
        
        # Apply passepartout if specified
        if self.passepartout_mm > 0:
            final_card = self._apply_passepartout_to_card(card_image)
            debug(f"Applied {self.passepartout_mm}mm passepartout to card at [{grid_x},{grid_y}]", request_id=self.request_id)
        else:
            final_card = card_image
        
        self.canvas.paste(final_card, (x, y))
        debug(f"Placed card at grid [{grid_x},{grid_y}] → pixel ({x}, {y})", request_id=self.request_id)
    
    def _apply_passepartout_to_card(self, card_image: Image.Image) -> Image.Image:
        """
        Apply equal passepartout (white border) on all sides.
        
        Args:
            card_image: Original card image
            
        Returns:
            Card image with equal passepartout applied on all sides
        """
        # Equal passepartout borders on all sides
        passepartout_width = self.passepartout_px   # Same amount for width
        passepartout_height = self.passepartout_px  # Same amount for height
        
        # Get current card dimensions (now optimal size)
        card_width, card_height = card_image.size
        
        # Calculate available space for card content after equal borders
        available_width = card_width - (2 * passepartout_width)
        available_height = card_height - (2 * passepartout_height)
        
        # Calculate scaling factor to fit card within available space
        scale_factor = min(available_width / card_width, available_height / card_height)
        
        # Scale down the card
        new_width = int(card_width * scale_factor)
        new_height = int(card_height * scale_factor)
        scaled_card = card_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create white background canvas (same size as current card space)
        white_canvas = Image.new('RGB', (card_width, card_height), 'white')
        
        # Center the scaled card on the white canvas with equal borders
        paste_x = (card_width - new_width) // 2
        paste_y = (card_height - new_height) // 2
        white_canvas.paste(scaled_card, (paste_x, paste_y))
        
        debug(f"Equal passepartout: {passepartout_width}px×{passepartout_height}px, scale={scale_factor:.3f}", request_id=self.request_id)
        return white_canvas
    
    def draw_cutting_guides(self) -> None:
        """Draw cutting guide lines only between cards (no outer edges, no double lines)"""
        if not self.draw:
            raise RuntimeError("Canvas not created. Call create_canvas() first.")
        
        # Draw vertical cutting lines between columns (not at edges)
        for grid_x in range(GRID_COLS - 1):  # Between columns only
            # Get positions of adjacent cards
            left_card_x, left_card_y = self.get_card_position(grid_x, 0)
            right_card_x, right_card_y = self.get_card_position(grid_x + 1, 0)
            
            # Line position is halfway between the cards
            line_x = left_card_x + self.card_width + (self.actual_spacing_x // 2)
            
            # Draw vertical line from top of layout to bottom
            top_y = self.offset_y
            bottom_y = self.offset_y + self.layout_height
            
            self._draw_dashed_line((line_x, top_y), (line_x, bottom_y), CUTTING_LINE_COLOR, CUTTING_LINE_WIDTH)
        
        # Draw horizontal cutting lines between rows (not at edges)
        for grid_y in range(GRID_ROWS - 1):  # Between rows only
            # Get positions of adjacent cards
            top_card_x, top_card_y = self.get_card_position(0, grid_y)
            bottom_card_x, bottom_card_y = self.get_card_position(0, grid_y + 1)
            
            # Line position is halfway between the cards
            line_y = top_card_y + self.card_height + (self.actual_spacing_y // 2)
            
            # Draw horizontal line from left of layout to right
            left_x = self.offset_x
            right_x = self.offset_x + self.layout_width
            
            self._draw_dashed_line((left_x, line_y), (right_x, line_y), CUTTING_LINE_COLOR, CUTTING_LINE_WIDTH)
        
        log(f"Added cutting guides between cards only (no outer edges, no double lines)", request_id=self.request_id)
    
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
                               passepartout_mm: float = 0,
                               request_id: Optional[str] = None) -> bytes:
    """
    Create an A4 layout with up to 6 card images and optional passepartout.
    
    Args:
        card_images: List of PIL Images (up to 6 cards)
        layout_title: Optional title for the layout
        output_format: "TIFF" for print, "PNG" for preview
        passepartout_mm: White border around each card in millimeters (0 = no passepartout)
        request_id: Request tracking ID
        
    Returns:
        A4 layout image bytes
    """
    if len(card_images) > 6:
        log(f"Too many cards provided: {len(card_images)}. Maximum is 6.", level="WARNING", request_id=request_id)
        card_images = card_images[:6]
    
    log(f"Creating A4 layout with {len(card_images)} cards, passepartout: {passepartout_mm}mm", request_id=request_id)
    
    # Create layout with passepartout
    layout = A4Layout(request_id=request_id, passepartout_mm=passepartout_mm)
    layout.create_canvas()
    
    # Place cards in grid (left-to-right, top-to-bottom)
    for i, card_image in enumerate(card_images):
        grid_x = i % GRID_COLS
        grid_y = i // GRID_COLS
        layout.place_card(card_image, grid_x, grid_y)
    
    # Add cutting guides
    layout.draw_cutting_guides()
    
    # Add print information
    title_suffix = f" | Passepartout: {passepartout_mm}mm" if passepartout_mm > 0 else ""
    if layout_title:
        layout.add_print_info(f"{layout_title} | 300 DPI | A4{title_suffix}", "bottom_right")
    else:
        layout.add_print_info(f"ShadeFreude Postcards | 300 DPI | A4{title_suffix}", "bottom_right")
    
    # Save and return
    return layout.save_layout(output_format) 