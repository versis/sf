"""
PDF Postcard Generator
Generate professional PDF with front and back pages for cards in CMYK color space.

Instructions:
1. Edit the configuration variables below
2. Run: python generate_pdf.py
3. Generated PDF will be saved with CMYK color space for professional printing

Usage Options:
1. Edit configuration variables below and run: python generate_pdf.py
2. Use command line: python generate_pdf.py --generation-name "my_pdf" --ids "000000001 FE F,000000002 FE F" --orientation v
3. Interactive mode: python generate_pdf.py --interactive
"""

import requests
import time
import sys
import os
import argparse
from typing import List, Optional, Dict, Any
import re
from PIL import Image, ImageCms
import io

# PDF generation imports
try:
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import A4, letter, legal
    from reportlab.lib.units import mm, inch
    from reportlab.lib.colors import Color
    from reportlab.lib.utils import ImageReader
    REPORTLAB_AVAILABLE = True
except ImportError:
    print("⚠️  ReportLab not installed. Install with: pip install reportlab")
    REPORTLAB_AVAILABLE = False
    # Define fallback values
    A4 = (595.276, 841.890)  # A4 size in points
    letter = (612, 792)      # US Letter size in points  
    legal = (612, 1008)      # US Legal size in points
    mm = 2.834645669          # Points per millimeter
    inch = 72.0              # Points per inch

# =============================================================================
# CONFIGURATION - EDIT THESE VARIABLES (used when no CLI args provided)
# =============================================================================

# API Configuration  
API_BASE_URL = "http://localhost:3000/api"

# Generation Configuration
GENERATION_NAME = "sfkuba_pdf01"
CARD_IDS = [
    "000000693 FE F",
    "000000694 FE F", 
    "000000695 FE F"
]

# PDF Settings
ORIENTATION = "v"  # "v" for vertical, "h" for horizontal cards
PAGE_SIZE = A4  # A4, letter, legal, or custom (width, height) in points
OUTPUT_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "pdf_generations")
CMYK_CONVERSION = True  # Convert to CMYK color space for professional printing
CARD_QUALITY = "TIFF"  # "TIFF" for print quality, "PNG" for web quality

# =============================================================================
# CONFIGURATION EXAMPLES:
#
# Horizontal orientation:
# ORIENTATION = "h"
#
# Different page size:
# PAGE_SIZE = letter  # US Letter format
# PAGE_SIZE = (200*mm, 300*mm)  # Custom size in millimeters
#
# Web quality (faster generation):
# CARD_QUALITY = "PNG"
# CMYK_CONVERSION = False
#
# Different cards:
# CARD_IDS = ["000000001 FE F", "000000002 FE F"]
#
# Custom generation name:
# GENERATION_NAME = "my_custom_pdf"  # Generates: my_custom_pdf.pdf
#
# =============================================================================

def convert_extended_id_to_simple_id(extended_id: str) -> str:
    """
    Convert extended ID format to simple ID format, preserving the suffix.
    
    Args:
        extended_id: Extended ID like "000000057 FE F"
        
    Returns:
        Simple ID like "000000057FEF" (no spaces or underscores)
    """
    # Remove spaces and underscores but keep all characters
    cleaned = re.sub(r'[^A-Za-z0-9]', '', extended_id)
    return cleaned

def check_dependencies() -> bool:
    """Check if all required dependencies are available."""
    
    if not REPORTLAB_AVAILABLE:
        print("❌ ReportLab is required for PDF generation")
        print("   Install with: pip install reportlab")
        return False
    
    return True

def check_api_status() -> bool:
    """Check if the API is running."""
    
    print("🔍 Checking API status...")
    
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api', '')}", timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running")
            return True
        else:
            print(f"   ⚠️  Server responded with status {response.status_code}")
            # For Next.js, a 500 might be expected for the root endpoint, let's be more lenient
            if response.status_code in [404, 500]:
                print("   ✅ Server appears to be running (Next.js)")
                return True
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Server not reachable: {str(e)}")
        print(f"   💡 Make sure both servers are running:")
        print(f"      1. Next.js: pnpm dev")
        print(f"      2. Python API: uvicorn api.index:app --reload")
        return False

