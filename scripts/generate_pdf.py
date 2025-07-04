"""
PDF Postcard Generator with Professional ICC Profile Support

Generate professional PDF with front and back pages for cards in CMYK color space.
Uses img2pdf for proper ICC profile preservation and pikepdf for enhanced metadata.
Each PDF page is sized exactly to match the TIFF card dimensions (no A4 backgrounds).

Features:
- Two professional workflows: "NO_PROFILE" (HP Indigo) and "FOGRA39_CMYK" (Standard)
- NO_PROFILE: RGB output for professional RIP conversion (HP Indigo compatible)
- FOGRA39_CMYK: Professional CMYK conversion using ISO Coated v2 profile
- Full ICC profile control (embed or omit based on printer requirements)
- Compatible with HP Indigo, DrukExpress.pl, and most European print services
- Direct TIFF→PDF conversion without quality loss

Instructions:
1. Edit the configuration variables below
2. Run: uv run python scripts/generate_pdf.py
3. Generated PDF will have pages sized exactly to card dimensions for professional printing

Usage Options:
1. Edit configuration variables below and run: uv run python scripts/generate_pdf.py
2. Use command line: uv run python scripts/generate_pdf.py --generation-name "my_pdf" --ids "000000001 FE F,000000002 FE F" --orientation h
3. Interactive mode: uv run python scripts/generate_pdf.py --interactive
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

# PDF generation with ICC profile support
try:
    import img2pdf
    import pikepdf
    IMG2PDF_AVAILABLE = True
except ImportError:
    print("⚠️  img2pdf not installed. Install with: uv add img2pdf")
    IMG2PDF_AVAILABLE = False

# =============================================================================
# CONFIGURATION - EDIT THESE VARIABLES (used when no CLI args provided)
# =============================================================================

# =============================================================================
# PRINTING WORKFLOW CONFIGURATION  
# =============================================================================

# Choose your printing workflow:
# RGB: Send RGB files, let printer handle conversion
# - Keeps images in RGB color space
# - No ICC profiles embedded  
# - Printer's RIP handles CMYK conversion with their profile
# - Recommended for: HP Indigo, professional printers with custom RIP

# CMYK_BASIC: Basic CMYK conversion (like graphics software)
# - Converts using basic PIL algorithm (img.convert('CMYK'))
# - No ICC profiles used or embedded
# - Mimics "Export as CMYK without profile" from Photoshop/Illustrator
# - Recommended for: Printers requesting "CMYK without profiles"

# CMYK_FOGRA39_EMBED: Professional CMYK with embedded profile
# - Converts using FOGRA39 ICC profile for accurate colors
# - Profile embedded for guaranteed color accuracy  
# - Full color management control
# - Recommended for: Standard offset printing, DrukExpress.pl
# =============================================================================

# WORKFLOW = "RGB"
WORKFLOW = "CMYK_BASIC"
# WORKFLOW = "CMYK_FOGRA39_EMBED"
CARD_IDS = [
    # top3
    "000000750 FE F",
    "000000753 FE F",
    "000000761 FE F",
    # de01 one more time (6)
    # "000000713 FE F", # Aga
    # "000000719 FE F", # Dolomity lilac
    # "000000770 FE F", # Magda Ż. czarne tło
    # "000000771 FE F", # mloda polska (było ok)
    # "000000776 FE F", # czerwony szwajcaria
    # "000000764 FE F", # ja na slowhopie (sprawdzenei jasnej i twarz)
    # print de01
    # "000000751 FE F", # najlepsza; po wykładzie Igora
    # "000000719 FE F",
    # "000000722 FE F",
    # "000000723 FE F",
    # "000000741 FE F",
    # "000000752 FE F",
    # "000000759 FE F",
    # "000000762 FE F",
    # "000000769 FE F",
    # "000000773 FE F",
]

# API Configuration
API_BASE_URL = "http://localhost:3000/api"

# Generation Configuration
GENERATION_NAME = "sf-kuba-de03-profiletest-cmyknoprofile"

# PDF Settings  
ORIENTATION = "v"  # "v" for vertical, "h" for horizontal cards
OUTPUT_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "pdf_generations")

# Auto-configure based on workflow choice
if WORKFLOW == "RGB":
    CMYK_CONVERSION = False
    WORKFLOW_NAME = "RGB"
elif WORKFLOW == "CMYK_BASIC":
    CMYK_CONVERSION = True
    WORKFLOW_NAME = "CMYK_BASIC"
elif WORKFLOW == "CMYK_FOGRA39_EMBED":
    CMYK_CONVERSION = True
    WORKFLOW_NAME = "CMYK_FOGRA39_EMBED"
else:
    raise ValueError(f"Invalid WORKFLOW: {WORKFLOW}")

CARD_QUALITY = "TIFF"  # "TIFF" for print quality, "PNG" for web quality
SAVE_DEBUG_TIFFS = True # Set to True to save debug TIFFs

# =============================================================================
# CONFIGURATION EXAMPLES:
#
# Horizontal orientation:
# ORIENTATION = "h"
#
# Web quality (faster generation):
# CARD_QUALITY = "PNG"
#
# Different cards:
# CARD_IDS = ["000000001 FE F", "000000002 FE F"]
#
# Custom generation name:
# GENERATION_NAME = "my_custom_pdf"  # Generates: my_custom_pdf.pdf
#
# Different printing workflows:
# WORKFLOW = "RGB"                    # RGB for HP Indigo
# WORKFLOW = "CMYK_BASIC"             # Basic CMYK for graphics software compatibility  
# WORKFLOW = "CMYK_FOGRA39_EMBED"     # Professional CMYK with embedded ICC profiles
#
# =============================================================================

# =============================================================================
# CONSTANTS AND HELPER FUNCTIONS
# =============================================================================

# Orientation mapping used throughout the script
ORIENTATION_MAP = {"v": "vertical", "h": "horizontal"}

def get_orientation_display(orientation: str) -> str:
    """Convert orientation shorthand to full name."""
    return ORIENTATION_MAP.get(orientation, orientation)

def download_image_safely(url: str, description: str = "image") -> Optional[bytes]:
    """
    Download image with proper error handling.
    
    Args:
        url: Image URL to download
        description: Description for error messages
        
    Returns:
        Image bytes or None if failed
    """
    if not url:
        return None
        
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"      ❌ Failed to download {description}: {str(e)}")
        return None

def determine_tiff_urls(card_data: Dict[str, Any], orientation: str) -> tuple:
    """
    Determine front and back TIFF URLs based on orientation.
    
    Args:
        card_data: Card information from API
        orientation: "v" for vertical, "h" for horizontal
        
    Returns:
        Tuple of (front_tiff_url, back_tiff_url)
    """
    full_orientation = get_orientation_display(orientation)
    
    if full_orientation == "vertical":
        return card_data.get("vTiff"), card_data.get("bvTiff")
    else:  # horizontal
        return card_data.get("hTiff"), card_data.get("bhTiff")

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
    
    if not IMG2PDF_AVAILABLE:
        print("❌ img2pdf is required for PDF generation")
        print("   Install with: uv add img2pdf")
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
        # Get TIFF URLs based on orientation
        front_tiff_url, back_tiff_url = determine_tiff_urls(card_data, orientation)
        
        # Download images using helper function
        front_image_bytes = download_image_safely(front_tiff_url, "front card image")
        back_image_bytes = download_image_safely(back_tiff_url, "back card image")
        
        return front_image_bytes, back_image_bytes
        
    except Exception as e:
        print(f"      ❌ Failed to generate card images: {str(e)}")
        return None, None

def convert_image_to_cmyk(image_bytes: bytes, debug_save_path: str = None) -> bytes:
    """
    Convert image from RGB to CMYK color space based on current workflow.
    
    Args:
        image_bytes: Image data in bytes
        debug_save_path: Optional path to save the converted TIFF for inspection
        
    Returns:
        CMYK image data in bytes
    """
    try:
        # Load image
        img = Image.open(io.BytesIO(image_bytes))
        print(f"         📊 Original image: {img.mode} mode, {img.size}px")
        
        # Skip conversion if already CMYK
        if img.mode == 'CMYK':
            print(f"         ✅ Already CMYK, keeping original")
            return image_bytes
        
        # Convert to RGB first if needed (handles RGBA, L, etc.)
        if img.mode != 'RGB':
            print(f"         🔄 Converting {img.mode} → RGB")
            if img.mode == 'RGBA':
                # Create white background for RGBA images
                rgb_img = Image.new('RGB', img.size, 'white')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            else:
                img = img.convert('RGB')
        
        # Choose conversion based on workflow
        if WORKFLOW == "CMYK_BASIC":
            # Basic PIL conversion - what graphics software does
            print(f"         🎨 Basic PIL CMYK conversion (graphics software style)")
            cmyk_img = img.convert('CMYK')
            cmyk_profile = None
            profile_info = "basic PIL conversion"
            
        elif WORKFLOW == "CMYK_FOGRA39_EMBED":
            # Professional ICC conversion using FOGRA39
            print(f"         🎨 Professional ICC conversion using FOGRA39 profile")
            cmyk_img, cmyk_profile = convert_with_icc_profile(img)
            profile_info = "with embedded FOGRA39 profile" if cmyk_profile else "FOGRA39 conversion (profile missing)"
            
        else:
            # This shouldn't happen with our workflow validation
            raise ValueError(f"CMYK conversion called for non-CMYK workflow: {WORKFLOW}")
        
        # Save as TIFF with proper settings
        output = io.BytesIO()
        save_kwargs = {
            'format': 'TIFF',
            'compression': 'lzw',
            'dpi': (300, 300)  # Ensure 300 DPI is preserved
        }
        
        # Embed ICC profile for FOGRA39_EMBED workflow
        if cmyk_profile and WORKFLOW == "CMYK_FOGRA39_EMBED":
            save_kwargs['icc_profile'] = cmyk_profile
        
        cmyk_img.save(output, **save_kwargs)
        
        # DEBUG: Save interim TIFF file if path provided
        if debug_save_path:
            try:
                os.makedirs(os.path.dirname(debug_save_path), exist_ok=True)
                cmyk_img.save(debug_save_path, **save_kwargs)
                print(f"         💾 Debug TIFF saved: {debug_save_path}")
                
                # Verify the saved file has ICC profile
                test_img = Image.open(debug_save_path)
                has_profile = 'icc_profile' in test_img.info
                profile_size = len(test_img.info.get('icc_profile', b'')) if has_profile else 0
                print(f"         🔍 Verification: ICC profile embedded = {has_profile}, size = {profile_size} bytes")
                
            except Exception as debug_error:
                print(f"         ⚠️  Debug save failed: {debug_error}")
        
        converted_bytes = output.getvalue()
        print(f"         ✅ CMYK conversion successful: {len(converted_bytes)/1024:.1f}KB {profile_info}")
        return converted_bytes
        
    except Exception as e:
        print(f"      ❌ CMYK conversion failed: {str(e)}")
        print(f"      📋 Using original RGB for compatibility")
        return image_bytes

def convert_with_icc_profile(img: Image.Image) -> tuple:
    """
    Convert RGB image to CMYK using professional ICC profile (FOGRA39).
    
    Args:
        img: PIL Image in RGB mode
        
    Returns:
        Tuple of (cmyk_image, cmyk_profile_bytes)
    """
    # Path to FOGRA39 profile (in scripts directory)
    fogra39_path = os.path.join(os.path.dirname(__file__), "ISOcoated_v2_eci.icc")
    
    # Check if FOGRA39 profile exists
    if not os.path.exists(fogra39_path):
        print(f"         ⚠️  FOGRA39 profile not found at: {fogra39_path}")
        print(f"         💡 Download from: http://www.eci.org/doku.php?id=en:downloads")
        print(f"         📦 Extract ISOcoated_v2_eci.icc from eci_offset_2009.zip")
        print(f"         🔄 Using basic PIL CMYK conversion instead")
        cmyk_img = img.convert('CMYK')
        return cmyk_img, None
    
    try:
        # Create sRGB input profile
        src_profile = ImageCms.createProfile('sRGB')
        
        # Load FOGRA39 CMYK output profile
        dst_profile = ImageCms.getOpenProfile(fogra39_path)
        
        # Create color transformation with perceptual rendering intent
        transform = ImageCms.buildTransform(
            src_profile, dst_profile, 'RGB', 'CMYK',
            renderingIntent=0  # Perceptual rendering for better color accuracy
        )
        
        # Apply transformation
        cmyk_img = ImageCms.applyTransform(img, transform)
        
        # Get FOGRA39 profile for embedding
        with open(fogra39_path, 'rb') as f:
            cmyk_profile = f.read()
        
        return cmyk_img, cmyk_profile
        
    except Exception as profile_error:
        print(f"         ❌ FOGRA39 conversion failed: {profile_error}")
        print(f"         🔄 Using basic PIL CMYK conversion instead")
        cmyk_img = img.convert('CMYK')
        return cmyk_img, None

def add_pdf_output_intent(pdf_path: str, icc_path: str) -> bool:
    """
    Add professional OutputIntent to PDF for proper color management.
    Simplified Adobe Reader compatible implementation.
    
    Args:
        pdf_path: Path to the PDF file
        icc_path: Path to the ICC profile
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
            # Read ICC profile data
            with open(icc_path, "rb") as icc_file:
                icc_data = icc_file.read()
            
            # Create uncompressed ICC profile stream (more compatible)
            icc_stream = pikepdf.Stream(pdf, icc_data)
            icc_stream["/N"] = 4  # CMYK = 4 components
            
            # Simple OutputIntent dictionary - minimal but compatible
            output_intent = pikepdf.Dictionary({
                "/Type": pikepdf.Name("/OutputIntent"),
                "/S": pikepdf.Name("/GTS_PDFX"), 
                "/OutputConditionIdentifier": "FOGRA39",
                "/Info": "ISO Coated v2 FOGRA39",
                "/DestOutputProfile": icc_stream
            })
            
            # Add OutputIntent to PDF root
            pdf.Root["/OutputIntents"] = pikepdf.Array([output_intent])
            
            pdf.save()
        
        print(f"   📋 Added simplified OutputIntent (Adobe Reader compatible)")
        return True
        
    except Exception as e:
        print(f"   ⚠️  Could not add OutputIntent: {e}")
        print(f"   📋 PDF still valid for printing without OutputIntent")
        return False

