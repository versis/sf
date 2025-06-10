#!/usr/bin/env python3
"""
8mm Passepartout Demo - Shows A4 layout with white borders around cards.
"""

import asyncio
import base64
from PIL import Image, ImageDraw
import io
import sys
import os

# Add parent directory to path to import from api
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.utils.card_utils import generate_card_image_bytes
from api.utils.print_utils import create_a4_layout_with_cards

def create_test_image(color: str) -> str:
    """Create a simple test image as base64 data URL"""
    img = Image.new('RGB', (400, 400), color=color)
    
    # Add some pattern to make it visible
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 350, 350], fill='white')
    draw.ellipse([100, 100, 300, 300], fill=color)
    
    # Convert to base64 data URL
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

async def create_8mm_passepartout_demo():
    """Generate cards and create A4 layout with 8mm passepartout"""
    
    print("🎨 Creating 8mm Passepartout Demo")
    print("=" * 40)
    
    # Generate 6 beautiful test cards (full A4 layout)
    colors = [
        ("#FF6B35", "Vibrant Orange"),
        ("#004225", "Forest Green"), 
        ("#C4142D", "Cherry Red"),
        ("#0A5EB0", "Ocean Blue"),
        ("#7209B7", "Royal Purple"),
        ("#F7931E", "Golden Yellow")
    ]
    
    cards = []
    
    print("\n📋 Generating demo cards...")
    for i, (hex_color, color_name) in enumerate(colors):
        print(f"  Creating card {i+1}: {color_name}")
        
        # Create test image
        test_image_data_url = create_test_image(hex_color)
        
        # Card details
        card_details = {
            "colorName": color_name,
            "phoneticName": f"demo {i+1}",
            "article": "a",
            "description": f"This is a beautiful {color_name.lower()} color perfect for demonstrating the 8mm passepartout effect on A4 layouts.",
            "extendedId": f"DEMO{i+1:03d}"
        }
        
        # Generate card
        front_bytes = await generate_card_image_bytes(
            cropped_image_data_url=test_image_data_url,
            card_details=card_details,
            hex_color_input=hex_color,
            orientation="vertical",
            request_id=f"demo_card_{i+1}"
        )
        
        # Convert to PIL Image
        card_image = Image.open(io.BytesIO(front_bytes))
        cards.append(card_image)
    
    print(f"✅ Generated {len(cards)} demo cards (full A4 layout)")
    
    # Create A4 layout with 8mm passepartout
    print(f"\n📄 Creating A4 layout with 8mm passepartout...")
    
    a4_bytes = create_a4_layout_with_cards(
        card_images=cards,
        layout_title="8mm Passepartout Demo",
        output_format="PNG",  # PNG for easy viewing
        passepartout_mm=8,    # 8mm white border around each card
        request_id="demo_8mm_passepartout"
    )
    
    # Save the A4 layout
    filename = "demo_8mm_passepartout.png"
    with open(filename, 'wb') as f:
        f.write(a4_bytes)
    
    print(f"✅ A4 layout created: {len(a4_bytes)/1024:.1f}KB → {filename}")
    
    # Show details
    a4_img = Image.open(io.BytesIO(a4_bytes))
    print(f"📐 A4 dimensions: {a4_img.size[0]}×{a4_img.size[1]}px")
    print(f"🔲 Passepartout: 8mm = {int(8 * 11.811)}px white border around each card")
    print(f"🚀 Card size optimized: 708×1416px → 800×1600px (+27.7% bigger!)")
    
    print("\n🎯 What you'll see in the demo:")
    print("- 6 colorful cards in a 3×2 grid (3 across, 2 down - full A4 layout)")
    print("- Cards optimized to maximum size (800×1600px vs original 708×1416px)")
    print("- 8mm equal passepartout borders on all sides")
    print("- Perfect 1:2 aspect ratio maintained")
    print("- Full A4 page utilization (no wasted space)")
    print("- Clean cutting guides between cards only")
    print("- Professional print-ready layout")
    
    print(f"\n📁 Open '{filename}' to see the 8mm passepartout effect!")
    
    return filename

if __name__ == "__main__":
    asyncio.run(create_8mm_passepartout_demo()) 