def retrieve_card_details(extended_ids: List[str]) -> Dict[str, Any]:
    """
    Retrieve card details for multiple cards using batch API.
    
    Args:
        extended_ids: List of extended IDs to retrieve
        
    Returns:
        Dictionary mapping extended_id to card data
    """
    print(f"📥 Retrieving details for {len(extended_ids)} cards...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/batch-retrieve-cards",
            json={"extended_ids": extended_ids},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            cards = result.get("cards", {})
            found_count = len([c for c in cards.values() if c is not None])
            print(f"   ✅ Found {found_count}/{len(extended_ids)} cards")
            return cards
        else:
            print(f"   ❌ API error {response.status_code}: {response.text}")
            return {}
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {str(e)}")
        return {}

def generate_card_images(card_data: Dict[str, Any], orientation: str, card_quality: str) -> tuple:
    """
    Generate front and back card images from card data.
    
    Args:
        card_data: Card information from API
        orientation: "v" for vertical, "h" for horizontal
        card_quality: "TIFF" or "PNG"
        
    Returns:
        Tuple of (front_image_bytes, back_image_bytes) or (None, None) if failed
    """
    try:
        # Convert orientation shorthand
        orientation_map = {"v": "vertical", "h": "horizontal"}
        full_orientation = orientation_map.get(orientation, orientation)
        
        # Determine which TIFF URLs to use based on orientation
        if full_orientation == "vertical":
            front_tiff_url = card_data.get("vTiff")
            back_tiff_url = card_data.get("bvTiff")
        else:  # horizontal
            front_tiff_url = card_data.get("hTiff") 
            back_tiff_url = card_data.get("bhTiff")
        
        front_image_bytes = None
        back_image_bytes = None
        
        # Download front card image
        if front_tiff_url:
            response = requests.get(front_tiff_url, timeout=60)
            response.raise_for_status()
            front_image_bytes = response.content
        
        # Download back card image
        if back_tiff_url:
            response = requests.get(back_tiff_url, timeout=60)
            response.raise_for_status()
            back_image_bytes = response.content
            
        return front_image_bytes, back_image_bytes
        
    except Exception as e:
        print(f"      ❌ Failed to generate card images: {str(e)}")
        return None, None

def convert_image_to_cmyk(image_bytes: bytes) -> bytes:
    """
    Convert image from RGB to CMYK color space.
    
    Args:
        image_bytes: Image data in bytes
        
    Returns:
        CMYK image data in bytes
    """
    try:
        # Load image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if not already
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Create CMYK color profile
        rgb_profile = ImageCms.createProfile('sRGB')
        cmyk_profile = ImageCms.createProfile('CMYK')
        
        # Convert RGB to CMYK
        transform = ImageCms.buildTransformFromOpenProfiles(
            rgb_profile, cmyk_profile, 'RGB', 'CMYK'
        )
        cmyk_img = ImageCms.applyTransform(img, transform)
        
        # Save as bytes
        output = io.BytesIO()
        cmyk_img.save(output, format='TIFF', compression='lzw')
        return output.getvalue()
        
    except Exception as e:
        print(f"      ⚠️  CMYK conversion failed: {str(e)}, using original")
        return image_bytes

def create_pdf_with_cards(card_images: List[tuple], output_path: str, page_size: tuple, 
                         cmyk_conversion: bool = True) -> bool:
    """
    Create PDF with front and back pages for each card.
    
    Args:
        card_images: List of (extended_id, front_bytes, back_bytes) tuples
        output_path: Path to save the PDF
        page_size: PDF page size in points (width, height)
        cmyk_conversion: Whether to convert images to CMYK
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create PDF canvas
        pdf = pdf_canvas.Canvas(output_path, pagesize=page_size)
        page_width, page_height = page_size
        
        print(f"   📄 Creating PDF: {page_width:.0f}x{page_height:.0f} points")
        
        total_pages = 0
        
        for extended_id, front_bytes, back_bytes in card_images:
            print(f"   🎨 Adding card {extended_id} to PDF...")
            
            # Process front image
            if front_bytes:
                if cmyk_conversion:
                    front_bytes = convert_image_to_cmyk(front_bytes)
                
                # Load image and calculate dimensions
                front_img = Image.open(io.BytesIO(front_bytes))
                img_width, img_height = front_img.size
                
                # Calculate scaling to fit page while maintaining aspect ratio
                scale_x = (page_width - 20) / img_width  # 10 point margin on each side
                scale_y = (page_height - 20) / img_height  # 10 point margin on each side
                scale = min(scale_x, scale_y)
                
                new_width = img_width * scale
                new_height = img_height * scale
                
                # Center the image on the page
                x = (page_width - new_width) / 2
                y = (page_height - new_height) / 2
                
                # Add front page
                pdf.drawImage(ImageReader(io.BytesIO(front_bytes)), 
                            x, y, width=new_width, height=new_height)
                pdf.showPage()
                total_pages += 1
                
            # Process back image
            if back_bytes:
                if cmyk_conversion:
                    back_bytes = convert_image_to_cmyk(back_bytes)
                
                # Load image and calculate dimensions (same logic as front)
                back_img = Image.open(io.BytesIO(back_bytes))
                img_width, img_height = back_img.size
                
                scale_x = (page_width - 20) / img_width
                scale_y = (page_height - 20) / img_height
                scale = min(scale_x, scale_y)
                
                new_width = img_width * scale
                new_height = img_height * scale
                
                x = (page_width - new_width) / 2
                y = (page_height - new_height) / 2
                
                # Add back page
                pdf.drawImage(ImageReader(io.BytesIO(back_bytes)), 
                            x, y, width=new_width, height=new_height)
                pdf.showPage()
                total_pages += 1
        
        # Save PDF
        pdf.save()
        print(f"   ✅ PDF created with {total_pages} pages")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create PDF: {str(e)}")
        return False

def generate_pdf_from_cards(
    generation_name: str,
    card_ids: List[str], 
    orientation: str = "v",
    page_size: tuple = A4,
    cmyk_conversion: bool = True,
    card_quality: str = "TIFF"
) -> bool:
    """
    Generate PDF with front and back pages for cards.
    
    Args:
        generation_name: Name for the PDF file
        card_ids: List of extended card IDs
        orientation: "v" for vertical, "h" for horizontal
        page_size: PDF page size in points
        cmyk_conversion: Convert to CMYK color space
        card_quality: "TIFF" or "PNG"
        
    Returns:
        True if successful, False otherwise
    """
    
    # Convert orientation shorthand
    orientation_map = {"v": "vertical", "h": "horizontal"}
    full_orientation = orientation_map.get(orientation, orientation)
    
    print(f"📄 Generating PDF: {generation_name}")
    print(f"   🆔 Cards: {len(card_ids)} cards")
    print(f"   📐 Orientation: {full_orientation}")
    print(f"   📄 Page size: {page_size[0]:.0f}x{page_size[1]:.0f} points")
    print(f"   🎨 CMYK conversion: {'ON' if cmyk_conversion else 'OFF'}")
    print(f"   🖼️  Quality: {card_quality}")
    print(f"   📚 Expected pages: {len(card_ids) * 2} (front + back for each card)")
    print()
    
    # Create output directory
    output_dir = OUTPUT_BASE_DIR
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Created directory: {output_dir}")
    
    # Retrieve card details
    card_details = retrieve_card_details(card_ids)
    
    if not card_details:
        print("❌ No card details retrieved. Cannot proceed.")
        return False
    
    # Generate card images
    card_images = []
    total_generated = 0
    
    for extended_id in card_ids:
        card_data = card_details.get(extended_id)
        
        if not card_data:
            print(f"⚠️  Card not found: {extended_id}")
            continue
            
        print(f"🎨 Processing {extended_id}")
        
        # Generate front and back images
        front_bytes, back_bytes = generate_card_images(card_data, orientation, card_quality)
        
        if front_bytes or back_bytes:
            card_images.append((extended_id, front_bytes, back_bytes))
            total_generated += 1
            sides = []
            if front_bytes: sides.append("front")
            if back_bytes: sides.append("back")
            print(f"      ✅ Generated {', '.join(sides)}")
        else:
            print(f"      ❌ Failed to generate images")
    
    if not card_images:
        print("❌ No card images generated. Cannot create PDF.")
        return False
    
    # Create PDF file path
    pdf_filename = f"{generation_name}.pdf"
    pdf_path = os.path.join(output_dir, pdf_filename)
    
    # Generate PDF
    print(f"📄 Creating PDF with {len(card_images)} cards...")
    success = create_pdf_with_cards(card_images, pdf_path, page_size, cmyk_conversion)
    
    if success:
        file_size_mb = os.path.getsize(pdf_path) / 1024 / 1024
        print(f"✅ PDF generated successfully: {pdf_filename} ({file_size_mb:.1f}MB)")
        print(f"📁 Location: {pdf_path}")
        return True
    else:
        print("❌ PDF generation failed!")
        return False

def interactive_mode():
    """Run interactive mode to collect parameters."""
    print("🎯 Interactive Mode")
    print("="*30)
    
    # Get generation name
    generation_name = input("📦 Enter generation name: ").strip()
    if not generation_name:
        print("❌ Generation name cannot be empty")
        return None, None, None, None, None, None
    
    # Get card IDs
    print("🆔 Enter card IDs (one per line, empty line to finish):")
    card_ids = []
    while True:
        card_id = input("   Card ID: ").strip()
        if not card_id:
            break
        card_ids.append(card_id)
    
    if not card_ids:
        print("❌ At least one card ID is required")
        return None, None, None, None, None, None
    
    # Get orientation
    orientation = input("📐 Enter orientation (v for vertical, h for horizontal) [v]: ").strip()
    if not orientation:
        orientation = "v"
    
    if orientation not in ["v", "h"]:
        print(f"❌ Invalid orientation '{orientation}'. Must be 'v' or 'h'")
        return None, None, None, None, None, None
    
    # Get page size
    print("📄 Page size options:")
    print("   1. A4 (210x297mm)")
    print("   2. US Letter (8.5x11in)")
    print("   3. US Legal (8.5x14in)")
    page_choice = input("   Enter choice [1]: ").strip()
    if not page_choice:
        page_choice = "1"
    
    page_size_map = {
        "1": A4,
        "2": letter,
        "3": legal
    }
    page_size = page_size_map.get(page_choice, A4)
    
    # Get CMYK conversion
    cmyk_choice = input("🎨 Convert to CMYK color space for professional printing? (y/n) [y]: ").strip().lower()
    cmyk_conversion = cmyk_choice != "n"
    
    # Get quality
    quality_choice = input("🖼️  Image quality (tiff for print, png for web) [tiff]: ").strip().lower()
    if quality_choice in ["png", "web"]:
        card_quality = "PNG"
    else:
        card_quality = "TIFF"
    
    return generation_name, card_ids, orientation, page_size, cmyk_conversion, card_quality

def print_configuration(generation_name: str, card_ids: List[str], orientation: str, 
                       page_size: tuple, cmyk_conversion: bool, card_quality: str):
    """Print current configuration settings."""
    orientation_display = {"v": "vertical", "h": "horizontal"}.get(orientation, orientation)
    
    # Determine page size name
    page_size_names = {
        A4: "A4 (210x297mm)",
        letter: "US Letter (8.5x11in)", 
        legal: "US Legal (8.5x14in)"
    }
    page_size_name = page_size_names.get(page_size, f"Custom ({page_size[0]:.0f}x{page_size[1]:.0f} points)")
    
    print("🛠️  Current Configuration:")
    print(f"   📦 Generation name: {generation_name}")
    print(f"   🆔 Card IDs: {', '.join(card_ids)}")
    print(f"   📐 Orientation: {orientation_display} ({orientation})")
    print(f"   📄 Page size: {page_size_name}")
    print(f"   🎨 CMYK conversion: {'ON' if cmyk_conversion else 'OFF'}")
    print(f"   🖼️  Quality: {card_quality}")
    print(f"   💾 Output directory: {OUTPUT_BASE_DIR}")
    print(f"   📚 Expected pages: {len(card_ids) * 2} (front + back for each card)")
    print()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate PDF with front and back pages for cards in CMYK color space",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_pdf.py --generation-name "my_pdf" --ids "000000001 FE F,000000002 FE F"
  python generate_pdf.py --interactive
  python generate_pdf.py  # Uses configuration from script
        """
    )
    
    parser.add_argument(
        "--generation-name", "-g",
        type=str,
        help="Name for the PDF file"
    )
    
    parser.add_argument(
        "--ids", "-i",
        type=str,
        help="Comma-separated list of card IDs (e.g., '000000001 FE F,000000002 FE F')"
    )
    
    parser.add_argument(
        "--orientation", "-o",
        type=str,
        choices=["v", "h"],
        help="Card orientation: 'v' for vertical, 'h' for horizontal"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    
    return parser.parse_args()

def main():
    """Main entry point."""
    
    print("📄 PDF POSTCARD GENERATOR")
    print("="*50)
    print(f"🌐 API URL: {API_BASE_URL}")
    print()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Determine parameters source
    if args.interactive:
        generation_name, card_ids, orientation, page_size, cmyk_conversion, card_quality = interactive_mode()
        if not generation_name:
            sys.exit(1)
    elif args.generation_name or args.ids or args.orientation:
        # Use command line arguments
        generation_name = args.generation_name or GENERATION_NAME
        card_ids = args.ids.split(",") if args.ids else CARD_IDS
        orientation = args.orientation or ORIENTATION
        page_size = PAGE_SIZE
        cmyk_conversion = CMYK_CONVERSION
        card_quality = CARD_QUALITY
        
        # Clean card IDs
        card_ids = [card_id.strip() for card_id in card_ids if card_id.strip()]
    else:
        # Use configuration from script
        generation_name = GENERATION_NAME
        card_ids = CARD_IDS
        orientation = ORIENTATION
        page_size = PAGE_SIZE
        cmyk_conversion = CMYK_CONVERSION
        card_quality = CARD_QUALITY
        print("🔧 Using configuration from script")
    
    # Show current configuration
    print_configuration(generation_name, card_ids, orientation, page_size, cmyk_conversion, card_quality)
    
    # Validate inputs
    if not generation_name or not generation_name.strip():
        print("❌ Error: Generation name cannot be empty")
        if not args.interactive:
            print("   Use --generation-name or --interactive mode")
        sys.exit(1)
    
    if not card_ids:
        print("❌ Error: No card IDs provided")
        if not args.interactive:
            print("   Use --ids or --interactive mode")
        sys.exit(1)
    
    if orientation not in ["h", "v"]:
        print(f"❌ Error: Invalid orientation '{orientation}'. Must be 'h' or 'v'")
        sys.exit(1)
    
    # Check API status
    if not check_api_status():
        print("\n❌ Cannot proceed without server. Please start both servers:")
        print("   1. Next.js: pnpm dev")
        print("   2. Python API: uvicorn api.index:app --reload")
        sys.exit(1)
    
    print("\n" + "="*50)
    
    # Generate PDF
    success = generate_pdf_from_cards(
        generation_name=generation_name,
        card_ids=card_ids,
        orientation=orientation,
        page_size=page_size,
        cmyk_conversion=cmyk_conversion,
        card_quality=card_quality
    )
    
    print("\n" + "="*50)
    
    if success:
        print("🎉 PDF generated successfully!")
        print()
        print("📋 Next steps:")
        print("   1. Open the generated PDF to review")
        print("   2. Send to print service with CMYK color profile")
        print("   3. Use professional paper (300gsm+ recommended)")
        print("   4. Specify CMYK printing when ordering")
        print()
        print("💡 Usage examples:")
        print("   python generate_pdf.py --generation-name 'my_pdf' --ids '000000001 FE F,000000002 FE F'")
        print("   python generate_pdf.py --interactive")
    else:
        print("❌ PDF generation failed!")
        print("   Check the configuration and API status, then try again")
        sys.exit(1)

if __name__ == "__main__":
    main() 