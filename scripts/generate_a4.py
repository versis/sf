"""
A4 Postcard Layout Generator
Generate professional A4 layouts for front and back sides with proper duplex alignment.

Instructions:
1. Edit the configuration variables below
2. Run: python generate_a4.py
3. Generated TIFF files will be saved in the current directory
"""

import requests
import time
import sys
from typing import List, Optional

# =============================================================================
# CONFIGURATION - EDIT THESE VARIABLES
# =============================================================================

# API Configuration
API_BASE_URL = "http://localhost:8000/api"

# Card Configuration
CARD_IDS = [
    "000000632 FE F",
    "000000633 FE F", 
    "000000634 FE F"
]  # Maximum 3 cards per A4 sheet

# Layout Settings
PASSEPARTOUT_MM = 8                    # White border in millimeters (0, 8, 12, etc.)
CONTENT_WIDTH_MM = 146                 # Content width in mm (default 146 = 14.6cm)
ORIENTATION = "v"                     # "h" for horizontal, "v" for vertical
DUPLEX_MODE = True                     # True = back side positioned on right for proper duplex alignment
OUTPUT_PREFIX = "wydruktestowy_sf"                   # Filename prefix (generates: sf_w156_pp12_cardids_front.tiff)

# =============================================================================
# COMMON CONFIGURATION EXAMPLES:
#
# No white border:
# PASSEPARTOUT_MM = 0
#
# Vertical orientation with larger border:
# ORIENTATION = "v"
# PASSEPARTOUT_MM = 12
#
# Single-sided printing (no duplex):
# DUPLEX_MODE = False
#
# Different cards:
# CARD_IDS = ["000001 FE F", "000002 FF A"]
#
# Professional print settings (thick border):
# PASSEPARTOUT_MM = 12
# CONTENT_WIDTH_MM = 140  # Slightly smaller content for cutting room
#
# Custom output prefix:
# OUTPUT_PREFIX = "myprint"  # Generates: myprint_w140_pp12_cardids_front.tiff
# =============================================================================

