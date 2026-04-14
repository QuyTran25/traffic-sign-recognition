"""
Ứng dụng Flask cho Hệ thống Nhận diện Biển báo Giao thông
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
# CÁC TUYẾN ĐƯỜNG
# ============================================

@app.route('/')
def index():
    """Phục vụ trang ứng dụng chính"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Điểm cuối kiểm tra sức khỏe"""
    return jsonify({
        'status': 'healthy',
        'service': 'API Hệ thống Nhận diện Biển báo Giao thông',
        'version': '1.0.0'
    }), 200

# ============================================
# CÁC TUYẾN ĐỌC API (TRÌNH GIỮ CHỖ)
# ============================================

@app.route('/api/predict-image', methods=['POST'])
def predict_image():
    """
    Dự đoán biển báo giao thông từ ảnh tải lên
    
    Mong đợi: Yêu cầu POST với trường file
    Trả về: JSON với sign_id, sign_name_vi, confidence, guidance_vi, audio_file
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error_message': 'Không có tệp nào được cung cấp'}), 400
        
        # TODO: Triển khai dự đoán ảnh
        # 1. Tải mô hình từ src/model.py
        # 2. Tiền xử lý ảnh
        # 3. Chạy suy luận
        # 4. Trả về kết quả
        
        return jsonify({
            'success': True,
            'message': 'Trình giữ chỗ điểm cuối API - triển khai trong Sprint 1',
            'sign_id': 0,
            'sign_name_vi': 'Trình giữ chỗ',
            'confidence': 0.5,
            'guidance_vi': 'Đây là trình giữ chỗ. Triển khai dự đoán trong Sprint 2.',
            'audio_file': '',
            'processing_time_ms': 0
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error_message': str(e)}), 500

@app.route('/api/predict-video', methods=['POST'])
def predict_video():
    """
    Tải video để xử lý
    
    Mong đợi: Yêu cầu POST với tệp video
    Trả về: JSON với job_id và trạng thái xử lý
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error_message': 'Không có tệp nào được cung cấp'}), 400
        
        # TODO: Triển khai tải video và tạo công việc
        # 1. Lưu video tải lên
        # 2. Tạo công việc xử lý
        # 3. Xếp hàng cho xử lý nền
        # 4. Trả về job_id để thăm dò trạng thái
        
        return jsonify({
            'success': True,
            'job_id': f'video_{os.urandom(8).hex()}',
            'status': 'queued',
            'message': 'Video được xếp hàng để xử lý'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error_message': str(e)}), 500

@app.route('/api/video-status', methods=['GET'])
def video_status():
    """
    Thăm dò trạng thái xử lý video
    
    Truy vấn: job_id
    Trả về: JSON với progress, current_frame, detections_count, eta_seconds
    """
    try:
        job_id = request.args.get('job_id')
        if not job_id:
            return jsonify({'success': False, 'error_message': 'yêu cầu job_id'}), 400
        
        # TODO: Triển khai thăm dò trạng thái
        # 1. Tra cứu công việc trong cơ sở dữ liệu/hàng đợi
        # 2. Trả về tiến độ hiện tại
        # 3. Khi hoàn thành, đặt status='completed'
        
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
    Lấy kết quả xử lý video
    
    Truy vấn: job_id
    Trả về: JSON với danh sách phát hiện và URL video đầu ra
    """
    try:
        job_id = request.args.get('job_id')
        if not job_id:
            return jsonify({'success': False, 'error_message': 'yêu cầu job_id'}), 400
        
        # TODO: Triển khai lấy kết quả
        # 1. Tra cứu công việc đã hoàn thành
        # 2. Trả về phát hiện từ cơ sở dữ liệu
        # 3. Cung cấp URL tải xuống cho video được xử lý
        
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
# CÁC TRÌNH XỬ LÝ LỖI
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Xử lý lỗi 404"""
    return jsonify({'error': 'Không tìm thấy'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Xử lý lỗi 500"""
    return jsonify({'error': 'Lỗi máy chủ nội bộ'}), 500

# ============================================
# CHÍNH
# ============================================

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════╗
    ║  Hệ thống Nhận diện Biển báo           ║
    ║  Máy chủ Phát triển Flask              ║
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
