#!/usr/bin/env python3
"""
Quick test function for experimenting with passepartout values
Usage: python quick_test.py
"""

from PIL import Image
from api.utils.print_utils import create_a4_layout_with_cards

def test_layout(passepartout_mm=8, filename=None):
    """
    Quick test function to generate A4 layout
    
    Args:
        passepartout_mm (float): Passepartout in millimeters (default: 8)
        filename (str): Output filename (default: auto-generated)
    """
    
    # Create 3 test cards
    cards = [
        Image.new('RGB', (708, 1416), '#FF0000'),  # Red
        Image.new('RGB', (708, 1416), '#00FF00'),  # Green  
        Image.new('RGB', (708, 1416), '#0000FF'),  # Blue
    ]
    
    # Generate layout
    layout_bytes = create_a4_layout_with_cards(
        card_images=cards,
        passepartout_mm=passepartout_mm,
        output_format="PNG"
    )
    
    # Auto-generate filename if not provided
    if filename is None:
        filename = f"test_{passepartout_mm}mm_passepartout.png"
    
    # Save to file
    with open(filename, "wb") as f:
        f.write(layout_bytes)
    
    print(f"✅ Generated: {filename} ({len(layout_bytes)/1024:.1f}KB)")
    print(f"   Content: 14.6×7.3cm")
    print(f"   Passepartout: {passepartout_mm}mm")
    if passepartout_mm > 0:
        final_w = 14.6 + (passepartout_mm/10)*2
        final_h = 7.3 + (passepartout_mm/10)*2
        print(f"   Final size: {final_w}×{final_h}cm")
    else:
        print(f"   Final size: 14.6×7.3cm (same as content)")

if __name__ == "__main__":
    print("🧪 Quick Layout Tester")
    print("=" * 40)
    
    # Test different passepartout values
    test_values = [0, 5, 8, 10, 15]
    
    for passepartout in test_values:
        test_layout(passepartout)
    
    print(f"\n🎉 Generated {len(test_values)} test layouts!")
    print(f"\n📋 To test your own values:")
    print(f"   from quick_test import test_layout")
    print(f"   test_layout(passepartout_mm=12)  # Test 12mm passepartout") 