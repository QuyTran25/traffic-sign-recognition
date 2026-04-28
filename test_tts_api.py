"""
Test Script - Kiểm tra cấu hình vclip.io API trước khi generate
"""

import os
import sys
import json
import requests
from pathlib import Path

# ============================================
# CONFIGURATION
# ============================================

VCLIP_API_ENDPOINT = "https://api-tts.vclip.io/json-rpc"
VCLIP_API_KEY = os.getenv("VCLIP_API_KEY", "")
VCLIP_VOICE_ID = "8VXsCLxU7Pn55ADXQc6sAb"

BASE_DIR = Path(__file__).parent.parent
OUTPUT_AUDIO_DIR = BASE_DIR / "output" / "audio"

# ============================================
# TEST FUNCTIONS
# ============================================

def print_section(title: str):
    """Print một section header"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")


def test_api_key():
    """Test 1: Kiểm tra API Key có được cung cấp không"""
    print_section("TEST 1: API Key Configuration")
    
    if not VCLIP_API_KEY or VCLIP_API_KEY == "":
        print("❌ FAIL: VCLIP_API_KEY chưa được cung cấp")
        print("\n   Giải pháp:")
        print("   1. Lấy API Key từ vclip.io")
        print("   2. Đặt environment variable:")
        print("      $env:VCLIP_API_KEY = 'your_api_key'  (PowerShell)")
        print("      set VCLIP_API_KEY=your_api_key       (CMD)")
        print("      export VCLIP_API_KEY='your_api_key'  (Bash)")
        return False
    
    print(f"✅ PASS: API Key đã được cung cấp")
    print(f"   Key (first 10 chars): {VCLIP_API_KEY[:10]}...")
    return True


def test_api_connectivity():
    """Test 2: Kiểm tra kết nối tới API"""
    print_section("TEST 2: API Connectivity")
    
    try:
        headers = {
            "Authorization": f"Bearer {VCLIP_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Test với request đơn giản
        test_payload = {
            "method": "getExportStatus",
            "input": {"projectExportId": "test_123"}
        }
        
        print("📡 Gửi request test tới API...")
        response = requests.post(VCLIP_API_ENDPOINT, json=test_payload, headers=headers, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            print("✅ PASS: API connectivity OK")
            return True
        else:
            print(f"❌ FAIL: API returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except requests.exceptions.Timeout:
        print("❌ FAIL: Request timeout")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ FAIL: Connection error (check internet)")
        return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_voice_id():
    """Test 3: Kiểm tra Voice ID"""
    print_section("TEST 3: Voice ID Configuration")
    
    print(f"Voice ID: {VCLIP_VOICE_ID}")
    
    if len(VCLIP_VOICE_ID) > 10:
        print("✅ PASS: Voice ID có format hợp lệ")
        return True
    else:
        print("⚠️  WARNING: Voice ID có vẻ không đúng")
        return False


def test_tts_api_call():
    """Test 4: Thử gọi TTS API với text đơn giản"""
    print_section("TEST 4: TTS API Call (Generate Audio)")
    
    try:
        headers = {
            "Authorization": f"Bearer {VCLIP_API_KEY}",
            "Content-Type": "application/json"
        }
        
        test_text = "Xin chào, đây là test gọi API vclip"
        
        payload = {
            "method": "ttsLongText",
            "input": {
                "text": test_text,
                "userVoiceId": VCLIP_VOICE_ID,
                "speed": 1.0
            }
        }
        
        print(f"📝 Text: {test_text}")
        print(f"🎙️  Voice ID: {VCLIP_VOICE_ID}")
        print(f"⚡ Speed: 1.0")
        print("\n📡 Gửi request TTS...")
        
        response = requests.post(VCLIP_API_ENDPOINT, json=payload, headers=headers, timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAIL: API returned {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        
        if "error" in result:
            print(f"❌ FAIL: API Error: {result['error']}")
            return False
        
        if "result" in result and "projectExportId" in result["result"]:
            export_id = result["result"]["projectExportId"]
            print(f"✅ PASS: Export ID tạo thành công")
            print(f"   Export ID: {export_id}")
            return True
        else:
            print(f"❌ FAIL: Unexpected response: {result}")
            return False
    
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_output_directory():
    """Test 5: Kiểm tra output directory"""
    print_section("TEST 5: Output Directory")
    
    try:
        OUTPUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        
        # Test write permission
        test_file = OUTPUT_AUDIO_DIR / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        
        print(f"📁 Output Directory: {OUTPUT_AUDIO_DIR}")
        print(f"✅ PASS: Directory writable")
        
        # Count existing files
        existing_files = list(OUTPUT_AUDIO_DIR.glob("sign_*.mp3"))
        print(f"   Existing audio files: {len(existing_files)}/43")
        
        return True
    
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_guidance_json():
    """Test 6: Kiểm tra guidance_texts_vi.json"""
    print_section("TEST 6: Guidance JSON File")
    
    guidance_file = BASE_DIR / "guidance_texts_vi.json"
    
    try:
        if not guidance_file.exists():
            print(f"❌ FAIL: File không tồn tại: {guidance_file}")
            return False
        
        with open(guidance_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📄 File: {guidance_file}")
        print(f"✅ PASS: JSON valid")
        print(f"   Total entries: {len(data)}")
        
        if len(data) == 43:
            print(f"   ✅ Có đủ 43 guidance texts")
            return True
        else:
            print(f"   ⚠️  Expected 43, got {len(data)}")
            return True
    
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


# ============================================
# MAIN TEST RUNNER
# ============================================

def run_all_tests():
    """Chạy tất cả tests"""
    
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "🧪 TTS API CONFIGURATION TEST" + " "*14 + "║")
    print("╚" + "="*58 + "╝")
    
    tests = [
        ("API Key", test_api_key),
        ("Guidance JSON", test_guidance_json),
        ("Output Directory", test_output_directory),
        ("Voice ID", test_voice_id),
        ("API Connectivity", test_api_connectivity),
        ("TTS API Call", test_tts_api_call),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ FAIL: Unexpected error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Print Summary
    print_section("📊 TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 Tất cả tests pass! Bạn có thể chạy:")
        print("   python src/tts_engine.py")
    else:
        print("\n⚠️  Một số tests fail, vui lòng fix theo hướng dẫn trên")
    
    print()
    
    return passed == total


# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
