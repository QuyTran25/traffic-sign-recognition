"""
TTS Engine - Tích hợp API vclip.io để generate audio cho 43 biển báo
"""

import json
import os
import time
import requests
import logging
from pathlib import Path
from typing import Optional, Dict, List
import sys

# ============================================
# CONFIGURATION
# ============================================

# API Configuration
VCLIP_API_ENDPOINT = "https://api-tts.vclip.io/json-rpc"
VCLIP_API_KEY = os.getenv("VCLIP_API_KEY", "")  # API Key từ vclip.io (set via environment variable)
VCLIP_VOICE_ID = "8VXsCLxU7Pn55ADXQc6sAb"  # Voice ID của Adam
VCLIP_SPEED = 0.9  # Tốc độ đọc (0.5 - 2.0)

# Paths
BASE_DIR = Path(__file__).parent.parent
GUIDANCE_FILE = BASE_DIR / "guidance_texts_vi.json"
OUTPUT_AUDIO_DIR = BASE_DIR / "output" / "audio"

# Polling Configuration
POLLING_INTERVAL = 0  # giây (không dừng giữa polling)
MAX_POLLING_ATTEMPTS = 300  # 300 * 0 = không timeout (liên tục polling)
RETRY_ATTEMPTS = 3

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / "output" / "tts_generation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# VCLIP API FUNCTIONS
# ============================================

def check_api_key():
    """Kiểm tra API key có được cung cấp không"""
    if not VCLIP_API_KEY or VCLIP_API_KEY == "":
        logger.error("❌ LỖI: VCLIP_API_KEY chưa được cung cấp!")
        logger.error("   Hãy đặt environment variable: set VCLIP_API_KEY=your_api_key")
        return False
    return True


