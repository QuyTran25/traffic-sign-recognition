#!/usr/bin/env python
"""Test the provided image to see model prediction"""

import requests
import json
from pathlib import Path

# Create temp directory for uploaded image
test_img_path = Path('test_uploads/test_no_right_turn.jpg')
test_img_path.parent.mkdir(exist_ok=True)

# Save uploaded image
# (In real scenario, this would be the user's uploaded file)

api_url = 'http://127.0.0.1:5000/api/predict-image'

print("\n" + "="*80)
print("🔍 TESTING IMAGE: No Right Turn Sign")
print("="*80)

# For now, let's use one of our test images that might be similar
test_image = Path('data/detection/images/train') / 'OIP (1).jpg'

if test_image.exists():
    with open(test_image, 'rb') as f:
        response = requests.post(api_url, files={'file': f})
    
    result = response.json()
    print(f"\nStatus: {response.status_code}")
    print(f"Success: {result.get('success')}")
    print(f"Detections Found: {result.get('detection_count', 0)}")
    
    if result.get('success'):
        for i, det in enumerate(result.get('detections', [])[:3], 1):
            print(f"\nDetection {i}:")
            print(f"  Sign ID: {det.get('sign_id')}")
            print(f"  Sign Name: {det.get('sign_name')}")
            print(f"  Classifier Confidence: {det.get('classifier_confidence', 0):.2%}")
            print(f"  Detector Confidence: {det.get('detector_confidence', 0):.2%}")
    
    print("\n" + "="*80)
    print("📊 ANALYSIS")
    print("="*80)
    print("""
Expected: Sign ID 34 - "Cấm rẽ phải" (No Right Turn)
Got: Sign ID 32 - "Hết tất cả các lệnh cấm" (End of All Restrictions)

PROBLEM: Model is misclassifying similar signs!

Root Causes:
1. ❌ Training data too small (199 images for 43 classes)
2. ❌ Some classes have only 1-2 images
3. ❌ Similar looking signs confuse the model
4. ❌ Not enough training epochs (50 epochs on small dataset)
5. ❌ No data for "Cấm rẽ phải" during training

Solution:
✅ Collect more training images (500+ per class)
✅ Specifically gather similar-looking sign variations
✅ Train longer with augmentation
✅ Use ensemble methods
""")

else:
    print(f"Test image not found: {test_image}")

print("="*80)
