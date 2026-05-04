#!/usr/bin/env python
"""Test audio feature in API"""

import requests
from pathlib import Path

# Test image
image_path = Path('data/detection/images/train') / 'OIP (1).jpg'
url = 'http://127.0.0.1:5000/api/predict-image'

print("\n" + "="*80)
print("🔊 TESTING AUDIO FEATURE")
print("="*80)

with open(image_path, 'rb') as f:
    response = requests.post(url, files={'file': f})
    result = response.json()
    
    if result.get('success'):
        detections = result.get('detections', [])
        for i, det in enumerate(detections, 1):
            sign_id = det.get('sign_id')
            sign_name = det.get('sign_name')
            audio_file = det.get('audio_file')
            
            print(f"\nDetection {i}:")
            print(f"  Sign ID: {sign_id}")
            print(f"  Sign Name: {sign_name}")
            print(f"  Audio File: {audio_file}")
            
            # Check if audio file exists
            if audio_file:
                audio_path = Path('output/audio') / audio_file
                if audio_path.exists():
                    file_size = audio_path.stat().st_size / 1024
                    print(f"  ✅ Audio found: {audio_file} ({file_size:.1f} KB)")
                    print(f"  🔗 URL: /api/audio/{audio_file}")
                else:
                    print(f"  ❌ Audio file NOT found at: {audio_path}")
            else:
                print(f"  ⚠ No audio file returned")

print("\n" + "="*80)