def call_tts_api(text: str, voice_id: str = VCLIP_VOICE_ID, speed: float = VCLIP_SPEED) -> Optional[str]:
    """
    Gọi vclip.io API để tạo audio
    Return: projectExportId nếu thành công, None nếu thất bại
    """
    try:
        headers = {
            "Authorization": f"Bearer {VCLIP_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "method": "ttsLongText",
            "input": {
                "text": text,
                "userVoiceId": voice_id,
                "speed": speed
            }
        }
        
        logger.info(f"📝 Gọi TTS API: text='{text[:50]}...'")
        
        response = requests.post(VCLIP_API_ENDPOINT, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # Kiểm tra lỗi từ API
        if "error" in result:
            logger.error(f"❌ API Error: {result['error']}")
            return None
        
        if "result" in result and "projectExportId" in result["result"]:
            export_id = result["result"]["projectExportId"]
            logger.info(f"✅ Tạo export ID: {export_id}")
            return export_id
        
        logger.error(f"❌ Unexpected API response: {result}")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request Error: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error calling TTS API: {e}")
        return None


def get_export_status(export_id: str) -> Optional[Dict]:
    """
    Check status của audio export
    Return: Dict với status và URL, None nếu thất bại
    """
    try:
        headers = {
            "Authorization": f"Bearer {VCLIP_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "method": "getExportStatus",
            "input": {
                "projectExportId": export_id
            }
        }
        
        response = requests.post(VCLIP_API_ENDPOINT, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if "error" in result:
            logger.error(f"❌ API Error: {result['error']}")
            return None
        
        if "result" in result:
            return result["result"]
        
        logger.error(f"❌ Unexpected API response: {result}")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request Error: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error getting export status: {e}")
        return None


def poll_until_completed(export_id: str, max_attempts: int = MAX_POLLING_ATTEMPTS) -> Optional[str]:
    """
    Poll API cho đến khi audio hoàn tất
    Return: URL của audio file, None nếu timeout/error
    """
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        
        status_result = get_export_status(export_id)
        
        if not status_result:
            logger.warning(f"⚠️  Polling attempt {attempt}/{max_attempts} failed")
            time.sleep(POLLING_INTERVAL)
            continue
        
        state = status_result.get("state", "")
        progress = status_result.get("progress", 0)
        
        logger.info(f"⏳ Polling ({attempt}/{max_attempts}): state={state}, progress={progress}%")
        
        if state == "completed":
            url = status_result.get("url", "")
            if url:
                logger.info(f"✅ Audio completed! URL: {url}")
                return url
            else:
                logger.error(f"❌ completed nhưng không có URL")
                return None
        
        elif state == "failed":
            logger.error(f"❌ Audio generation failed")
            return None
        
        elif state == "processing":
            time.sleep(POLLING_INTERVAL)
            continue
        
        else:
            logger.warning(f"⚠️  Unknown state: {state}")
            time.sleep(POLLING_INTERVAL)
            continue
    
    logger.error(f"❌ Polling timeout sau {max_attempts} attempts")
    return None


def download_audio(url: str, output_path: Path) -> bool:
    """
    Download audio file từ URL
    Return: True nếu thành công
    """
    try:
        logger.info(f"📥 Downloading audio từ: {url}")
        
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Tạo directory nếu chưa tồn tại
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        file_size = output_path.stat().st_size
        logger.info(f"✅ Downloaded: {output_path} ({file_size} bytes)")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Download error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error saving audio: {e}")
        return False


def generate_audio_for_sign(sign_id: int, text: str) -> bool:
    """
    Generate audio cho một biển báo
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"🔄 Processing Sign #{sign_id}")
    logger.info(f"   Text: {text[:80]}...")
    logger.info(f"{'='*60}")
    
    for attempt in range(RETRY_ATTEMPTS):
        try:
            # Bước 1: Gọi TTS API
            export_id = call_tts_api(text)
            if not export_id:
                logger.warning(f"⚠️  Attempt {attempt + 1}/{RETRY_ATTEMPTS}: Không thể tạo export ID")
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(2)
                continue
            
            # Bước 2: Poll cho đến khi hoàn tất
            audio_url = poll_until_completed(export_id)
            if not audio_url:
                logger.warning(f"⚠️  Attempt {attempt + 1}/{RETRY_ATTEMPTS}: Polling timeout/failed")
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(2)
                continue
            
            # Bước 3: Download audio file
            output_filename = f"sign_{sign_id:02d}.mp3"
            output_path = OUTPUT_AUDIO_DIR / output_filename
            
            if download_audio(audio_url, output_path):
                logger.info(f"✅ Sign #{sign_id} hoàn tất thành công!")
                return True
            else:
                logger.warning(f"⚠️  Attempt {attempt + 1}/{RETRY_ATTEMPTS}: Download failed")
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(2)
                continue
        
        except Exception as e:
            logger.error(f"❌ Attempt {attempt + 1}/{RETRY_ATTEMPTS} Exception: {e}")
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(2)
            continue
    
    logger.error(f"❌ FAILED sign #{sign_id} sau {RETRY_ATTEMPTS} attempts")
    return False


# ============================================
# MAIN GENERATION FUNCTIONS
# ============================================

def load_guidance_texts() -> Optional[Dict[str, str]]:
    """Load file guidance_texts_vi.json"""
    try:
        if not GUIDANCE_FILE.exists():
            logger.error(f"❌ File không tồn tại: {GUIDANCE_FILE}")
            return None
        
        with open(GUIDANCE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"✅ Loaded {len(data)} guidance texts từ {GUIDANCE_FILE}")
        return data
    
    except Exception as e:
        logger.error(f"❌ Error loading guidance texts: {e}")
        return None


def generate_all_audio():
    """Generate audio cho tất cả 43 biển báo"""
    
    # Kiểm tra API key
    if not check_api_key():
        return False
    
    # Load guidance texts
    guidance_texts = load_guidance_texts()
    if not guidance_texts:
        return False
    
    # Tạo output directory
    OUTPUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Output directory: {OUTPUT_AUDIO_DIR}")
    
    # Generate audio cho từng sign
    successful = 0
    failed = 0
    failed_signs = []
    
    total_signs = len(guidance_texts)
    
    logger.info(f"\n🚀 BẮT ĐẦU GENERATE {total_signs} AUDIO FILES\n")
    
    start_time = time.time()
    
    for sign_id, text in sorted(guidance_texts.items(), key=lambda x: int(x[0])):
        sign_id_int = int(sign_id)
        
        if generate_audio_for_sign(sign_id_int, text):
            successful += 1
        else:
            failed += 1
            failed_signs.append(sign_id_int)
    
    elapsed = time.time() - start_time
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 GENERATION SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"✅ Successful: {successful}/{total_signs}")
    logger.info(f"❌ Failed: {failed}/{total_signs}")
    logger.info(f"⏱️  Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    
    if failed_signs:
        logger.warning(f"Failed signs: {failed_signs}")
    
    logger.info(f"{'='*60}\n")
    
    return failed == 0


def verify_generated_files() -> List[str]:
    """
    Verify tất cả 43 file .mp3 có được tạo không
    Return: List các file đã tạo
    """
    logger.info(f"\n🔍 VERIFYING GENERATED FILES\n")
    
    OUTPUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    missing_files = []
    
    for sign_id in range(43):
        filename = f"sign_{sign_id:02d}.mp3"
        filepath = OUTPUT_AUDIO_DIR / filename
        
        if filepath.exists():
            file_size = filepath.stat().st_size
            logger.info(f"✅ {filename:20} ({file_size:,} bytes)")
            generated_files.append(str(filepath))
        else:
            logger.warning(f"❌ {filename:20} MISSING")
            missing_files.append(sign_id)
    
    logger.info(f"\n📊 VERIFICATION SUMMARY")
    logger.info(f"   Generated: {len(generated_files)}/43")
    logger.info(f"   Missing: {len(missing_files)}/43")
    
    if missing_files:
        logger.warning(f"   Missing sign IDs: {missing_files}")
    
    logger.info()
    
    return generated_files


# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎙️  TTS AUDIO GENERATION ENGINE")
    print("="*60 + "\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        # Chỉ verify, không generate
        verify_generated_files()
    else:
        # Generate audio cho tất cả signs
        success = generate_all_audio()
        
        # Verify kết quả
        print()
        verify_generated_files()
        
        if success:
            print("\n✅ Tất cả audio files đã được generate thành công!\n")
        else:
            print("\n⚠️  Một số file không được generate, vui lòng kiểm tra log.\n")
