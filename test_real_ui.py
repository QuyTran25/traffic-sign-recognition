#!/usr/bin/env python
"""Test the API endpoints with actual image"""

import requests
import json
from pathlib import Path

# Test image paths
test_images = [
    'data/detection/images/train/OIP (1).jpg',
    'data/detection/images/train/OIP (11).jpg',
    'data/detection/images/train/OIP (12).jpg'
]

api_url = 'http://127.0.0.1:5000/api/predict-image'

print("\n" + "="*80)
print("🧪 TESTING API ON REAL PROJECT IMAGES")
print("="*80 + "\n")

for i, image_path in enumerate(test_images, 1):
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}\n")
        continue
    
    print(f"Test {i}: {Path(image_path).name}")
    print("-" * 80)
    
    try:
        with open(image_path, 'rb') as f:
            response = requests.post(api_url, files={'file': f}, timeout=10)
        
        print(f"✅ Status Code: {response.status_code}")
        
        result = response.json()
        
        if result.get('success'):
            print(f"✅ Detections Found: {result.get('detection_count', 0)}")
            
            for j, det in enumerate(result.get('detections', []), 1):
                print(f"\n   Detection {j}:")
                print(f"   • Sign ID: {det.get('sign_id')}")
                print(f"   • Sign Name: {det.get('sign_name')}")
                print(f"   • Detector Conf: {det.get('detector_confidence'):.2%}")
                print(f"   • Classifier Conf: {det.get('classifier_confidence'):.2%}")
                print(f"   • BBox: {det.get('bbox')}")
                print(f"   • Guidance: {det.get('guidance', '')[:60]}...")
        else:
            print(f"❌ Error: {result.get('error_message', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n")

print("="*80)
print("✅ Testing completed!")
print("="*80)
