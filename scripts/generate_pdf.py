"""
PDF Postcard Generator with Professional ICC Profile Support

Generate professional PDF with front and back pages for cards in CMYK color space.
Uses img2pdf for proper ICC profile preservation and pikepdf for enhanced metadata.
Each PDF page is sized exactly to match the TIFF card dimensions (no A4 backgrounds).

Features:
- Professional CMYK conversion using FOGRA52 color profile
- Full ICC profile preservation in PDF 
- Proper color management for commercial printing
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

# API Configuration  
API_BASE_URL = "http://localhost:3000/api"

# Generation Configuration
GENERATION_NAME = "sfkuba_test101"
CARD_IDS = [
    "000000704 FE F",
    "000000705 FE F", 
    "000000706 FE F"
]

# PDF Settings
ORIENTATION = "v"  # "v" for vertical, "h" for horizontal cards
OUTPUT_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "pdf_generations")
CMYK_CONVERSION = True  # Convert to CMYK color space for professional printing
CARD_QUALITY = "TIFF"  # "TIFF" for print quality, "PNG" for web quality
SAVE_DEBUG_TIFFS = True # Set to True to save CMYK TIFFs for debugging

# =============================================================================
# CONFIGURATION EXAMPLES:
#
# Horizontal orientation:
# ORIENTATION = "h"
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

def convert_image_to_cmyk(image_bytes: bytes, debug_save_path: str = None) -> bytes:
    """
    Convert image from RGB to CMYK color space using PSO Uncoated v3 FOGRA52 profile.
    This provides professional-grade color conversion for commercial printing.
    
    Args:
        image_bytes: Image data in bytes
        debug_save_path: Optional path to save the converted TIFF for inspection
        
    Returns:
        CMYK image data in bytes with embedded FOGRA52 profile
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
        
        # Path to FOGRA52 profile (in scripts directory)
        fogra52_path = os.path.join(os.path.dirname(__file__), "PSOuncoated_v3_FOGRA52.icc")
        
        # Check if FOGRA52 profile exists
        if not os.path.exists(fogra52_path):
            print(f"         ⚠️  FOGRA52 profile not found at: {fogra52_path}")
            print(f"         🔄 Using basic PIL CMYK conversion")
            cmyk_img = img.convert('CMYK')
            cmyk_profile = None
        else:
            print(f"         🎨 Converting RGB → CMYK using FOGRA52 profile")
            
            try:
                # Create sRGB input profile
                src_profile = ImageCms.createProfile('sRGB')
                
                # Load FOGRA52 CMYK output profile
                dst_profile = ImageCms.getOpenProfile(fogra52_path)
                
                # Create color transformation with perceptual rendering intent
                transform = ImageCms.buildTransform(
                    src_profile, dst_profile, 'RGB', 'CMYK',
                    renderingIntent=0  # Perceptual rendering for better color accuracy
                )
                
                # Apply transformation
                cmyk_img = ImageCms.applyTransform(img, transform)
                
                # Get FOGRA52 profile for embedding
                with open(fogra52_path, 'rb') as f:
                    cmyk_profile = f.read()
                
                print(f"         📋 Using ICC profile: PSO Uncoated v3 (FOGRA52)")
                
            except Exception as profile_error:
                print(f"         ❌ FOGRA52 conversion failed: {profile_error}")
                print(f"         🔄 Using basic PIL CMYK conversion")
                cmyk_img = img.convert('CMYK')
                cmyk_profile = None
        
        # Save as TIFF with proper settings and ICC profile
        output = io.BytesIO()
        save_kwargs = {
            'format': 'TIFF',
            'compression': 'lzw',
            'dpi': (300, 300)  # Ensure 300 DPI is preserved
        }
        
        # Embed FOGRA52 profile if available
        if cmyk_profile:
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
        profile_info = "with FOGRA52 profile" if cmyk_profile else "without ICC profile"
        print(f"         ✅ CMYK conversion successful: {len(converted_bytes)/1024:.1f}KB {profile_info}")
        return converted_bytes
        
    except Exception as e:
        print(f"      ❌ CMYK conversion failed: {str(e)}")
        print(f"      📋 Using original RGB for compatibility")
        return image_bytes

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
                "/OutputConditionIdentifier": "FOGRA52",
                "/Info": "PSO Uncoated v3 FOGRA52",
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
                if cmyk_conversion:
                    debug_path = os.path.join(OUTPUT_BASE_DIR, "debug_tiffs", f"{extended_id.replace(' ', '_')}_front_FOGRA52.tiff") if SAVE_DEBUG_TIFFS else None
                    front_bytes = convert_image_to_cmyk(front_bytes, debug_path)
                
                # Add front image data to list
                image_data_list.append(front_bytes)
                total_pages += 1
                
                # Get image info for logging
                front_img = Image.open(io.BytesIO(front_bytes))
                print(f"      ✅ Front: {front_img.size[0]}×{front_img.size[1]}px, ICC: {'Yes' if 'icc_profile' in front_img.info else 'No'}")
                
            # Process back image
            if back_bytes:
                if cmyk_conversion:
                    debug_path = os.path.join(OUTPUT_BASE_DIR, "debug_tiffs", f"{extended_id.replace(' ', '_')}_back_FOGRA52.tiff") if SAVE_DEBUG_TIFFS else None
                    back_bytes = convert_image_to_cmyk(back_bytes, debug_path)
                
                # Add back image data to list
                image_data_list.append(back_bytes)
                total_pages += 1
                
                # Get image info for logging
                back_img = Image.open(io.BytesIO(back_bytes))
                print(f"      ✅ Back: {back_img.size[0]}×{back_img.size[1]}px, ICC: {'Yes' if 'icc_profile' in back_img.info else 'No'}")
        
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
        
        # OutputIntent disabled for Adobe Reader compatibility
        # The CMYK images with embedded ICC profiles are sufficient for professional printing
        # if cmyk_conversion:
        #     fogra52_path = os.path.join(os.path.dirname(__file__), "PSOuncoated_v3_FOGRA52.icc")
        #     if os.path.exists(fogra52_path):
        #         add_pdf_output_intent(output_path, fogra52_path)
        
        # Add metadata using pikepdf
        try:
            with pikepdf.open(output_path, allow_overwriting_input=True) as pdf:
                pdf.docinfo.Title = "shadefreude" 
                pdf.docinfo.Subject = "CMYK Cards with PSO Uncoated v3 (FOGRA52) Color Profile"
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
    orientation_map = {"v": "vertical", "h": "horizontal"}
    full_orientation = orientation_map.get(orientation, orientation)
    
    print(f"📄 Generating PDF: {generation_name}")
    print(f"   🆔 Cards: {len(card_ids)} cards")
    print(f"   📐 Orientation: {full_orientation}")
    print(f"   📄 Page sizing: Each page sized to match TIFF dimensions")
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
    orientation_display = {"v": "vertical", "h": "horizontal"}.get(orientation, orientation)
    
    print("🛠️  Current Configuration:")
    print(f"   📦 Generation name: {generation_name}")
    print(f"   🆔 Card IDs: {', '.join(card_ids)}")
    print(f"   📐 Orientation: {orientation_display} ({orientation})")
    print(f"   📄 Page sizing: Each page sized to match TIFF dimensions")
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
        print("   2. Send to print service with CMYK color profile")
        print("   3. Use professional paper (300gsm+ recommended)")
        print("   4. Specify CMYK printing when ordering")
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