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
 * Dự đoán ảnh bằng API phía sau
 */
async function predictImage() {
    const imageInput = document.getElementById('imageInput');
    const predictBtn = document.getElementById('predictBtn');
    const imageResults = document.getElementById('imageResults');

    if (!imageInput.files[0]) {
        showError('Vui lòng chọn ảnh trước');
        return;
    }

    try {
        // Vô hiệu hóa nút trong quá trình xử lý
        predictBtn.disabled = true;
        showLoading('Đang dự đoán ảnh...');

        // Tải lên và dự đoán
        const result = await uploadFile('/predict-image', imageInput);

        // Hiển thị kết quả
        displayImageResults(result);
        showSuccess('Dự đoán đã hoàn tất!');
    } catch (error) {
        showError(error.message);
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
                <h3>Prediction Error</h3>
                <p>${result.error_message || 'An error occurred'}</p>
            </div>
        `;
        return;
    }

    // Build confidence gauge HTML
    const confidenceClass = getConfidenceClass(result.confidence);
    const confidencePercent = formatConfidence(result.confidence);

    // Build results HTML
    const resultsHTML = `
        <div class="result-card">
            <h3>Detection Results</h3>
            <div class="result-item">
                <span class="result-label">Traffic Sign:</span>
                <span class="result-value">${result.sign_name_vi}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Confidence:</span>
                <span class="result-value">${confidencePercent}</span>
            </div>
            <div class="confidence-gauge">
                <div class="confidence-bar ${confidenceClass}" style="width: ${result.confidence * 100}%;"></div>
            </div>
        </div>

        <div class="guidance-box">
            <strong>Guidance:</strong><br>
            ${result.guidance_vi}
        </div>

        <div class="audio-section">
            <label>Audio Guidance</label>
            <audio id="imageAudio" class="audio-player" controls preload="auto">
                <source src="${result.audio_file}" type="audio/mpeg">
            </audio>
        </div>
    `;

    imageResults.innerHTML = resultsHTML;

    console.log('✅ Results displayed:', result);
}

// Initialize image handlers on page load
document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.getElementById('imageInput');
    if (imageInput) {
        imageInput.addEventListener('change', previewImage);
        console.log('✅ Image handlers initialized');
    }
});
