/* ============================================
   LOGIC CHUYỂN ĐỔI TAB
   ============================================ */

/**
 * Chuyển tab với hoạt ảnh trơn tru
 */
function switchTab(tabName) {
    // Lấy tất cả tab và nút
    const tabs = document.querySelectorAll('.tab-content');
    const buttons = document.querySelectorAll('.tab-btn');

    // Tìm tab mục tiêu
    const targetTab = document.getElementById(tabName);
    const targetButton = Array.from(buttons).find(btn => 
        btn.textContent.toLowerCase().includes(tabName.replace('-tab', ''))
    );

    // Xử lý tab không hợp lệ
    if (!targetTab) {
        console.error(`❌ Không tìm thấy tab: ${tabName}`);
        return;
    }

    // Gỡ bỏ lớp Đang hoạt động khỏi tất cả tab và nút
    tabs.forEach(tab => {
        tab.classList.remove('active');
        // Kích hoạt bất kỳ dọn dẹp nào
        if (tab.id === 'webcam-tab' && appState && appState.webcamActive) {
            // Sẽ được xử lý bởi stopWebcam
        }
    });
    buttons.forEach(btn => btn.classList.remove('active'));

    // Thêm lớp Đang hoạt động vào mục tiêu
    targetTab.classList.add('active');
    if (targetButton) {
        targetButton.classList.add('active');
    }

    // Cập nhật trạng thái ứng dụng
    if (appState) {
        appState.currentTab = tabName;
    }

    // Dừng webcam nếu chuyển đi khỏi tab webcam
    if (tabName !== 'webcam-tab' && appState && appState.webcamActive) {
        stopWebcam();
    }

    console.log(`📑 Tab đã chuyển sang: ${tabName}`);

    // Xuôn lại đặt vị trí nội dung
    document.querySelector('.main-content').scrollTop = 0;
}

// Thêm trình xử lý sự kiện nhấp nút tab
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    
    tabButtons.forEach((button, index) => {
        // Xác định tab nào mà nút này tương ứng với
        const tabNames = ['image-tab', 'video-tab', 'webcam-tab'];
        
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            // Lấy tên tab từ vị trí nút
            const tabName = tabNames[Array.from(tabButtons).indexOf(button)];
            switchTab(tabName);
        });
    });

    console.log('✅ Các nút tab đã được khởi tạo');
});
