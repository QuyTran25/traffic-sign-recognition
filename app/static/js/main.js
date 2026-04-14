/* ============================================
   MAIN APPLICATION LOGIC
   ============================================ */

// API Base URL
const API_BASE_URL = '/api';

// Global State
let appState = {
    currentTab: 'image-tab',
    webcamActive: false,
    webcamStream: null,
    videoJobId: null,
    lastInteractionTime: Date.now()
};

/**
 * Tắm dừng tab
 */
function switchTab(tabName) {
    // Ẩn tất cả tab
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));

    // Gỡ bỏ lớp Đang hoạt động khỏi tất cả các nút
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));

    // Hiền thị tab được chọn
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Thêm lớp Đang hoạt động vào nút được nhấp
    event.target.classList.add('active');

    // Cập nhật trạng thái
    appState.currentTab = tabName;

    // Dọn dẹp dựa trên thay đổi tab
    if (tabName !== 'webcam-tab' && appState.webcamActive) {
        stopWebcam();
    }

    console.log(`🗒 Đã chuyển sang tab: ${tabName}`);
}

/**
 * Định dạng thời gian kéo dài
 */
function formatTime(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hrs > 0) {
        return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Định dạng độ tin cậy dưới dạng phần trăm
 */
function formatConfidence(confidence) {
    return (confidence * 100).toFixed(1) + '%';
}

/**
 * Hiền thị chỉ báo tải
 */
function showLoading(message = 'Tải...'){
    console.log(`⏳ ${message}`);
}

/**
 * Hiền thị thông báo lỗi
 */
function showError(message) {
    console.error(`❌ Lỗi: ${message}`);
    alert('Lỗi: ' + message);
}

/**
 * Hiền thị thông báo thành công
 */
function showSuccess(message) {
    console.log(`✅ ${message}`);
}

/**
 * Determine confidence color
 */
function getConfidenceColor(confidence) {
    if (confidence >= 0.9) return '#27ae60';      // Green
    if (confidence >= 0.6) return '#f39c12';      // Orange
    return '#e74c3c';                              // Red
}

/**
 * Get confidence CSS class
 */
function getConfidenceClass(confidence) {
    if (confidence >= 0.9) return 'confidence-high';
    if (confidence >= 0.6) return 'confidence-medium';
    return 'confidence-low';
}

// Initialize app on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Traffic Sign Recognition System initialized');
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Ctrl+1: Switch to Image tab
        if (event.ctrlKey && event.key === '1') {
            switchTab('image-tab');
        }
        // Ctrl+2: Switch to Video tab
        if (event.ctrlKey && event.key === '2') {
            switchTab('video-tab');
        }
        // Ctrl+3: Switch to Webcam tab
        if (event.ctrlKey && event.key === '3') {
            switchTab('webcam-tab');
        }
    });
    
    console.log('💡 Keyboard shortcuts enabled: Ctrl+1/2/3 to switch tabs');
});

// Unload handler - cleanup webcam
window.addEventListener('beforeunload', function() {
    if (appState.webcamActive) {
        stopWebcam();
    }
});
