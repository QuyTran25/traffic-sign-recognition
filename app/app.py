"""
Flask API cho Traffic Sign Recognition System
Integrate Detection + Classification + Audio
"""

import io
import json
import os
from pathlib import Path
from typing import Dict, Tuple

import cv2
import numpy as np
from PIL import Image
import torch
import torchvision.transforms as transforms
from torchvision import models

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from config import Config

# Thêm src directory vào path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from classical_detector import detect_classical, load_params
except ImportError:
    print("⚠ classical_detector not available")
    detect_classical = None
    load_params = None

try:
    from tts_engine import generate_audio_file
except ImportError:
    print("⚠ tts_engine not available")
    generate_audio_file = None

# ============================================
# Configuration
# ============================================
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
AUDIO_DIR = OUTPUT_DIR / "audio"

MODEL_PATH = OUTPUT_DIR / "model.pth"
DETECTOR_CONFIG_PATH = BASE_DIR / "configs" / "classical_detector.json"
SIGN_LABELS_FILE = BASE_DIR / "sign_labels_vi.json"
GUIDANCE_TEXTS_FILE = BASE_DIR / "guidance_texts_vi.json"

NUM_CLASSES = 43
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Initialize Flask app
app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)

# Load configuration
app.config.from_object(Config)
CORS(app)

print(f"Device: {DEVICE}")

# ============================================
# Load Labels & Guidance
# ============================================
try:
    with open(SIGN_LABELS_FILE, 'r', encoding='utf-8') as f:
        SIGN_LABELS = json.load(f)
    print(f"✓ Loaded {len(SIGN_LABELS)} sign labels")
except Exception as e:
    print(f"⚠ Failed to load sign labels: {e}")
    SIGN_LABELS = {str(i): f"Sign {i}" for i in range(43)}

try:
    with open(GUIDANCE_TEXTS_FILE, 'r', encoding='utf-8') as f:
        GUIDANCE_TEXTS = json.load(f)
    print(f"✓ Loaded guidance texts")
except Exception as e:
    print(f"⚠ Failed to load guidance texts: {e}")
    GUIDANCE_TEXTS = {str(i): f"Hãy tuân thủ biển báo {i}" for i in range(43)}

# ============================================
# Load Classifier Model
# ============================================
print("\n🔧 Loading Classifier Model...")
classifier = None
try:
    if os.path.exists(MODEL_PATH):
        classifier = models.mobilenet_v2(weights=None)
        classifier.classifier[1] = torch.nn.Linear(classifier.last_channel, NUM_CLASSES)
        classifier.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
        classifier.eval()
        classifier = classifier.to(DEVICE)
        print(f"✓ Classifier loaded from {MODEL_PATH}")
    else:
        print(f"⚠ Model file not found: {MODEL_PATH}")
        print(f"   Run: python prepare_classification_data.py && python src/train.py")
except Exception as e:
    print(f"⚠ Failed to load classifier: {e}")

# ============================================
# Load Detector
# ============================================
print("\n🔧 Loading Detector...")
detector_params = None
try:
    if load_params and os.path.exists(DETECTOR_CONFIG_PATH):
        detector_params = load_params(DETECTOR_CONFIG_PATH)
        print(f"✓ Detector config loaded")
    else:
        print(f"⚠ Detector config not found: {DETECTOR_CONFIG_PATH}")
except Exception as e:
    print(f"⚠ Failed to load detector: {e}")

# ============================================
# Image Transform for Classifier
# ============================================
classifier_transform = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ============================================
# Helper Functions
# ============================================

