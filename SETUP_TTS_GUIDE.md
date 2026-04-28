# 🎙️ TTS Audio Generation - Setup & Usage Guide

## 📋 Tổng Quan

File `src/tts_engine.py` tích hợp API vclip.io để generate audio cho 43 biển báo giao thông.

**Voice:** Adam (ID: 8VXsCLxU7Pn55ADXQc6sAb)
**Speed:** 1.0 (điều chỉnh được 0.5 - 2.0)
**Output:** 43 file .mp3 → `output/audio/sign_00.mp3` → `sign_42.mp3`

---

## 🔑 Bước 1: Cung Cấp API Key

### 1.1 Lấy API Key từ vclip.io
1. Đăng nhập tài khoản vclip.io
2. Vào phần Profile/Settings
3. Copy API Key

### 1.2 Đặt Environment Variable

**Windows (PowerShell):**
```powershell
$env:VCLIP_API_KEY = "your_api_key_here"
echo $env:VCLIP_API_KEY  # Verify
```

**Windows (CMD):**
```cmd
set VCLIP_API_KEY=your_api_key_here
echo %VCLIP_API_KEY%
```

**Linux/Mac:**
```bash
export VCLIP_API_KEY="your_api_key_here"
echo $VCLIP_API_KEY
```

---

## 📦 Bước 2: Install Dependencies

```bash
# Cài đặt requirements
pip install -r requirements.txt

# Hoặc chỉ cài requests + dependencies cần thiết
pip install requests>=2.31.0
```

---

## 🚀 Bước 3: Generate Audio Files

### 3.1 Generate tất cả 43 audio files

```bash
python src/tts_engine.py
```

**Quá trình:**
- Đọc 43 guidance texts từ `guidance_texts_vi.json`
- Gọi vclip.io API cho mỗi text
- Polling status (2-3 giây) cho đến khi hoàn tất
- Download .mp3 file vào `output/audio/`
- Retry 3 lần nếu fail
- Sinh ra log file: `output/tts_generation.log`

**Thời gian ước tính:** ~43-86 giây (2 giây per file polling)

### 3.2 Output Example

```
✅ sign_00.mp3 (45,234 bytes) - Giới hạn tốc độ (20km/h)
✅ sign_01.mp3 (48,567 bytes) - Giới hạn tốc độ (30km/h)
✅ sign_02.mp3 (51,890 bytes) - Giới hạn tốc độ (50km/h)
...
✅ sign_42.mp3 (52,123 bytes) - Hết cấm xe tải vượt
```

---

## ✅ Bước 4: Verify Files

### 4.1 Chỉ Verify (không generate)

```bash
python src/tts_engine.py verify
```

Output:
```
🔍 VERIFYING GENERATED FILES

✅ sign_00.mp3          (45,234 bytes)
✅ sign_01.mp3          (48,567 bytes)
✅ sign_02.mp3          (51,890 bytes)
...
✅ sign_42.mp3          (52,123 bytes)

📊 VERIFICATION SUMMARY
   Generated: 43/43
   Missing: 0/43
```

### 4.2 Test Nghe Audio

```bash
# Windows
start output/audio/sign_01.mp3

# Linux
play output/audio/sign_01.mp3  # hoặc open

# Mac
open output/audio/sign_01.mp3
```

---

## 🔧 Configuration (Tùy Chỉnh)

Nếu muốn điều chỉnh, edit file `src/tts_engine.py`:

```python
# Line 30: Thay đổi speed (0.5 - 2.0)
VCLIP_SPEED = 1.0  # Thay thành 0.8 hoặc 1.2

# Line 26: Thay đổi voice ID
VCLIP_VOICE_ID = "8VXsCLxU7Pn55ADXQc6sAb"

# Line 35: Thay đổi polling interval
POLLING_INTERVAL = 2  # giây (1-5)

# Line 36: Thay đổi max polling attempts
MAX_POLLING_ATTEMPTS = 300  # 10 phút timeout
```

---

## 📊 Log File

Tất cả thông tin được lưu vào: `output/tts_generation.log`

**View log:**
```bash
# Windows
type output/tts_generation.log

# Linux/Mac
cat output/tts_generation.log

# Real-time monitoring
tail -f output/tts_generation.log
```

---

## 🐛 Troubleshooting

### ❌ Lỗi: "VCLIP_API_KEY chưa được cung cấp"

**Giải pháp:**
```bash
# Đặt environment variable
$env:VCLIP_API_KEY = "your_key"

# Hoặc edit src/tts_engine.py line 25
VCLIP_API_KEY = "your_key"  # Tạm thời cho testing

# Chạy lại
python src/tts_engine.py
```

### ❌ Lỗi: "ModuleNotFoundError: No module named 'requests'"

**Giải pháp:**
```bash
pip install requests
```

### ❌ Lỗi: "API Error: Invalid voice ID"

**Giải pháp:**
1. Kiểm tra voice ID có chính xác không
2. Đảm bảo voice ID đã được approve trong tài khoản vclip.io
3. Thử dùng voice ID khác

### ❌ Lỗi: "Polling timeout"

**Giải pháp:**
- Tăng MAX_POLLING_ATTEMPTS (dòng 36)
- Kiểm tra internet connection
- Retry sau 5-10 phút

### ⚠️ Một số file failed

**Giải pháp:**
1. File tts_engine.py sẽ **tự động retry 3 lần**
2. Nếu vẫn fail, xem log file để biết chi tiết
3. Retry bằng lệnh `python src/tts_engine.py`

---

## 🎯 Integration với Flask App

Sau khi generate xong, file .mp3 sẽ được gọi từ `app.py`:

```python
# app.py - Return audio file path
return jsonify({
    'success': True,
    'sign_name_vi': sign_name,
    'confidence': confidence,
    'audio_file': f'output/audio/sign_{sign_id:02d}.mp3'
})

# Frontend sẽ load audio
<audio src="/output/audio/sign_34.mp3" controls></audio>
```

---

## 📝 File Structure

```
traffic-sign-recognition/
├── src/
│   └── tts_engine.py              ← Main TTS script
├── output/
│   ├── audio/
│   │   ├── sign_00.mp3            ← Generated files
│   │   ├── sign_01.mp3
│   │   ├── ...
│   │   └── sign_42.mp3
│   └── tts_generation.log         ← Log file
├── guidance_texts_vi.json         ← 43 guidance texts
└── requirements.txt               ← Dependencies
```

---

## 🚀 Next Steps

1. ✅ Cung cấp API Key
2. ✅ Cài đặt dependencies: `pip install -r requirements.txt`
3. ✅ Generate audio: `python src/tts_engine.py`
4. ✅ Verify files: `python src/tts_engine.py verify`
5. ✅ Test nghe audio files
6. ✅ Integrate vào Flask app (auto)

---

## 💡 Tips

- **First run:** Sẽ mất ~1-2 phút để generate tất cả 43 files
- **Be patient:** Polling mỗi 2 giây, lý do là API vclip.io cần thời gian processing
- **Check log:** Nếu có error, luôn xem file `output/tts_generation.log`
- **Retry:** Script có built-in retry logic, không cần manual retry

---

**Author:** AI Assistant  
**Date:** April 17, 2026  
**Status:** Ready for Testing ✅
