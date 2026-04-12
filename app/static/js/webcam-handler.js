/* ============================================
   WEBCAM TAB - Xử lý phát hiện thời gian thực
   ============================================ */

let webcamSocket = null;
let webcamFPS = 0;
let frameCount = 0;
let lastFrameTime = Date.now();
let detectionHistory = [];
let audioMuted = false;

/**
 * Bật đầu luồng webcam
 */
async function startWebcam() {
    try {
        showLoading('Bắt đầu webcam...');

        // Yêu cầu truy cập camera
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            },
            audio: false
        });

        appState.webcamStream = stream;
        appState.webcamActive = true;

        // Hiển thị luồng video
        const video = document.getElementById('webcamVideo');
        video.srcObject = stream;
        video.play().catch(e => console.error('Lỗi phát video:', e));

        // Cập nhật UI
        document.getElementById('startWebcamBtn').disabled = true;
        document.getElementById('stopWebcamBtn').disabled = false;
        document.getElementById('cameraStatus').textContent = '🟢 Đang hoạt động';
        document.getElementById('cameraStatus').style.color = '#27ae60';

        // Đặt lại thống kê
        frameCount = 0;
        detectionHistory = [];
        document.getElementById('totalDetections').textContent = '0';
        updateDetectionHistory();

        // Kết nối WebSocket cho phát hiện thời gian thực
        connectWebcamSocket();

        // Start FPS counter
        updateFPS();

        console.log('✅ Webcam started successfully');
        showSuccess('Webcam started!');
    } catch (error) {
        showError(`Webcam access denied: ${error.message}`);
        document.getElementById('cameraStatus').textContent = '🔴 Error';
        document.getElementById('cameraStatus').style.color = '#e74c3c';
        appState.webcamActive = false;
    }
}

/**
 * Stop webcam stream
 */
function stopWebcam() {
    if (appState.webcamStream) {
        appState.webcamStream.getTracks().forEach(track => track.stop());
        appState.webcamStream = null;
    }

    appState.webcamActive = false;

    // Disconnect WebSocket
    if (webcamSocket) {
        webcamSocket.close();
        webcamSocket = null;
    }

    // Update UI
    const video = document.getElementById('webcamVideo');
    video.srcObject = null;

    document.getElementById('startWebcamBtn').disabled = false;
    document.getElementById('stopWebcamBtn').disabled = true;
    document.getElementById('cameraStatus').textContent = '🔴 Inactive';
    document.getElementById('cameraStatus').style.color = '#e74c3c';

    // Clear results
    document.getElementById('webcamResultCard').innerHTML = `
        <h3>🔴 Phát hiện Real-time</h3>
        <div class="empty-state" style="padding: 20px; text-align: center; color: #95a5a6;">
            <p>Webcam đã dừng</p>
        </div>
    `;
    document.getElementById('guidanceBox').style.display = 'none';
    document.getElementById('playAudioBtn').style.display = 'none';

    console.log('✅ Webcam stopped');
    showSuccess('Webcam stopped');
}

/**
 * Connect WebSocket for real-time detections
 */
function connectWebcamSocket() {
    try {
        // Determine WebSocket protocol
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const socketUrl = `${protocol}//${window.location.host}/api/webcam-stream`;

        webcamSocket = new WebSocket(socketUrl);

        webcamSocket.onopen = function(event) {
            console.log('✅ WebSocket connected');
        };

        webcamSocket.onmessage = function(event) {
            try {
                const frame = JSON.parse(event.data);
                handleWebcamFrame(frame);
            } catch (error) {
                console.error('❌ WebSocket parse error:', error);
            }
        };

        webcamSocket.onerror = function(error) {
            console.error('❌ WebSocket error:', error);
            showError('Real-time connection error');
        };

        webcamSocket.onclose = function(event) {
            console.log('⚠️ WebSocket closed');
        };
    } catch (error) {
        console.error('❌ WebSocket connection error:', error.message);
        showError('Could not establish real-time connection');
    }
}

/**
 * Handle incoming webcam frame
 */
