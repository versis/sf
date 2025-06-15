"""
Single Card Generation Downloader
Download TIFF cards (front and back) for a list of card IDs.

Usage Options:
1. Edit configuration variables below and run: python download_generation.py
2. Use command line: python download_generation.py --generation-name "my_gen" --ids "000000001 FE F,000000002 FE F" --orientation v
3. Interactive mode: python download_generation.py --interactive
"""

import requests
import time
import sys
import os
import argparse
from typing import List, Optional, Dict, Any
import re

# =============================================================================
# CONFIGURATION - EDIT THESE VARIABLES (used when no CLI args provided)
# =============================================================================

# API Configuration
API_BASE_URL = "http://localhost:3000/api"

# Generation Configuration
GENERATION_NAME = "test_generation"
CARD_IDS = [
    "000000666 FE F",
    "000000667 FE F", 
    "000000668 FE F"
]

# Download Settings
ORIENTATION = "v"  # "v" for vertical, "h" for horizontal
OUTPUT_BASE_DIR = "data/generations_single"

# =============================================================================
# CONFIGURATION EXAMPLES:
#
# Horizontal orientation:
# ORIENTATION = "h"
#
# Different generation name:
# GENERATION_NAME = "my_custom_generation"
#
# Different cards:
# CARD_IDS = ["000001 FE F", "000002 FE F"]
#
# =============================================================================

def convert_extended_id_to_simple_id(extended_id: str) -> str:
    """
    Convert extended ID format to simple ID format.
    
    Args:
        extended_id: Extended ID like "000000057 FE F"
        
    Returns:
        Simple ID like "000000057" (no spaces or underscores)
    """
    # Remove spaces and underscores, take the first 9 digits
    cleaned = re.sub(r'[^0-9]', '', extended_id)
    if len(cleaned) >= 9:
        return cleaned[:9]
    else:
        # If somehow we don't have enough digits, pad with zeros
        return cleaned.zfill(9)

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

