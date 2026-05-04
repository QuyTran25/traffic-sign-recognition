#!/usr/bin/env python
"""
Quick test script to classify a single traffic sign image
Usage: python test_with_image.py <image_path>
"""

import cv2
import json
import requests
import sys
from pathlib import Path

def test_crop(image_path):
    """Test single crop prediction"""
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return
    
    print(f"\n🔍 Testing crop classification on: {image_path}")
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        try:
            response = requests.post('http://127.0.0.1:5000/api/predict-crop', files=files)
            result = response.json()
            
            if result.get('success'):
                print(f"""
✅ CLASSIFICATION SUCCESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sign ID: {result['sign_id']}
Sign Name: {result['sign_name']}
Confidence: {result['confidence']:.2%}
Guidance: {result['guidance'][:100]}...
""")
            else:
                print(f"❌ Classification failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Error: {e}")

def test_full_image(image_path):
    """Test full image detection"""
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return
    
    print(f"\n🔍 Testing full image detection on: {image_path}")
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        try:
            response = requests.post('http://127.0.0.1:5000/api/predict-image', files=files)
            result = response.json()
            
            if result.get('success'):
                print(f"""
✅ DETECTION SUCCESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Image Size: {result['image_size']}
Detections Found: {result['detection_count']}
""")
                for i, det in enumerate(result['detections'], 1):
                    print(f"""
Detection {i}:
  • Sign: {det['sign_name']} (ID: {det['sign_id']})
  • Confidence: Detector={det['detector_confidence']:.2%}, Classifier={det['classifier_confidence']:.2%}
  • BBox: {det['bbox']}
  • Guidance: {det['guidance'][:80]}...
""")
            else:
                print(f"❌ Detection failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        # Use test images from data directory
        test_images = [
            'data/Train/0/crop_000014_train.jpg',
            'data/detection/images/train/OIP (1).jpg'
        ]
        print("""
╔════════════════════════════════════════╗
║   Traffic Sign Recognition Test        ║
╚════════════════════════════════════════╝

Usage: python test_with_image.py <image_path>

Running with default test images...
""")
        for img in test_images:
            if Path(img).exists():
                test_crop(img)
            else:
                print(f"⚠ Test image not found: {img}")
    else:
        image_path = sys.argv[1]
        mode = sys.argv[2] if len(sys.argv) > 2 else 'crop'
        
        if mode == 'image':
            test_full_image(image_path)
        else:
            test_crop(image_path)
