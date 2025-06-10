"""
Simple test script for print generation API with hardcoded IDs.
Run this to quickly test the A4 layout generation.
"""

import requests
import json
import time

# API Configuration
API_BASE_URL = "http://localhost:8000/api"

# Hardcoded test card IDs - replace these with actual IDs from your database
TEST_CARD_IDS = [
    "000000632 FE F",
    "000000633 FE F",
    "000000634 FE F"
]

def run_a4():
    """Test the print generation with hardcoded IDs."""
    
    print("🖨️  Testing Print Generation API")
    print("="*50)
    
    # Test case 1: 8mm passepartout (standard)
    print("\n🎨 Test 1: Standard 8mm passepartout")
    request_data = {
        "extended_ids": TEST_CARD_IDS,
        "passepartout_mm": 8,
        "target_content_width_mm": 146
    }
    
    print(f"   📋 Request: {len(TEST_CARD_IDS)} cards with 8mm border")
    print(f"   🆔 IDs: {', '.join(TEST_CARD_IDS)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/create-a4-layouts",
            json=request_data,
            timeout=60
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success! ({duration:.1f}s)")
            print(f"   📊 Cards found: {result['cards_found']}/{len(TEST_CARD_IDS)}")
            print(f"   📊 Cards processed: {result['cards_processed']}")
            
            if result.get('front_layout_size_mb'):
                print(f"   📄 Front layout: {result['front_layout_size_mb']:.1f}MB")
                if result.get('front_layout_file'):
                    print(f"   💾 Front file: {result['front_layout_file']}")
            
            if result.get('back_layout_size_mb'):
                print(f"   📄 Back layout: {result['back_layout_size_mb']:.1f}MB")
                if result.get('back_layout_file'):
                    print(f"   💾 Back file: {result['back_layout_file']}")
                
            print(f"   💬 {result['message']}")
            
        else:
            print(f"   ❌ Error {response.status_code}")
            print(f"   📝 Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {str(e)}")
    

def check_api_status():
    """Check if the API is running."""
    
    print("🔍 Checking API status...")
    
    try:
        # Try to reach the API
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

def main():
    print("🖨️  PRINT GENERATION API TESTER")
    print("="*50)
    print(f"🌐 API URL: {API_BASE_URL}")
    print(f"🆔 Test card IDs: {', '.join(TEST_CARD_IDS)}")
    print()
    
    # Check API status first
    if not check_api_status():
        print("\n❌ Cannot proceed without API. Please start the API server first.")
        return
    
    print("\n" + "="*50)
    
    # Run tests
    run_a4()

    print("\n" + "="*50)
    print("🎉 Testing complete!")
    print()
    print("💡 To modify test cards, edit the TEST_CARD_IDS list at the top of this script")
    print("💡 Make sure the card IDs exist in your database and have TIFF files")


if __name__ == "__main__":
    main() 