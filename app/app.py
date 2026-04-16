"""
Ứng dụng Flask cho Hệ thống Nhận diện Biển báo Giao thông
"""

import io
from PIL import Image
import torch
import torchvision.transforms as transforms
from torchvision import models
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
# ============================================
# KHỞI TẠO MÔ HÌNH AI (PYTORCH)
# ============================================
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
NUM_CLASSES = 43 # SỬA THÀNH 43 Ở ĐÂY

# Xây dựng lại cấu trúc mạng MobileNetV2
model = models.mobilenet_v2(weights=None)
model.classifier[1] = torch.nn.Linear(model.last_channel, NUM_CLASSES)

# Tải trọng số từ file model.pth
model_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'model.pth')
model.load_state_dict(torch.load(model_path, map_location=device))
model.eval() # Chuyển sang chế độ test

# Phép biến đổi ảnh
transform = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# Từ điển 43 loại biển báo (chuẩn GTSRB)
SIGN_NAMES = {
    0: 'Giới hạn tốc độ (20km/h)', 1: 'Giới hạn tốc độ (30km/h)', 2: 'Giới hạn tốc độ (50km/h)',
    3: 'Giới hạn tốc độ (60km/h)', 4: 'Giới hạn tốc độ (70km/h)', 5: 'Giới hạn tốc độ (80km/h)',
    6: 'Hết giới hạn tốc độ (80km/h)', 7: 'Giới hạn tốc độ (100km/h)', 8: 'Giới hạn tốc độ (120km/h)',
    9: 'Cấm vượt', 10: 'Cấm xe tải vượt', 11: 'Giao nhau với đường không ưu tiên',
    12: 'Đường ưu tiên', 13: 'Nhường đường', 14: 'Dừng lại (STOP)',
    15: 'Cấm mọi phương tiện', 16: 'Cấm xe tải', 17: 'Cấm đi ngược chiều',
    18: 'Nguy hiểm khác', 19: 'Đường cong vòng sang trái', 20: 'Đường cong vòng sang phải',
    21: 'Nhiều khúc cua liên tiếp', 22: 'Đường gồ ghề', 23: 'Đường trơn trượt',
    24: 'Đường hẹp bên phải', 25: 'Công trường', 26: 'Có tín hiệu đèn giao thông',
    27: 'Người đi bộ cắt ngang', 28: 'Trẻ em cắt ngang', 29: 'Người đi xe đạp cắt ngang',
    30: 'Cảnh báo băng tuyết', 31: 'Thú rừng vượt qua đường', 32: 'Hết mọi lệnh cấm/giới hạn',
    33: 'Chỉ được rẽ phải', 34: 'Chỉ được rẽ trái', 35: 'Chỉ được đi thẳng',
    36: 'Chỉ được đi thẳng hoặc rẽ phải', 37: 'Chỉ được đi thẳng hoặc rẽ trái',
    38: 'Đi vòng sang phải', 39: 'Đi vòng sang trái', 40: 'Vòng xuyến',
    41: 'Hết cấm vượt', 42: 'Hết cấm xe tải vượt'
}
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
    Dự đoán biển báo giao thông từ ảnh tải lên (Đã kết nối AI thật)
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error_message': 'Không có tệp nào được cung cấp'}), 400
        
        file = request.files['file']
        
        # 1. Đọc ảnh từ file tải lên
        image_bytes = file.read()
        image = Image.open(file).convert('RGB')
        
        # 2. Tiền xử lý ảnh (chuyển thành tensor)
        tensor = transform(image).unsqueeze(0).to(device)
        
        # 3. Chạy AI suy luận
        with torch.no_grad():
            outputs = model(tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, predicted = torch.max(probabilities, 0)
        
        class_id = predicted.item() # Ví dụ AI trả ra số 34
        
        # --- BƯỚC GIẢI MÃ: CHUYỂN VỊ TRÍ ABC VỀ ID THẬT ---
        # Đây là thứ tự chính xác 100% mà PyTorch đã đọc các thư mục
        PYTORCH_CLASSES = [
            0, 1, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 
            2, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 
            3, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 
            4, 40, 41, 42, 5, 6, 7, 8, 9
        ]
        
        # Lấy ID thư mục thực tế
        real_class_id = PYTORCH_CLASSES[class_id]
        
        # 4. Lấy tên biển báo theo ID thật (real_class_id)
        sign_name = SIGN_NAMES.get(real_class_id, f"Biển báo ID: {real_class_id}")
        
        return jsonify({
            'success': True,
            'message': 'Dự đoán thành công',
            'sign_id': class_id,
            'sign_name_vi': sign_name,
            'confidence': float(confidence.item()),
            'guidance_vi': f'AI nhận diện đây là {sign_name}. Hãy tuân thủ luật giao thông nhé!',
            'audio_file': ''
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
