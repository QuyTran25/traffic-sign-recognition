/* ============================================
   IMAGE TAB - Xử lý tải lên & dự đoán ảnh
   ============================================ */

/**
 * Xem trước ảnh tải lên
 */
function previewImage(event) {
    const file = event.target.files[0];
    const imageDisplay = document.getElementById('imageDisplay');
    const uploadedImage = document.getElementById('uploadedImage');
    const predictBtn = document.getElementById('predictBtn');
    const emptyImageState = document.getElementById('emptyImageState');

    if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();

        reader.onload = function(e) {
            uploadedImage.src = e.target.result;
            uploadedImage.style.display = 'block';
            emptyImageState.style.display = 'none';
            predictBtn.disabled = false;
            console.log(`📷 Đã tải trước ảnh: ${file.name}`);
        };

        reader.readAsDataURL(file);
    } else {
        showError('Định dạng tệp không hợp lệ. Vui lòng chọn ảnh JPG hoặc PNG.');
        clearImage();
    }
}

/**
 * Xóa ảnh tải lên
 */
function clearImage() {
    const imageInput = document.getElementById('imageInput');
    const imageDisplay = document.getElementById('imageDisplay');
    const uploadedImage = document.getElementById('uploadedImage');
    const predictBtn = document.getElementById('predictBtn');
    const emptyImageState = document.getElementById('emptyImageState');
    const imageResults = document.getElementById('imageResults');

    imageInput.value = '';
    uploadedImage.src = '';
    uploadedImage.style.display = 'none';
    emptyImageState.style.display = 'block';
    predictBtn.disabled = true;
    imageResults.innerHTML = '<div class="empty-state" style="text-align: center; padding: 40px; color: #95a5a6;"><p>Kết quả sẽ hiển thị ở đây</p></div>';

    console.log('🗑️ Đã xóa ảnh');
}

/**
 * Dự đoán ảnh bằng API phía sau (Đã chỉnh sửa để hoạt động độc lập)
 */
async function predictImage() {
    const imageInput = document.getElementById('imageInput');
    const predictBtn = document.getElementById('predictBtn');
    const imageResults = document.getElementById('imageResults');

    // Khai báo biến file rõ ràng ngay từ đầu
    const file = imageInput.files[0]; 

    if (!file) {
        alert('Vui lòng chọn ảnh trước');
        return;
    }

    try {
        // Vô hiệu hóa nút trong quá trình xử lý để tránh spam click
        predictBtn.disabled = true;
        imageResults.innerHTML = '<div style="text-align: center; padding: 20px;">Đang dự đoán ảnh... ⏳</div>';

        // 1. Tạo đối tượng FormData để chứa ảnh
        const formData = new FormData();
        formData.append("file", file); // Sử dụng đúng biến file đã khai báo ở trên

        // 2. Gửi ảnh trực tiếp đến Flask
        const response = await fetch('/api/predict-image', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Lỗi máy chủ: ${response.status}`);
        }

        const result = await response.json();

        // 3. Hiển thị kết quả
        displayImageResults(result);

    } catch (error) {
        console.error("Lỗi khi dự đoán:", error);
        imageResults.innerHTML = `
            <div class="result-card" style="color: red; border: 1px solid red; padding: 15px;">
                <h3>Lỗi xử lý</h3>
                <p>${error.message || 'Không thể kết nối đến máy chủ. Vui lòng thử lại.'}</p>
            </div>`;
    } finally {
        predictBtn.disabled = false;
    }
}

/**
 * Display image prediction results
 */
function displayImageResults(result) {
    const imageResults = document.getElementById('imageResults');

    if (!result.success) {
        imageResults.innerHTML = `
            <div class="result-card">
                <h3>Lỗi Dự đoán</h3>
                <p>${result.error_message || 'Có lỗi xảy ra'}</p>
            </div>
        `;
        return;
    }

    // Get detections array
    const detections = result.detections || [];
    
    if (detections.length === 0) {
        imageResults.innerHTML = `
            <div class="result-card">
                <h3>Không Phát Hiện</h3>
                <p>Không tìm thấy biển báo nào trong ảnh</p>
            </div>
        `;
        return;
    }

    // Build results HTML for each detection
    let resultsHTML = `
        <div class="result-card">
            <h3>Kết quả Phát hiện (${detections.length} biển báo)</h3>
            <div class="detections-list">
    `;

    detections.forEach((det, index) => {
        const classifierConf = det.classifier_confidence || 0;
        const detectorConf = det.detector_confidence || 0;
        const confidencePercent = (classifierConf * 100).toFixed(1);
        const confidenceClass = classifierConf > 0.7 ? 'high' : classifierConf > 0.5 ? 'medium' : 'low';
        const audioFile = det.audio_file || '';
        
        // Build audio player HTML if audio exists
        let audioHTML = '';
        if (audioFile) {
            audioHTML = `
                <div class="result-item" style="margin-top: 10px;">
                    <span class="result-label">🔊 Âm thanh:</span>
                    <audio style="width: 100%; height: 30px;" controls>
                        <source src="/api/audio/${audioFile}" type="audio/mpeg">
                        Trình duyệt không hỗ trợ phát audio
                    </audio>
                </div>
            `;
        }

        resultsHTML += `
            <div class="detection-item" style="border-bottom: 1px solid #eee; padding: 15px 0; margin-bottom: 15px;">
                <div class="result-item">
                    <span class="result-label">Biển báo ${index + 1}:</span>
                    <span class="result-value">${det.sign_name || 'Unknown'}</span>
                </div>
                <div class="result-item">
                    <span class="result-label">ID:</span>
                    <span class="result-value">${det.sign_id}</span>
                </div>
                <div class="result-item">
                    <span class="result-label">Độ tin cây (Classifier):</span>
                    <span class="result-value">${confidencePercent}%</span>
                </div>
                <div class="confidence-gauge">
                    <div class="confidence-bar ${confidenceClass}" style="width: ${classifierConf * 100}%;"></div>
                </div>
                <div class="result-item">
                    <span class="result-label">Độ tin cây (Detector):</span>
                    <span class="result-value">${(detectorConf * 100).toFixed(1)}%</span>
                </div>
                <div class="result-item">
                    <span class="result-label">Vị trí BBox:</span>
                    <span class="result-value">${JSON.stringify(det.bbox)}</span>
                </div>
                ${audioHTML}
            </div>
        `;
    });

    resultsHTML += `
            </div>
        </div>

        <div class="guidance-box" style="margin-top: 20px;">
            <strong>Hướng dẫn an toàn:</strong><br>
            <p>${detections[0].guidance || 'Không có hướng dẫn'}</p>
            ${detections[0].audio_file ? `
            <div style="margin-top: 15px;">
                <strong>🔊 Nghe hướng dẫn:</strong><br>
                <audio style="width: 100%; height: 35px; margin-top: 10px;" controls autoplay>
                    <source src="/api/audio/${detections[0].audio_file}" type="audio/mpeg">
                    Trình duyệt không hỗ trợ phát audio
                </audio>
            </div>
            ` : ''}
        </div>
    `;

    imageResults.innerHTML = resultsHTML;

    console.log('✅ Kết quả được hiển thị:', result);
}

// Initialize image handlers on page load
document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.getElementById('imageInput');
    if (imageInput) {
        imageInput.addEventListener('change', previewImage);
        console.log('✅ Image handlers initialized');
    }
});
