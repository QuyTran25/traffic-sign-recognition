"""
Flask application for Traffic Sign Recognition System
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from config import Config
import os

# Initialize Flask app
app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)

# Load configuration
app.config.from_object(Config)

# Enable CORS
CORS(app)

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    """Serve main application page"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Traffic Sign Recognition API',
        'version': '1.0.0'
    }), 200

# ============================================
# API ROUTES (PLACEHOLDER)
# ============================================

@app.route('/api/predict-image', methods=['POST'])
def predict_image():
    """
    Predict traffic sign from uploaded image
    
    Expected: POST request with file field
    Returns: JSON with sign_id, sign_name_vi, confidence, guidance_vi, audio_file
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error_message': 'No file provided'}), 400
        
        # TODO: Implement image prediction
        # 1. Load model from src/model.py
        # 2. Preprocess image
        # 3. Run inference
        # 4. Return results
        
        return jsonify({
            'success': True,
            'message': 'API endpoint placeholder - implement in Sprint 1',
            'sign_id': 0,
            'sign_name_vi': 'Placeholder',
            'confidence': 0.5,
            'guidance_vi': 'This is a placeholder. Implement prediction in Sprint 2.',
            'audio_file': '',
            'processing_time_ms': 0
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error_message': str(e)}), 500

@app.route('/api/predict-video', methods=['POST'])
def predict_video():
    """
    Upload video for processing
    
    Expected: POST request with video file
    Returns: JSON with job_id and processing status
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error_message': 'No file provided'}), 400
        
        # TODO: Implement video upload and job creation
        # 1. Save uploaded video
        # 2. Create processing job
        # 3. Queue for background processing
        # 4. Return job_id for status polling
        
        return jsonify({
            'success': True,
            'job_id': f'video_{os.urandom(8).hex()}',
            'status': 'queued',
            'message': 'Video queued for processing'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error_message': str(e)}), 500

@app.route('/api/video-status', methods=['GET'])
def video_status():
    """
    Poll video processing status
    
    Query: job_id
    Returns: JSON with progress, current_frame, detections_count, eta_seconds
    """
    try:
        job_id = request.args.get('job_id')
        if not job_id:
            return jsonify({'success': False, 'error_message': 'job_id required'}), 400
        
        # TODO: Implement status polling
        # 1. Look up job in database/queue
        # 2. Return current progress
        # 3. When complete, set status='completed'
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': 'processing',
            'progress_percent': 0,
            'current_frame': 0,
            'total_frames': 0,
            'detections_count': 0,
            'eta_seconds': 0
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error_message': str(e)}), 500

@app.route('/api/video-results', methods=['GET'])
def video_results():
    """
    Get video processing results
    
    Query: job_id
    Returns: JSON with detections list and output video URL
    """
    try:
        job_id = request.args.get('job_id')
        if not job_id:
            return jsonify({'success': False, 'error_message': 'job_id required'}), 400
        
        # TODO: Implement results retrieval
        # 1. Look up completed job
        # 2. Return detections from database
        # 3. Provide download URL for processed video
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': 'completed',
            'detections': [],
            'output_video_url': '',
            'processing_time_seconds': 0
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error_message': str(e)}), 500

# WebSocket endpoint for real-time webcam detections
# TODO: Implement with Flask-SocketIO in Sprint 3
# @socketio.on('connect', namespace='/api/webcam-stream')
# def handle_webcam_connect():
#     """Handle WebSocket connection and send real-time detections"""
#     pass

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════╗
    ║  Traffic Sign Recognition System       ║
    ║  Flask Development Server              ║
    ║  http://localhost:5000                 ║
    ╚════════════════════════════════════════╝
    """)
    
    # Run development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
