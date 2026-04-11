/* ============================================
   IMAGE TAB - Handle image upload & prediction
   ============================================ */

/**
 * Preview uploaded image
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
            console.log(`📷 Image preview loaded: ${file.name}`);
        };

        reader.readAsDataURL(file);
    } else {
        showError('Invalid file format. Please select a JPG or PNG image.');
        clearImage();
    }
}

/**
 * Clear uploaded image
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

    console.log('🗑️ Image cleared');
}

/**
 * Predict image using backend API
 */
async function predictImage() {
    const imageInput = document.getElementById('imageInput');
    const predictBtn = document.getElementById('predictBtn');
    const imageResults = document.getElementById('imageResults');

    if (!imageInput.files[0]) {
        showError('Please select an image first');
        return;
    }

    try {
        // Disable button during processing
        predictBtn.disabled = true;
        showLoading('Predicting image...');

        // Upload and predict
        const result = await uploadFile('/predict-image', imageInput);

        // Display results
        displayImageResults(result);
        showSuccess('Prediction completed!');
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