def process_card_side(image_bytes: bytes, extended_id: str, side: str) -> bytes:
    """
    Process a single card side (front or back) for PDF generation.
    
    Args:
        image_bytes: Raw image data
        extended_id: Card ID for debug naming
        side: "front" or "back" for debug naming
        
    Returns:
        Processed image bytes
    """
    if CMYK_CONVERSION:
        # Generate debug path based on workflow
        workflow_suffix = {
            "CMYK_BASIC": "BasicCMYK",
            "CMYK_FOGRA39_EMBED": "FOGRA39_Embed"
        }.get(WORKFLOW, "Unknown")
        
        debug_path = os.path.join(OUTPUT_BASE_DIR, "debug_tiffs", 
                                f"{extended_id.replace(' ', '_')}_{side}_{workflow_suffix}.tiff") if SAVE_DEBUG_TIFFS else None
        
        # Convert to CMYK
        image_bytes = convert_image_to_cmyk(image_bytes, debug_path)
    
    # Log image info
    img = Image.open(io.BytesIO(image_bytes))
    print(f"      ✅ {side.title()}: {img.size[0]}×{img.size[1]}px, ICC: {'Yes' if 'icc_profile' in img.info else 'No'}")
    
    return image_bytes

def create_pdf(card_images: List[tuple], output_path: str, 
               cmyk_conversion: bool = True) -> bool:
    """
    Create PDF using img2pdf library which preserves ICC profiles properly.
    Each TIFF image becomes a PDF page sized exactly to the image dimensions.
    
    Args:
        card_images: List of (extended_id, front_bytes, back_bytes) tuples
        output_path: Path to save the PDF
        cmyk_conversion: Whether to convert images to CMYK
        
    Returns:
        True if successful, False otherwise
    """
    if not IMG2PDF_AVAILABLE:
        print("   ❌ img2pdf not available")
        return False
    
    try:
        print(f"   📄 Creating PDF with ICC profile preservation")
        
        # Collect all image data for PDF creation
        image_data_list = []
        total_pages = 0
        
        for extended_id, front_bytes, back_bytes in card_images:
            print(f"   🎨 Processing card {extended_id}...")
            
            # Process front image
            if front_bytes:
                front_bytes = process_card_side(front_bytes, extended_id, "front")
                image_data_list.append(front_bytes)
                total_pages += 1
                
            # Process back image  
            if back_bytes:
                back_bytes = process_card_side(back_bytes, extended_id, "back")
                image_data_list.append(back_bytes)
                total_pages += 1
        
        if not image_data_list:
            print(f"   ❌ No images to process")
            return False
        
        # Create PDF with preserved ICC profiles
        print(f"   📋 Converting {len(image_data_list)} images to PDF with ICC profile preservation...")
        
        # Configuration for maximum quality
        layout_config = img2pdf.get_layout_fun(
            pagesize=None,  # Use image dimensions as page size
            imgsize=None,   # Use original image size
            border=None,    # No borders
            fit=None,       # No scaling
            auto_orient=False  # Keep original orientation
        )
        
        # Create PDF with preserved ICC profiles
        pdf_bytes = img2pdf.convert(
            image_data_list,
            layout_fun=layout_config,
            with_pdfrw=False  # Use internal PDF writer for better ICC support
        )
        
        # Save PDF
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"   ✅ PDF created with {total_pages} pages and preserved ICC profiles")
        
        # Add metadata using pikepdf
        try:
            with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
                pdf.docinfo.Title = "shadefreude" 
                if WORKFLOW == "RGB":
                    pdf.docinfo.Subject = "RGB Cards for Professional RIP Conversion (HP Indigo Compatible)"
                elif WORKFLOW == "CMYK_BASIC":
                    pdf.docinfo.Subject = "CMYK Cards with Basic PIL Conversion (Graphics Software Compatible)"
                elif WORKFLOW == "CMYK_FOGRA39_EMBED":
                    pdf.docinfo.Subject = "CMYK Cards with ISO Coated v2 (FOGRA39) Color Profile"
                pdf.docinfo.Creator = "tinker.institute"
                pdf.save()
            print(f"   📋 Added professional metadata to PDF")
        except Exception as meta_error:
            print(f"   ⚠️  Could not add metadata: {meta_error}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ img2pdf PDF generation failed: {str(e)}")
        return False

