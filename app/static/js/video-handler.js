/* ============================================
   VIDEO TAB - Xử lý tải lên & xử lý video
   ============================================ */

let videoPollingInterval;

/**
 * Xử lý tải lên tệp video
 */
async function handleVideoUpload(event) {
    const file = event.target.files[0];
    const progressSection = document.getElementById('progressSection');
    const detectionsContainer = document.getElementById('detectionsContainer');
    const downloadSection = document.getElementById('downloadSection');

    if (!file) return;

    try {
        // Xác thực tệp
        if (file.size > 500 * 1024 * 1024) {
            throw new Error('Tệp video quá lớn (tối đa 500MB)');
        }

        if (!file.type.startsWith('video/')) {
            throw new Error('Định dạng tệp không hợp lệ. Vui lòng chọn tệp video.');
        }

        // Hiển thị trạng thái đang tải
        showLoading(`Đang tải video: ${file.name}`);
        document.getElementById('videoStatus').textContent = '⏳ Đang tải...';
        document.getElementById('videoStatus').style.color = '#f39c12';

        // Tải video
        const result = await uploadFile('/predict-video', event.target);

        if (!result.success) {
            throw new Error(result.error_message || 'Tải lên thất bại');
        }

        // Lưu ID công việc
        appState.videoJobId = result.job_id;

        // Cập nhật UI
        document.getElementById('videoStatus').textContent = '⌛ Đang xử lý...';
        document.getElementById('videoStatus').style.color = '#3498db';
        progressSection.style.display = 'block';
        detectionsContainer.style.display = 'block';
        downloadSection.style.display = 'none';

        console.log(`✅ Video đã tải lên. ID công việc: ${result.job_id}`);

        // Start polling for progress
        pollVideoProgress(result.job_id);

        showSuccess('Video uploaded successfully!');
    } catch (error) {
        showError(error.message);
        document.getElementById('videoStatus').textContent = '❌ Error';
        document.getElementById('videoStatus').style.color = '#e74c3c';
    }
}

/**
 * Poll video processing progress
 */
async function pollVideoProgress(jobId) {
    // Clear any existing interval
    if (videoPollingInterval) {
        clearInterval(videoPollingInterval);
    }

    videoPollingInterval = setInterval(async () => {
        try {
            const status = await apiCall('GET', `/video-status?job_id=${jobId}`);

            // Update progress bar
            document.getElementById('videoProgress').textContent = `${status.progress_percent}%`;
            document.getElementById('progressBar').style.width = `${status.progress_percent}%`;

            // Update progress text
            const progressText = `Xử lý video: Frame ${status.current_frame}/${status.total_frames}`;
            document.getElementById('progressText').textContent = progressText;

            // Update ETA
            const eta = formatTime(status.eta_seconds);
            document.getElementById('etaText').textContent = `Est. ${eta}`;

            // Update detection count
            document.getElementById('videoDetectionCount').textContent = status.detections_count;

            // Check if processing completed
            if (status.status === 'completed') {
                clearInterval(videoPollingInterval);
                document.getElementById('videoStatus').textContent = '✅ Completed';
                document.getElementById('videoStatus').style.color = '#27ae60';
                
                // Fetch and display results
                fetchVideoResults(jobId);
            }

            console.log(`📊 Progress: ${status.progress_percent}% (${status.current_frame}/${status.total_frames})`);
        } catch (error) {
            console.error('❌ Poll error:', error.message);
            clearInterval(videoPollingInterval);
        }
    }, 1000); // Poll every 1 second
}

/**
 * Fetch final video results
 */
async function fetchVideoResults(jobId) {
    try {
        const results = await apiCall('GET', `/video-results?job_id=${jobId}`);

        if (!results.success) {
            throw new Error(results.error_message || 'Failed to fetch results');
        }

        // Display detections table
        displayDetectionsTable(results.detections);

        // Show download button
        document.getElementById('downloadSection').style.display = 'block';
        document.getElementById('downloadBtn').setAttribute('data-url', results.output_video_url);
        document.getElementById('downloadBtn').setAttribute('data-size', 
            Math.round(results.output_video_size_mb * 10) / 10);

        console.log(`✅ Results loaded: ${results.detections.length} detections`);
        showSuccess(`Video processing complete! Found ${results.detections.length} traffic signs.`);
    } catch (error) {
        showError(error.message);
    }
}

/**
 * Display detections in table
 */
function displayDetectionsTable(detections) {
    const tbody = document.getElementById('detectionsBody');

    // Store detections globally for audio playback
    window.currentVideoDetections = detections;

    if (!detections || detections.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #95a5a6;">No detections found</td></tr>';
        return;
    }

    const rows = detections.map((detection, index) => `
        <tr onclick="highlightDetection(${index})">
            <td class="timestamp">${detection.frame_id}</td>
            <td>${detection.frame_timestamp}</td>
            <td class="sign-name">${detection.sign_name_vi}</td>
            <td class="confidence-text">${formatConfidence(detection.confidence)}</td>
            <td style="text-align: center;">
                ${detection.confidence >= 0.8 ? '✓' : '⚠️'}
            </td>
        </tr>
    `).join('');

    tbody.innerHTML = rows;
    console.log(`📊 Table rendered: ${detections.length} rows`);
}

/**
 * Highlight detection in list
 */
function highlightDetection(index) {
    const rows = document.querySelectorAll('#detectionsTable tbody tr');
    rows.forEach((row, i) => {
        row.style.backgroundColor = i === index ? '#e8f5e9' : '';
    });

    // Get the detection data and play audio if available
    const detections = window.currentVideoDetections || [];
    if (detections[index]) {
        const detection = detections[index];
        playDetectionAudio(detection);
    }

    console.log(`🎯 Highlighted detection ${index}`);
}

/**
 * Play audio for a detection
 */
function playDetectionAudio(detection) {
    const audioSection = document.getElementById('videoAudioSection');
    const audioElement = document.getElementById('videoAudio');

    if (!audioSection || !audioElement) {
        console.error('❌ Audio element not found');
        return;
    }

    // Show audio section
    audioSection.style.display = 'block';

    // Set audio source if available
    if (detection.audio_file) {
        const source = audioElement.querySelector('source');
        source.src = detection.audio_file;
        audioElement.load();
        audioElement.play().catch(e => console.log('Audio play blocked:', e));
        console.log(`🔊 Playing audio for: ${detection.sign_name_vi}`);
    } else {
        console.log(`ℹ️ No audio file for: ${detection.sign_name_vi}`);
        audioElement.pause();
    }
}

/**
 * Download processed video
 */
function downloadVideo() {
    const btn = document.getElementById('downloadBtn');
    const url = btn.getAttribute('data-url');
    const size = btn.getAttribute('data-size');

    if (!url) {
        showError('Download URL not available');
        return;
    }

    // Create hidden link and trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = `traffic-sign-detection-${Date.now()}.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    console.log(`⬇️ Downloading video (${size}MB)`);
    showSuccess(`Downloaded: ${size}MB`);
}

// Initialize video handlers on page load
document.addEventListener('DOMContentLoaded', function() {
    const videoInput = document.getElementById('videoInput');
    if (videoInput) {
        videoInput.addEventListener('change', handleVideoUpload);
        console.log('✅ Video handlers initialized');
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (videoPollingInterval) {
        clearInterval(videoPollingInterval);
    }
});