def download_file(url: str, local_path: str) -> bool:
    """
    Download a file from URL to local path.
    
    Args:
        url: URL to download from
        local_path: Local file path to save to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        file_size_kb = len(response.content) / 1024
        print(f"      📄 Downloaded {os.path.basename(local_path)} ({file_size_kb:.1f}KB)")
        return True
        
    except Exception as e:
        print(f"      ❌ Failed to download {os.path.basename(local_path)}: {str(e)}")
        return False

def download_generation(
    generation_name: str,
    card_ids: List[str],
    orientation: str = "v"
) -> bool:
    """
    Download TIFF cards for a generation.
    
    Args:
        generation_name: Name for the generation directory
        card_ids: List of extended card IDs
        orientation: "v" for vertical, "h" for horizontal
        
    Returns:
        True if successful, False otherwise
    """
    
    # Convert orientation shorthand
    orientation_map = {"v": "vertical", "h": "horizontal"}
    full_orientation = orientation_map.get(orientation, orientation)
    
    print(f"📦 Downloading Generation: {generation_name}")
    print(f"   🆔 Cards: {len(card_ids)} cards")
    print(f"   📐 Orientation: {full_orientation}")
    print()
    
    # Create output directory
    output_dir = os.path.join(OUTPUT_BASE_DIR, generation_name)
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Created directory: {output_dir}")
    
    # Retrieve card details
    card_details = retrieve_card_details(card_ids)
    
    if not card_details:
        print("❌ No card details retrieved. Cannot proceed.")
        return False
    
    # Download files
    total_downloaded = 0
    total_files = 0
    
    for extended_id in card_ids:
        card_data = card_details.get(extended_id)
        
        if not card_data:
            print(f"⚠️  Card not found: {extended_id}")
            continue
            
        simple_id = convert_extended_id_to_simple_id(extended_id)
        print(f"📥 Processing {extended_id} -> {simple_id}")
        
        # Determine which TIFF URLs to use based on orientation
        if full_orientation == "vertical":
            front_tiff_url = card_data.get("frontVerticalTiffUrl")
            back_tiff_url = card_data.get("backVerticalTiffUrl")
        else:  # horizontal
            front_tiff_url = card_data.get("frontHorizontalTiffUrl")
            back_tiff_url = card_data.get("backHorizontalTiffUrl")
        
        # Download front card
        if front_tiff_url:
            front_filename = f"{simple_id}-front.tiff"
            front_path = os.path.join(output_dir, front_filename)
            total_files += 1
            if download_file(front_tiff_url, front_path):
                total_downloaded += 1
        else:
            print(f"      ⚠️  No front TIFF URL for {full_orientation} orientation")
        
        # Download back card
        if back_tiff_url:
            back_filename = f"{simple_id}-back.tiff"
            back_path = os.path.join(output_dir, back_filename)
            total_files += 1
            if download_file(back_tiff_url, back_path):
                total_downloaded += 1
        else:
            print(f"      ⚠️  No back TIFF URL for {full_orientation} orientation")
        
        print()  # Add spacing between cards
    
    print(f"✅ Download complete: {total_downloaded}/{total_files} files downloaded")
    print(f"📁 Files saved to: {output_dir}")
    
    return total_downloaded > 0

def interactive_mode():
    """Run interactive mode to collect parameters."""
    print("🎯 Interactive Mode")
    print("="*30)
    
    # Get generation name
    generation_name = input("📦 Enter generation name: ").strip()
    if not generation_name:
        print("❌ Generation name cannot be empty")
        return None, None, None
    
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
        return None, None, None
    
    # Get orientation
    orientation = input("📐 Enter orientation (v for vertical, h for horizontal) [v]: ").strip()
    if not orientation:
        orientation = "v"
    
    if orientation not in ["v", "h"]:
        print(f"❌ Invalid orientation '{orientation}'. Must be 'v' or 'h'")
        return None, None, None
    
    return generation_name, card_ids, orientation

def print_configuration(generation_name: str, card_ids: List[str], orientation: str):
    """Print current configuration settings."""
    orientation_display = {"v": "vertical", "h": "horizontal"}.get(orientation, orientation)
    
    print("🛠️  Configuration:")
    print(f"   📦 Generation name: {generation_name}")
    print(f"   🆔 Card IDs: {', '.join(card_ids)}")
    print(f"   📐 Orientation: {orientation_display} ({orientation})")
    print(f"   💾 Output directory: {OUTPUT_BASE_DIR}")
    print()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download TIFF cards for a generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_generation.py --generation-name "my_gen" --ids "000000001 FE F,000000002 FE F"
  python download_generation.py --interactive
  python download_generation.py  # Uses configuration from script
        """
    )
    
    parser.add_argument(
        "--generation-name", "-g",
        type=str,
        help="Name for the generation directory"
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
    
    print("📥 SINGLE CARD GENERATION DOWNLOADER")
    print("="*50)
    print(f"🌐 API URL: {API_BASE_URL}")
    print()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Determine parameters source
    if args.interactive:
        generation_name, card_ids, orientation = interactive_mode()
        if not generation_name:
            sys.exit(1)
    elif args.generation_name or args.ids or args.orientation:
        # Use command line arguments
        generation_name = args.generation_name
        card_ids = args.ids.split(",") if args.ids else []
        orientation = args.orientation or "v"
        
        # Clean card IDs
        card_ids = [card_id.strip() for card_id in card_ids if card_id.strip()]
    else:
        # Use configuration from script
        generation_name = GENERATION_NAME
        card_ids = CARD_IDS
        orientation = ORIENTATION
        print("🔧 Using configuration from script")
    
    # Show current configuration
    print_configuration(generation_name, card_ids, orientation)
    
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
        print("\n❌ Cannot proceed without API. Please start the API server first.")
        print("   Command: uvicorn api.index:app --reload")
        sys.exit(1)
    
    print("\n" + "="*50)
    
    # Download generation
    success = download_generation(
        generation_name=generation_name,
        card_ids=card_ids,
        orientation=orientation
    )
    
    print("\n" + "="*50)
    
    if success:
        print("🎉 Generation downloaded successfully!")
        print()
        print("📋 Next steps:")
        print("   1. Check the downloaded TIFF files")
        print("   2. Use for printing or further processing")
        print()
        print("💡 Usage examples:")
        print("   python download_generation.py --generation-name 'my_gen' --ids '000000001 FE F,000000002 FE F'")
        print("   python download_generation.py --interactive")
    else:
        print("❌ Download failed!")
        print("   Check the configuration and API status, then try again")
        sys.exit(1)

if __name__ == "__main__":
    main() 