def generate_pdf_from_cards(
    generation_name: str,
    card_ids: List[str], 
    orientation: str = "v",
    cmyk_conversion: bool = True,
    card_quality: str = "TIFF"
) -> bool:
    """
    Generate PDF with front and back pages for cards.
    Each PDF page is sized exactly to match the TIFF card dimensions.
    
    Args:
        generation_name: Name for the PDF file
        card_ids: List of extended card IDs
        orientation: "v" for vertical, "h" for horizontal
        cmyk_conversion: Convert to CMYK color space
        card_quality: "TIFF" or "PNG"
        
    Returns:
        True if successful, False otherwise
    """
    
    # Convert orientation shorthand
    full_orientation = get_orientation_display(orientation)
    
    print(f"📄 Generating PDF: {generation_name}")
    print(f"   🆔 Cards: {len(card_ids)} cards")
    print(f"   📐 Orientation: {full_orientation}")
    print(f"   📄 Page sizing: Each page sized to match TIFF dimensions")
    print(f"   🖨️  Workflow: {WORKFLOW} - {WORKFLOW_NAME}")
    print(f"   🎨 CMYK conversion: {'ON' if cmyk_conversion else 'OFF'}")
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
    success = create_pdf(card_images, pdf_path, cmyk_conversion)
    
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
        return None, None, None, None, None
    
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
        return None, None, None, None, None
    
    # Get orientation
    orientation = input("📐 Enter orientation (v for vertical, h for horizontal) [v]: ").strip()
    if not orientation:
        orientation = "v"
    
    if orientation not in ["v", "h"]:
        print(f"❌ Invalid orientation '{orientation}'. Must be 'v' or 'h'")
        return None, None, None, None, None
    
    # Get CMYK conversion
    cmyk_choice = input("🎨 Convert to CMYK color space for professional printing? (y/n) [y]: ").strip().lower()
    cmyk_conversion = cmyk_choice != "n"
    
    # Get quality
    quality_choice = input("🖼️  Image quality (tiff for print, png for web) [tiff]: ").strip().lower()
    if quality_choice in ["png", "web"]:
        card_quality = "PNG"
    else:
        card_quality = "TIFF"
    
    return generation_name, card_ids, orientation, cmyk_conversion, card_quality

