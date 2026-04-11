/* ============================================
   TAB SWITCHING LOGIC
   ============================================ */

/**
 * Switch tab with smooth animation
 */
function switchTab(tabName) {
    // Get all tabs and buttons
    const tabs = document.querySelectorAll('.tab-content');
    const buttons = document.querySelectorAll('.tab-btn');

    // Find the target tab
    const targetTab = document.getElementById(tabName);
    const targetButton = Array.from(buttons).find(btn => 
        btn.textContent.toLowerCase().includes(tabName.replace('-tab', ''))
    );

    // Handle invalid tab
    if (!targetTab) {
        console.error(`❌ Tab not found: ${tabName}`);
        return;
    }

    // Remove active class from all tabs and buttons
    tabs.forEach(tab => {
        tab.classList.remove('active');
        // Trigger any cleanup
        if (tab.id === 'webcam-tab' && appState && appState.webcamActive) {
            // Will be handled by stopWebcam
        }
    });
    buttons.forEach(btn => btn.classList.remove('active'));

    // Add active class to target
    targetTab.classList.add('active');
    if (targetButton) {
        targetButton.classList.add('active');
    }

    // Update app state
    if (appState) {
        appState.currentTab = tabName;
    }

    // Stop webcam if switching away from webcam tab
    if (tabName !== 'webcam-tab' && appState && appState.webcamActive) {
        stopWebcam();
    }

    console.log(`📑 Tab switched to: ${tabName}`);

    // Scroll to top of content
    document.querySelector('.main-content').scrollTop = 0;
}

// Add tab button click handlers
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    
    tabButtons.forEach((button, index) => {
        // Determine which tab this button corresponds to
        const tabNames = ['image-tab', 'video-tab', 'webcam-tab'];
        
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            // Get the tab name from button position
            const tabName = tabNames[Array.from(tabButtons).indexOf(button)];
            switchTab(tabName);
        });
    });

    console.log('✅ Tab buttons initialized');
});