function handleWebcamFrame(frame) {
    // Update FPS counter
    frameCount++;

    // Update latency
    if (frame.performance_metrics) {
        document.getElementById('latencyDisplay').textContent = 
            `${frame.performance_metrics.inference_latency_ms}ms`;
    }

    // Check if detection exists
    if (frame.detection_present && frame.current_detection) {
        const detection = frame.current_detection;

        // Update result card
        displayWebcamDetection(detection);

        // Add to history
        addToDetectionHistory(detection);

        // Play audio if not muted
        if (!audioMuted && detection.audio_file) {
            // Uncomment when audio files are ready
            // playDetectionAudio(detection.audio_file);
        }

        // Update total detections count
        document.getElementById('totalDetections').textContent = detectionHistory.length;
    }

    // Update session statistics if available
    if (frame.session_statistics) {
        const stats = frame.session_statistics;
        document.getElementById('fpsDisplay').textContent = 
            Math.round(stats.average_fps || frame.performance_metrics?.fps || 0);
    }
}

/**
 * Display current detection
 */
function displayWebcamDetection(detection) {
    const confidenceClass = getConfidenceClass(detection.confidence);
    const confidencePercent = formatConfidence(detection.confidence);

    const html = `
        <h3>🔴 Phát hiện Real-time</h3>
        <div class="result-item">
            <span class="result-label">Biển báo hiện tại:</span>
            <span class="result-value">${detection.sign_name_vi}</span>
        </div>
        <div class="result-item">
            <span class="result-label">Độ tin cậy:</span>
            <span class="result-value">${confidencePercent}</span>
        </div>
        <div class="confidence-gauge">
            <div class="confidence-bar ${confidenceClass}" style="width: ${detection.confidence * 100}%;"></div>
        </div>
    `;

    document.getElementById('webcamResultCard').innerHTML = html;

    // Update guidance box
    if (detection.guidance_vi) {
        const guidanceBox = document.getElementById('guidanceBox');
        guidanceBox.innerHTML = `<strong>⚡ Hướng dẫn ngay:</strong><br>${detection.guidance_vi}`;
        guidanceBox.style.display = 'block';
    }

    // Show audio button
    if (detection.audio_file) {
        document.getElementById('playAudioBtn').style.display = 'block';
    }
}

/**
 * Add detection to history
 */
function addToDetectionHistory(detection) {
    const now = new Date();
    const timeStr = now.toLocaleTimeString();

    detectionHistory.unshift({
        time: timeStr,
        sign: detection.sign_name_vi,
        confidence: detection.confidence
    });

    // Keep only last 10 detections
    if (detectionHistory.length > 10) {
        detectionHistory.pop();
    }

    updateDetectionHistory();
}

/**
 * Update detection history display
 */
function updateDetectionHistory() {
    const historyDiv = document.getElementById('detectionHistory');

    if (detectionHistory.length === 0) {
        historyDiv.innerHTML = '<div style="color: #95a5a6;">Chưa có phát hiện</div>';
        return;
    }

    const html = detectionHistory.map((det, i) => `
        <div>✓ ${det.time} - ${det.sign} (${formatConfidence(det.confidence)})</div>
    `).join('');

    historyDiv.innerHTML = html;
}

/**
 * Update FPS display
 */
function updateFPS() {
    if (!appState.webcamActive) return;

    const now = Date.now();
    const delta = (now - lastFrameTime) / 1000;

    if (delta >= 1) {
        webcamFPS = Math.round(frameCount / delta);
        document.getElementById('fpsCounter').textContent = webcamFPS;
        document.getElementById('fpsDisplay').textContent = webcamFPS;
        frameCount = 0;
        lastFrameTime = now;
    }

    requestAnimationFrame(updateFPS);
}

/**
 * Play detection audio
 */
function playDetectionAudio(audioFile) {
    const audio = new Audio(audioFile);
    audio.volume = audioMuted ? 0 : 1;
    audio.play().catch(e => console.log('Audio play blocked:', e));
}

/**
 * Toggle audio mute
 */
function toggleMute() {
    audioMuted = !audioMuted;
    const btn = document.getElementById('muteAudioBtn');

    if (audioMuted) {
        btn.innerHTML = '🔊 Unmute';
        btn.classList.remove('btn-secondary');
        btn.classList.add('btn-danger');
    } else {
        btn.innerHTML = '🔇 Mute';
        btn.classList.remove('btn-danger');
        btn.classList.add('btn-secondary');
    }

    console.log(`🔊 Audio muted: ${audioMuted}`);
}

/**
 * Play audio manually
 */
function playAudio() {
    if (detectionHistory.length === 0) {
        showError('No detection available');
        return;
    }

    // In real implementation, would play detection-specific audio
    console.log('🔊 Playing audio...');
    showSuccess('Audio would play here');
}

// Initialize webcam handlers on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Webcam handlers initialized');

    // Ensure cleanup on page navigation
    window.addEventListener('beforeunload', function() {
        if (appState.webcamActive) {
            stopWebcam();
        }
    });
});