def generate_a4_layout(
    card_ids: List[str],
    passepartout_mm: float = 0,
    target_content_width_mm: float = 146,
    orientation: str = "horizontal",
    duplex_mode: bool = True,
    output_prefix: str = "wydruktestowy"
) -> bool:
    """
    Generate A4 layouts for front and back sides.
    
    Args:
        card_ids: List of card extended IDs (max 3)
        passepartout_mm: White border in millimeters (0, 8, 12, etc.)
        target_content_width_mm: Content width in millimeters (default 146 = 14.6cm)
        orientation: "h" for horizontal, "v" for vertical card orientation
        duplex_mode: If True, adjusts back layout for proper duplex printing
        output_prefix: Prefix for output filenames
        
    Returns:
        True if successful, False otherwise
    """
    
    if len(card_ids) > 3:
        print(f"❌ Error: Maximum 3 cards allowed, got {len(card_ids)}")
        return False
    
    # Convert short orientation to full form for API
    orientation_map = {"h": "horizontal", "v": "vertical"}
    api_orientation = orientation_map.get(orientation, orientation)
    orientation_display = api_orientation
    
    print(f"🖨️  Generating A4 Layout")
    print(f"   📋 Cards: {len(card_ids)} cards")
    print(f"   🆔 IDs: {', '.join(card_ids)}")
    print(f"   📐 Orientation: {orientation_display}")
    print(f"   🔲 Passepartout: {passepartout_mm}mm")
    print(f"   📄 Content size: {target_content_width_mm}×{target_content_width_mm/2}mm")
    print(f"   🔄 Duplex mode: {'ON' if duplex_mode else 'OFF'}")
    print()
    
    # Prepare request data
    request_data = {
        "extended_ids": card_ids,
        "passepartout_mm": passepartout_mm,
        "target_content_width_mm": target_content_width_mm,
        "orientation": api_orientation,  # Send full form to API
        "duplex_mode": duplex_mode,
        "output_prefix": output_prefix
    }
    
    # For duplex printing, the back side is positioned on the right side of A4
    # This ensures proper alignment when the paper is flipped
    if duplex_mode:
        print("🔄 Duplex mode: Back side will be positioned on right for proper alignment")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/create-a4-layouts",
            json=request_data,
            timeout=120
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! ({duration:.1f}s)")
            print(f"   📊 Cards found: {result['cards_found']}/{len(card_ids)}")
            print(f"   📊 Cards processed: {result['cards_processed']}")
            
            # Report generated files
            front_file = result.get('front_layout_file')
            back_file = result.get('back_layout_file')
            
            if front_file:
                front_size = result.get('front_layout_size_mb', 0)
                print(f"   📄 Front: {front_size:.1f}MB → {front_file}")
            
            if back_file:
                back_size = result.get('back_layout_size_mb', 0)
                print(f"   📄 Back: {back_size:.1f}MB → {back_file}")
                
                if duplex_mode:
                    print(f"   💡 Back layout is ready for duplex printing")
                    print(f"      (Positioned on right side for proper alignment)")
            
            print(f"\n💬 {result['message']}")
            return True
            
        else:
            print(f"❌ Error {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   📝 Details: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"   📝 Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def check_api_status() -> bool:
    """Check if the API is running."""
    
    print("🔍 Checking API status...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/../docs", timeout=5)
        if response.status_code == 200:
            print("   ✅ API is running")
            return True
        else:
            print(f"   ⚠️  API responded with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ API not reachable: {str(e)}")
        print(f"   💡 Make sure to start the API with: uvicorn api.index:app --reload")
        return False

def print_configuration():
    """Print current configuration settings."""
    # Convert orientation for display
    orientation_display = {"h": "horizontal", "v": "vertical"}.get(ORIENTATION, ORIENTATION)
    
    print("🛠️  Current Configuration:")
    print(f"   🆔 Card IDs: {', '.join(CARD_IDS)}")
    print(f"   📐 Orientation: {orientation_display} ({ORIENTATION})")
    print(f"   🔲 Passepartout: {PASSEPARTOUT_MM}mm")
    print(f"   📄 Content size: {CONTENT_WIDTH_MM}×{CONTENT_WIDTH_MM/2}mm")
    print(f"   🔄 Duplex mode: {'ON' if DUPLEX_MODE else 'OFF'}")
    print()
    
    if DUPLEX_MODE:
        print("💡 Duplex mode explanation:")
        print("   Front side: [Card1] [Card2] [Card3] positioned on LEFT")
        print("   Back side:  [Card1_back] [Card2_back] [Card3_back] positioned on RIGHT")
        print("   After flipping: Perfect alignment due to horizontal positioning")
        print()

def main():
    """Main entry point."""
    
    print("🖨️  A4 POSTCARD LAYOUT GENERATOR")
    print("="*50)
    print(f"🌐 API URL: {API_BASE_URL}")
    print()
    
    # Show current configuration
    print_configuration()
    
    # Validate card count
    if len(CARD_IDS) > 3:
        print(f"❌ Error: Maximum 3 cards allowed per A4 sheet, got {len(CARD_IDS)}")
        print("   Edit CARD_IDS in the configuration section")
        sys.exit(1)
    
    if len(CARD_IDS) == 0:
        print(f"❌ Error: No card IDs provided")
        print("   Edit CARD_IDS in the configuration section")
        sys.exit(1)
    
    # Validate orientation
    if ORIENTATION not in ["h", "v"]:
        print(f"❌ Error: Invalid orientation '{ORIENTATION}'. Must be 'h' or 'v'")
        sys.exit(1)
    
    # Check API status
    if not check_api_status():
        print("\n❌ Cannot proceed without API. Please start the API server first.")
        print("   Command: uvicorn api.index:app --reload")
        sys.exit(1)
    
    print("\n" + "="*50)
    
    # Generate layouts using configuration variables
    success = generate_a4_layout(
        card_ids=CARD_IDS,
        passepartout_mm=PASSEPARTOUT_MM,
        target_content_width_mm=CONTENT_WIDTH_MM,
        orientation=ORIENTATION,
        duplex_mode=DUPLEX_MODE,
        output_prefix=OUTPUT_PREFIX
    )
    
    print("\n" + "="*50)
    
    if success:
        print("🎉 A4 layouts generated successfully!")
        print()
        print("📋 Next steps:")
        print("   1. Open the generated TIFF files to review")
        print("   2. Send to print service with duplex printing settings")
        print("   3. Use professional paper (300gsm+ recommended)")
        print("   4. Cut along the cutting guides after printing")
        print()
        print("💡 To generate different layouts:")
        print("   1. Edit the configuration variables at the top of this script")
        print("   2. Run: python generate_a4.py")
    else:
        print("❌ Layout generation failed!")
        print("   Check the configuration variables and try again")
        sys.exit(1)

if __name__ == "__main__":
    main() 