def print_configuration(generation_name: str, card_ids: List[str], orientation: str, 
                       cmyk_conversion: bool, card_quality: str):
    """Print current configuration settings."""
    orientation_display = get_orientation_display(orientation)
    
    print("🛠️  Current Configuration:")
    print(f"   📦 Generation name: {generation_name}")
    print(f"   🆔 Card IDs: {', '.join(card_ids)}")
    print(f"   📐 Orientation: {orientation_display} ({orientation})")
    print(f"   📄 Page sizing: Each page sized to match TIFF dimensions")
    print(f"   🖨️  Workflow: {WORKFLOW} - {WORKFLOW_NAME}")
    print(f"   🎨 CMYK conversion: {'ON' if cmyk_conversion else 'OFF'}")
    print(f"   🖼️  Quality: {card_quality}")
    print(f"   💾 Debug TIFFs: {'ON' if SAVE_DEBUG_TIFFS else 'OFF'}")
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
  uv run python scripts/generate_pdf.py --generation-name "my_pdf" --ids "000000001 FE F,000000002 FE F"
  uv run python scripts/generate_pdf.py --interactive
  uv run python scripts/generate_pdf.py  # Uses configuration from script
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
        generation_name, card_ids, orientation, cmyk_conversion, card_quality = interactive_mode()
        if not generation_name:
            sys.exit(1)
    elif args.generation_name or args.ids or args.orientation:
        # Use command line arguments
        generation_name = args.generation_name or GENERATION_NAME
        card_ids = args.ids.split(",") if args.ids else CARD_IDS
        orientation = args.orientation or ORIENTATION
        cmyk_conversion = CMYK_CONVERSION
        card_quality = CARD_QUALITY
        
        # Clean card IDs
        card_ids = [card_id.strip() for card_id in card_ids if card_id.strip()]
    else:
        # Use configuration from script
        generation_name = GENERATION_NAME
        card_ids = CARD_IDS
        orientation = ORIENTATION
        cmyk_conversion = CMYK_CONVERSION
        card_quality = CARD_QUALITY
        print("🔧 Using configuration from script")
    
    # Show current configuration
    print_configuration(generation_name, card_ids, orientation, cmyk_conversion, card_quality)
    
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
        cmyk_conversion=cmyk_conversion,
        card_quality=card_quality
    )
    
    print("\n" + "="*50)
    
    if success:
        print("🎉 PDF generated successfully!")
        print()
        print("📋 Next steps:")
        print("   1. Open the generated PDF to review")
        if WORKFLOW == "RGB":
            print("   2. Send RGB PDF to HP Indigo / professional printer")
            print("   3. Let printer's RIP handle CMYK conversion")
            print("   4. Specify: 'Use your calibrated color profile'")
            print("   5. Professional paper (300gsm+ recommended)")
            print()
            print("✅ Perfect for HP Indigo printers with custom RIP profiles!")
        elif WORKFLOW == "CMYK_BASIC":
            print("   2. Send CMYK PDF without embedded profiles")
            print("   3. Basic PIL conversion mimics graphics software export")
            print("   4. Printer will apply their own profile/calibration")
            print("   5. Professional paper (300gsm+ recommended)")
            print()
            print("✅ Perfect for HP Indigo with CMYK delivery requirement!")
        elif WORKFLOW == "CMYK_FOGRA39_EMBED":
            print("   2. Send CMYK PDF with ISO Coated v2 (FOGRA39) Color Profile")
            print("   3. Use with DrukExpress.pl or ISO Coated v2 printers")
            print("   4. Specify CMYK printing when ordering")
            print("   5. Professional paper (300gsm+ recommended)")
            print()
            print("✅ Perfect for standard offset printing and DrukExpress.pl!")
        print()
        print("💡 Usage examples:")
        print("   uv run python scripts/generate_pdf.py --generation-name 'my_pdf' --ids '000000001 FE F,000000002 FE F'")
        print("   uv run python scripts/generate_pdf.py --interactive")
    else:
        print("❌ PDF generation failed!")
        print("   Check the configuration and API status, then try again")
        sys.exit(1)

if __name__ == "__main__":
    main() 