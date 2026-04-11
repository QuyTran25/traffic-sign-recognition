/* ============================================
   API CLIENT - Handle backend communications
   ============================================ */

/**
 * Make API call with error handling
 */
async function apiCall(method, endpoint, data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.error_message || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`❌ API Error [${method} ${endpoint}]:`, error.message);
        throw error;
    }
}

/**
 * Upload file to API
 */
async function uploadFile(endpoint, fileInput) {
    try {
        const file = fileInput.files[0];
        if (!file) {
            throw new Error('No file selected');
        }

        // Validate file size (10MB for images, 500MB for videos)
        const maxSize = endpoint.includes('video') ? 500 * 1024 * 1024 : 10 * 1024 * 1024;
        if (file.size > maxSize) {
            throw new Error(`File too large. Maximum size: ${Math.round(maxSize / 1024 / 1024)}MB`);
        }

        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.error_message || `HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`❌ Upload Error [${endpoint}]:`, error.message);
        throw error;
    }
}

/**
 * Poll API for status updates
 */
async function pollStatus(endpoint, interval = 1000, maxAttempts = 300) {
    let attempts = 0;
    
    return new Promise((resolve, reject) => {
        const poll = async () => {
            try {
                const response = await apiCall('GET', endpoint);
                
                if (response.status === 'completed' || response.status === 'success') {
                    resolve(response);
                } else if (attempts >= maxAttempts) {
                    reject(new Error('Poll timeout exceeded'));
                } else {
                    attempts++;
                    setTimeout(poll, interval);
                }
            } catch (error) {
                reject(error);
            }
        };
        
        poll();
    });
}

/**
 * Get mock data (for testing without backend)
 */
function getMockData(type) {
    const mockData = {
        image: {
            success: true,
            sign_id: 0,
            sign_name_vi: "Giới hạn tốc độ 30 km/h",
            sign_name_en: "Speed Limit 30 km/h",
            confidence: 0.985,
            guidance_vi: "Vui lòng giảm tốc độ xuống 30 km/h để đảm bảo an toàn. Đây là khu vực có lưu lượng giao thông cao hoặc gần trường học.",
            audio_file: "/static/audio/mock_audio.wav",
            bbox: { x: 45, y: 30, width: 120, height: 135 },
            processing_time_ms: 145
        },
        video: {
            success: true,
            job_id: "video_001_202604111425",
            status: "completed",
            total_frames: 200,
            fps: 30,
            detections: [
                {
                    detection_id: 1,
                    frame_id: 10,
                    frame_timestamp: "00:00.33s",
                    sign_id: 0,
                    sign_name_vi: "Giới hạn tốc độ 30 km/h",
                    confidence: 0.985
                },
                {
                    detection_id: 2,
                    frame_id: 45,
                    frame_timestamp: "01:30.00s",
                    sign_id: 14,
                    sign_name_vi: "Stop - Dừng lại",
                    confidence: 0.872
                },
                {
                    detection_id: 3,
                    frame_id: 78,
                    frame_timestamp: "02:36.00s",
                    sign_id: 25,
                    sign_name_vi: "Cảnh báo: Công trường",
                    confidence: 0.921
                }
            ]
        },
        webcam: {
            timestamp: new Date().toISOString(),
            detection_present: true,
            current_detection: {
                sign_id: 1,
                sign_name_vi: "Giới hạn tốc độ 50 km/h",
                confidence: 0.942,
                guidance_vi: "Giới hạn tốc độ 50 km/h - Khu vực gần trung tâm thành phố"
            },
            performance_metrics: {
                fps: 24,
                inference_latency_ms: 120
            }
        }
    };

    return mockData[type] || null;
}

// Initialize API client
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ API Client initialized');
    console.log(`📡 API Base URL: ${API_BASE_URL}`);
});
