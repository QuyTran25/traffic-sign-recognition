#!/usr/bin/env python3
"""
Test Traffic Sign Recognition API
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:5000"

def test_health():
    """Test /health endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check (/health)")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_predict_crop():
    """Test /api/predict-crop endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Predict Crop (/api/predict-crop)")
    print("="*60)
    
    # Find a test image
    train_dir = Path("data/Train")
    if not train_dir.exists():
        print("❌ data/Train not found")
        return False
    
    # Get first image from first class
    for class_dir in sorted(train_dir.glob("*")):
        if class_dir.is_dir():
            images = list(class_dir.glob("*.jpg"))
            if images:
                test_image = images[0]
                print(f"Using test image: {test_image}")
                
                try:
                    with open(test_image, "rb") as f:
                        files = {"file": f}
                        response = requests.post(f"{BASE_URL}/api/predict-crop", files=files)
                    
                    print(f"Status Code: {response.status_code}")
                    result = response.json()
                    print(f"Response:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
                    
                    # Validate response structure
                    if response.status_code == 200 and result.get("success"):
                        print("\n✅ Response has correct structure:")
                        print(f"  - sign_id: {result.get('sign_id')}")
                        print(f"  - sign_name: {result.get('sign_name')}")
                        print(f"  - confidence: {result.get('confidence'):.4f}")
                        print(f"  - guidance: {result.get('guidance')[:50]}...")
                        print(f"  - audio_file: {result.get('audio_file')}")
                        return True
                except Exception as e:
                    print(f"❌ Error: {e}")
                    return False
    
    print("❌ No test image found")
    return False

def test_predict_image():
    """Test /api/predict-image endpoint"""
    print("\n" + "="*60)
    print("TEST 3: Predict Image (/api/predict-image)")
    print("="*60)
    
    # Find a detection test image
    test_images_dir = Path("data/detection/images/train")
    if not test_images_dir.exists():
        print("❌ Detection images not found")
        return False
    
    images = list(test_images_dir.glob("*.jpg"))[:1]
    if not images:
        print("❌ No test images found")
        return False
    
    test_image = images[0]
    print(f"Using test image: {test_image}")
    
    try:
        with open(test_image, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{BASE_URL}/api/predict-image", files=files)
        
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # Validate response structure
        if response.status_code == 200 and result.get("success"):
            print("\n✅ Response has correct structure:")
            print(f"  - image_size: {result.get('image_size')}")
            print(f"  - detection_count: {result.get('detection_count')}")
            
            detections = result.get('detections', [])
            if detections:
                det = detections[0]
                print(f"  - First detection:")
                print(f"    - bbox: {det.get('bbox')}")
                print(f"    - sign_id: {det.get('sign_id')}")
                print(f"    - sign_name: {det.get('sign_name')}")
                print(f"    - detector_confidence: {det.get('detector_confidence')}")
                print(f"    - classifier_confidence: {det.get('classifier_confidence')}")
                print(f"    - guidance: {det.get('guidance')[:50]}...")
                print(f"    - audio_file: {det.get('audio_file')}")
            
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return False

def test_model_exists():
    """Test if model.pth exists"""
    print("\n" + "="*60)
    print("TEST 0: Check Model File")
    print("="*60)
    model_path = Path("output/model.pth")
    if model_path.exists():
        print(f"✅ Model exists: {model_path}")
        print(f"   Size: {model_path.stat().st_size / 1024 / 1024:.2f} MB")
        return True
    else:
        print(f"❌ Model not found: {model_path}")
        return False

def test_training_log():
    """Test if training_log.json exists"""
    print("\n" + "="*60)
    print("TEST: Check Training Log")
    print("="*60)
    log_path = Path("output/training_log.json")
    if log_path.exists():
        print(f"✅ Training log exists: {log_path}")
        with open(log_path, "r") as f:
            log = json.load(f)
        print(f"   Epochs: {log.get('total_epochs')}")
        print(f"   Best epoch: {log.get('best_epoch')}")
        print(f"   Best val accuracy: {log.get('best_val_acc'):.4f}")
        return True
    else:
        print(f"❌ Training log not found: {log_path}")
        return False

if __name__ == "__main__":
    print("\n" + "🚀 "*30)
    print("TESTING TRAFFIC SIGN RECOGNITION API")
    print("🚀 "*30)
    
    # Check model first
    test_model_exists()
    test_training_log()
    
    # Test API endpoints
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Predict Crop", test_predict_crop()))
    results.append(("Predict Image", test_predict_image()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! API is working correctly!")
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Check the output above.")