def classify_crop(crop_pil: Image.Image) -> Tuple[int, float]:
    """
    Classify a single traffic sign crop
    Returns: (class_id, confidence)
    """
    if classifier is None:
        return -1, 0.0
    
    try:
        tensor = classifier_transform(crop_pil).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            outputs = classifier(tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, predicted = torch.max(probabilities, 0)
        
        class_id = int(predicted.item())
        confidence_score = float(confidence.item())
        
        return class_id, confidence_score
    except Exception as e:
        print(f"Classification error: {e}")
        return -1, 0.0

def get_sign_info(class_id: int) -> Dict[str, str]:
    """Get sign name and guidance text"""
    sign_id_str = str(class_id)
    
    sign_name = SIGN_LABELS.get(sign_id_str, f"Biển báo {class_id}")
    guidance = GUIDANCE_TEXTS.get(sign_id_str, f"Hãy tuân thủ quy định biển báo {class_id}")
    
    return {
        "sign_name": sign_name,
        "guidance": guidance
    }

def generate_audio(text: str, class_id: int) -> str:
    """
    Get audio file for traffic sign guidance
    First tries pre-recorded audio, then TTS, then returns empty
    Returns: audio filename (or empty string if not available)
    """
    try:
        # Step 1: Check if pre-recorded audio exists
        prerecorded_audio = AUDIO_DIR / f"sign_{class_id:02d}.mp3"
        if prerecorded_audio.exists():
            print(f"✓ Using pre-recorded audio: sign_{class_id:02d}.mp3")
            return f"sign_{class_id:02d}.mp3"
        
        # Step 2: Try TTS generation as fallback
        if generate_audio_file is not None:
            audio_file = generate_audio_file(text, output_dir=str(AUDIO_DIR))
            if audio_file:
                print(f"✓ Generated TTS audio: {audio_file}")
                return audio_file
        
        # Step 3: No audio available
        print(f"⚠ No audio available for sign {class_id}")
        return ""
    
    except Exception as e:
        print(f"⚠ Audio retrieval failed: {e}")
        return ""


# ============================================
# Routes
# ============================================

@app.route('/')
def index():
    """Serve main application"""
    return render_template('index.html')

@app.route('/test')
def test_api():
    """Serve API test page"""
    return render_template('test_api.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    classifier_ready = classifier is not None
    detector_ready = detector_params is not None
    
    return jsonify({
        'status': 'healthy' if classifier_ready else 'degraded',
        'service': 'Traffic Sign Recognition API',
        'version': '2.0.0',
        'components': {
            'classifier': 'ready' if classifier_ready else 'not_ready',
            'detector': 'ready' if detector_ready else 'not_ready'
        }
    }), 200

@app.route('/api/predict-image', methods=['POST'])
def predict_image():
    """
    Predict traffic signs in an image
    
    Request:
    - file: image file (POST multipart)
    
    Response:
    {
        "success": bool,
        "image_size": [width, height],
        "detections": [
            {
                "bbox": [x1, y1, x2, y2],
                "confidence": float,
                "sign_id": int,
                "sign_name": str,
                "guidance": str,
                "audio_file": str
            }
        ],
        "error_message": str (if failed)
    }
    """
    try:
        # Validate input
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error_message': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error_message': 'Empty file'
            }), 400
        
        # Read image
        image_bytes = file.read()
        image_pil = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        image_cv = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
        
        h, w = image_cv.shape[:2]
        
        detections = []
        
        # Step 1: Detect traffic signs in image
        if detector_params is not None and detect_classical is not None:
            try:
                detector_output = detect_classical(
                    np.array(image_pil),  # RGB format
                    params=detector_params,
                    return_debug=False
                )
                bboxes = detector_output.get('bboxes', [])
                scores = detector_output.get('scores', [])
            except Exception as e:
                print(f"Detection error: {e}")
                bboxes = []
                scores = []
        else:
            bboxes = []
            scores = []
        
        # Step 2: Classify each detected region
        for bbox, score in zip(bboxes, scores):
            try:
                x1, y1, x2, y2 = bbox
                
                # Extract crop
                crop_cv = image_cv[y1:y2, x1:x2]
                crop_pil = Image.fromarray(cv2.cvtColor(crop_cv, cv2.COLOR_BGR2RGB))
                
                # Classify
                class_id, confidence = classify_crop(crop_pil)
                
                # Get sign info
                sign_info = get_sign_info(class_id)
                
                # Generate audio
                audio_file = generate_audio(sign_info['guidance'], class_id)
                
                detection = {
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "detector_confidence": float(score),
                    "classifier_confidence": float(confidence),
                    "sign_id": int(class_id),
                    "sign_name": sign_info['sign_name'],
                    "guidance": sign_info['guidance'],
                    "audio_file": audio_file
                }
                detections.append(detection)
            except Exception as e:
                print(f"Crop processing error: {e}")
                continue
        
        return jsonify({
            'success': True,
            'image_size': [w, h],
            'detections': detections,
            'detection_count': len(detections)
        }), 200
    
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({
            'success': False,
            'error_message': str(e)
        }), 500

@app.route('/api/predict-crop', methods=['POST'])
def predict_crop():
    """
    Direct classification of a traffic sign crop
    (Useful for testing classifier alone)
    
    Request:
    - file: cropped sign image
    
    Response:
    {
        "success": bool,
        "sign_id": int,
        "sign_name": str,
        "confidence": float,
        "guidance": str,
        "audio_file": str
    }
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error_message': 'No file'}), 400
        
        file = request.files['file']
        image_pil = Image.open(io.BytesIO(file.read())).convert('RGB')
        
        # Classify
        class_id, confidence = classify_crop(image_pil)
        
        if class_id == -1:
            return jsonify({
                'success': False,
                'error_message': 'Classification failed'
            }), 500
        
        # Get info
        sign_info = get_sign_info(class_id)
        audio_file = generate_audio(sign_info['guidance'], class_id)
        
        return jsonify({
            'success': True,
            'sign_id': class_id,
            'sign_name': sign_info['sign_name'],
            'confidence': confidence,
            'guidance': sign_info['guidance'],
            'audio_file': audio_file
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error_message': str(e)
        }), 500

@app.route('/api/audio/<filename>', methods=['GET'])
def get_audio(filename):
    """Download audio file (MP3 or WAV)"""
    try:
        audio_path = AUDIO_DIR / filename
        if not audio_path.exists():
            return jsonify({'error': 'Audio file not found'}), 404
        
        # Determine MIME type based on file extension
        mime_type = 'audio/mpeg' if filename.endswith('.mp3') else 'audio/wav'
        
        return send_file(
            str(audio_path),
            mimetype=mime_type,
            as_attachment=False,  # Inline playback, not download
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# Error Handlers
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 error"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 error"""
    return jsonify({'error': 'Internal server error'}), 500

# ============================================
# Main
# ============================================

if __name__ == '__main__':
    print(f"""
    ╔═══════════════════════════════════════╗
    ║  Traffic Sign Recognition API v2.0    ║
    ║  http://localhost:5000                ║
    ╚═══════════════════════════════════════╝
    
    Components:
    - Detector: {'✓' if detector_params else '✗'}
    - Classifier: {'✓' if classifier else '✗'}
    - Audio: ✓ (with TTS API key)
    """)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
