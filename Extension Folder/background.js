// background.js - Improved version with better timing and error handling

// Add retry mechanism for failed requests
async function fetchWithRetry(url, options, maxRetries = 2) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 8000);
      
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      console.log(`Attempt ${attempt} failed:`, error.message);
      
      if (attempt === maxRetries) {
        throw error;
      }
      
      // Wait before retry (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
    }
  }
}

chrome.webNavigation.onCompleted.addListener(async (details) => {
  const url = details.url;

  // Skip non-http URLs, iframes, and chrome:// pages
  if (!url.startsWith("http") || details.frameId !== 0 || url.startsWith("chrome://")) return;

  try {
    console.log(`🔍 Checking URL: ${url}`);
    
    // First check if backend is available
    let backendAvailable = false;
    try {
      const healthResponse = await fetch("http://localhost:5000/health", {
        method: "GET",
        timeout: 3000,
        mode: 'cors'
      });
      backendAvailable = healthResponse.ok;
    } catch (healthError) {
      console.log("Backend health check failed:", healthError.message);
    }
    
    if (!backendAvailable) {
      console.log("Backend not available, skipping phishing check");
      
      // Show notification that backend is not running
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDgiIGhlaWdodD0iNDgiIHZpZXdCb3g9IjAgMCA0OCA0OCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTI0IDRDMzUuMDQ1NyA0IDQ0IDEyLjk1NDMgNDQgMjRDMjQgMzUuMDQ1NyAxMi45NTQzIDQ0IDI0IDQ0QzM1LjA0NTcgNDQgNDQgMzUuMDQ1NyA0NCAyNEM0NCAxMi45NTQzIDM1LjA0NTcgNCAyNCA0WiIgZmlsbD0iI0Y0NDM2Ii8+CjxwYXRoIGQ9Ik0yNCAyOEMyNS42NTY5IDI4IDI3IDI2LjY1NjkgMjcgMjVDMjcgMjMuMzQzMSAyNS42NTY5IDIyIDI0IDIyQzIyLjM0MzEgMjIgMjEgMjMuMzQzMSAyMSAyNUMyMSAyNi42NTY5IDIyLjM0MzEgMjggMjQgMjhaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4K',
        title: 'Phishing Shield - Backend Offline',
        message: 'Backend server is not running. Phishing protection is disabled. Start the backend server to enable protection.'
      });
      return;
    }
    
    // Backend is available, proceed with phishing check
    let response;
    try {
      response = await fetchWithRetry("http://localhost:5000/check", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({ url }),
        mode: 'cors',
        credentials: 'omit'
      });
    } catch (fetchError) {
      console.error("❌ All fetch attempts failed:", fetchError);
      
      // Show user-friendly error notification
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDgiIGhlaWdodD0iNDgiIHZpZXdCb3g9IjAgMCA0OCA0OCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTI0IDRDMzUuMDQ1NyA0IDQ0IDEyLjk1NDMgNDQgMjRDMjQgMzUuMDQ1NyAxMi45NTQzIDQ0IDI0IDQ0QzM1LjA0NTcgNDQgNDQgMzUuMDQ1NyA0NCAyNEM0NCAxMi45NTQzIDM1LjA0NTcgNCAyNCA0WiIgZmlsbD0iI0Y0NDM2Ii8+CjxwYXRoIGQ9Ik0yNCAyOEMyNS42NTY5IDI4IDI3IDI2LjY1NjkgMjcgMjVDMjcgMjMuMzQzMSAyNS42NTY5IDIyIDI0IDIyQzIyLjM0MzEgMjIgMjEgMjMuMzQzMSAyMSAyNUMyMSAyNi42NTY5IDIyLjM0MzEgMjggMjQgMjhaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4K',
        title: 'Phishing Shield - Connection Error',
        message: 'Failed to connect to backend server. Please check your connection and try again.'
      });
      return;
    }

    if (!response.ok) {
      console.error("Backend error:", response.status);
      // Show error notification to user
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDgiIGhlaWdodD0iNDgiIHZpZXdCb3g9IjAgMCA0OCA0OCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTI0IDRDMzUuMDQ1NyA0IDQ0IDEyLjk1NDMgNDQgMjRDMjQgMzUuMDQ1NyAxMi45NTQzIDQ0IDI0IDQ0QzM1LjA0NTcgNDQgNDQgMzUuMDQ1NyA0NCAyNEM0NCAxMi45NTQzIDM1LjA0NTcgNCAyNCA0WiIgZmlsbD0iI0Y0NDM2Ii8+CjxwYXRoIGQ9Ik0yNCAyOEMyNS42NTY5IDI4IDI3IDI2LjY1NjkgMjcgMjVDMjcgMjMuMzQzMSAyNS42NTY5IDIyIDI0IDIyQzIyLjM0MzEgMjIgMjEgMjMuMzQzMSAyMSAyNUMyMSAyNi42NTY5IDIyLjM0MzEgMjggMjQgMjhaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4K',
        title: 'Phishing Shield Error',
        message: 'Unable to check website. Backend server may be down.'
      });
      return;
    }

    const result = await response.json();
    console.log("✅ Result:", result);

    // Minimal delay to ensure page is ready
    setTimeout(async () => {
      try {
        await chrome.scripting.executeScript({
          target: { tabId: details.tabId },
          func: (data) => {
            // Create and inject the phishing result display
            function showPhishingResult(data) {
              const { status, confidence, isSafe, category, categoryConfidence } = data;

              // Check if already displayed to prevent duplicates
              if (document.querySelector('.phishing-safe-popup') || document.querySelector('.phishing-warning-overlay')) {
                return;
              }

              // Inject styles dynamically
              const styleId = 'phishing-shield-styles';
              if (!document.getElementById(styleId)) {
                const style = document.createElement("style");
                style.id = styleId;
                style.textContent = `
                  .phishing-safe-popup {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: linear-gradient(135deg, #00c853 0%, #00e676 100%);
                    color: white;
                    padding: 18px 24px;
                    border-radius: 16px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    font-size: 14px;
                    z-index: 2147483647;
                    box-shadow: 0 8px 32px rgba(0,200,83,0.4), 0 0 0 1px rgba(255,255,255,0.1);
                    animation: slideInRight 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                    min-width: 300px;
                    max-width: 380px;
                    backdrop-filter: blur(20px);
                    border: 1px solid rgba(255,255,255,0.2);
                  }
                  .phishing-safe-popup .category-badge {
                    display: inline-block;
                    background: rgba(255,255,255,0.25);
                    padding: 6px 12px;
                    border-radius: 8px;
                    margin-top: 8px;
                    font-size: 12px;
                    border: 1px solid rgba(255,255,255,0.3);
                    font-weight: 500;
                  }
                  .phishing-warning-overlay {
                    position: fixed;
                    inset: 0;
                    background: rgba(0,0,0,0.95);
                    z-index: 2147483647;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    animation: fadeIn 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                    backdrop-filter: blur(8px);
                  }
                  .phishing-warning-box {
                    background: linear-gradient(145deg, #ffffff, #f8f9fa);
                    color: #1a1a1a;
                    padding: 32px;
                    border-radius: 20px;
                    text-align: center;
                    max-width: 480px;
                    box-shadow: 0 25px 80px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.1);
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    border: 1px solid rgba(255,255,255,0.2);
                    position: relative;
                    overflow: hidden;
                  }
                  .phishing-warning-box::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 4px;
                    background: linear-gradient(90deg, #ff6b6b, #ffa726, #66bb6a);
                  }
                  .phishing-warning-box h2 { 
                    color: #d32f2f; 
                    margin: 0 0 20px 0;
                    font-size: 28px;
                    font-weight: 700;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
                  }
                  .phishing-warning-box p {
                    margin: 12px 0;
                    color: #555;
                    line-height: 1.6;
                    font-size: 15px;
                  }
                  .phishing-warning-box .category-info {
                    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                    padding: 20px;
                    border-radius: 16px;
                    margin: 24px 0;
                    border: 1px solid #dee2e6;
                    box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
                  }
                  .phishing-warning-box .risk-warning {
                    background: linear-gradient(135deg, #fff3cd, #ffeaa7);
                    border: 2px solid #ffc107;
                    border-radius: 12px;
                    padding: 16px;
                    margin: 20px 0;
                    box-shadow: 0 4px 12px rgba(255, 193, 7, 0.2);
                  }
                  .phishing-warning-box .buttons { 
                    margin-top: 28px; 
                    display: flex; 
                    gap: 16px;
                    justify-content: center;
                    flex-wrap: wrap;
                  }
                  .phishing-warning-box button {
                    padding: 14px 28px;
                    border: none;
                    border-radius: 12px;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 15px;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    min-width: 150px;
                    position: relative;
                    overflow: hidden;
                  }
                  .phishing-warning-box button::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                    transition: left 0.5s;
                  }
                  .phishing-warning-box button:hover::before {
                    left: 100%;
                  }
                  .phishing-warning-box button:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 8px 25px rgba(0,0,0,0.2);
                  }
                  .phishing-warning-box button:active {
                    transform: translateY(-1px);
                  }
                  #phishing-continueBtn { 
                    background: linear-gradient(135deg, #4CAF50, #45a049); 
                    color: white;
                    box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
                  }
                  #phishing-goBackBtn { 
                    background: linear-gradient(135deg, #f44336, #d32f2f); 
                    color: white;
                    box-shadow: 0 4px 15px rgba(244, 67, 54, 0.3);
                  }
                  .countdown-timer {
                    background: linear-gradient(135deg, #ff6b6b, #ff8a80);
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-weight: 600;
                    font-size: 14px;
                    display: inline-block;
                    margin-top: 16px;
                    box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
                    animation: pulse 1s infinite;
                  }
                  @keyframes slideInRight { 
                    from { 
                      opacity: 0; 
                      transform: translateX(120px) scale(0.9); 
                    } 
                    to { 
                      opacity: 1; 
                      transform: translateX(0) scale(1); 
                    } 
                  }
                  @keyframes fadeIn { 
                    from { 
                      opacity: 0; 
                      transform: scale(0.8) translateY(20px); 
                    } 
                    to { 
                      opacity: 1; 
                      transform: scale(1) translateY(0); 
                    } 
                  }
                  @keyframes pulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                  }
                `;
                document.head.appendChild(style);
              }

              if (isSafe) {
                const popup = document.createElement("div");
                popup.className = "phishing-safe-popup";
                
                let categoryDisplay = category || 'General';
                let categoryInfo = '';
                
                if (categoryConfidence > 0) {
                  categoryInfo = `<div class="category-badge">📁 ${categoryDisplay} (${categoryConfidence.toFixed(0)}% confidence)</div>`;
                } else {
                  categoryInfo = `<div class="category-badge">📁 ${categoryDisplay}</div>`;
                }
                
                popup.innerHTML = `
                  <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">✅</span>
                    <div>
                      <strong>${status}</strong>
                      <div style="font-size: 12px; opacity: 0.9;">Confidence: ${confidence.toFixed(1)}%</div>
                    </div>
                  </div>
                  ${categoryInfo}
                  <div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">
                    🛡️ Protected by Phishing Shield
                  </div>
                `;
                document.body.appendChild(popup);
                
                // Auto-remove after 5 seconds
                setTimeout(() => {
                  if (popup.parentNode) {
                    popup.style.animation = 'slideInRight 0.4s ease reverse';
                    setTimeout(() => popup.remove(), 400);
                  }
                }, 5000);
              } else {
                const overlay = document.createElement("div");
                overlay.className = "phishing-warning-overlay";
                
                let categoryDisplay = category || 'Unknown';
                let categoryInfo = '';
                
                if (categoryConfidence > 0) {
                  categoryInfo = `
                    <div class="category-info">
                      <strong>🔍 Detected Category:</strong> ${categoryDisplay}<br>
                      <strong>🤖 ML Confidence:</strong> ${categoryConfidence.toFixed(1)}%
                    </div>
                  `;
                } else {
                  categoryInfo = `
                    <div class="category-info">
                      <strong>📁 Category:</strong> ${categoryDisplay}
                    </div>
                  `;
                }
                
                overlay.innerHTML = `
                  <div class="phishing-warning-box">
                    <h2>⚠️ ${status}</h2>
                    <p style="font-size: 16px; font-weight: 500;">This website may be harmful or suspicious.</p>
                    ${categoryInfo}
                    <div class="risk-warning">
                      <p style="margin: 0; font-size: 14px; color: #856404;"><strong>🚨 Risk Score:</strong> ${(100 - confidence).toFixed(1)}/100</p>
                      <p style="margin: 4px 0 0 0; font-size: 12px; color: #856404;">Proceeding may put your personal information at risk.</p>
                    </div>
                    <div class="buttons">
                      <button id="phishing-goBackBtn">🛡️ Go Back (Safe)</button>
                      <button id="phishing-continueBtn">⚠️ Continue Anyway</button>
                    </div>
                    <div class="countdown-timer" id="countdownTimer">
                      ⏰ Auto-redirect in <span id="countdownNumber">10</span> seconds
                    </div>
                    <div style="font-size: 10px; color: #ccc; margin-top: 8px;">
                      🛡️ Protected by Phishing Shield
                    </div>
                  </div>
                `;
                document.body.appendChild(overlay);

                // Countdown timer functionality
                let countdown = 10;
                const countdownElement = document.getElementById("countdownNumber");
                const countdownInterval = setInterval(() => {
                  countdown--;
                  if (countdownElement) {
                    countdownElement.textContent = countdown;
                  }
                  if (countdown <= 0) {
                    clearInterval(countdownInterval);
                  }
                }, 1000);

                const timer = setTimeout(() => {
                  if (overlay.parentNode) {
                    clearInterval(countdownInterval);
                    window.history.back();
                  }
                }, 10000);

                document.getElementById("phishing-continueBtn").addEventListener("click", () => {
                  clearTimeout(timer);
                  clearInterval(countdownInterval);
                  overlay.remove();
                });
                
                document.getElementById("phishing-goBackBtn").addEventListener("click", () => {
                  clearTimeout(timer);
                  clearInterval(countdownInterval);
                  window.history.back();
                });
              }
            }

            // Execute the display function
            showPhishingResult(data);
          },
          args: [result]
        });
      } catch (scriptError) {
        console.error("Failed to inject script:", scriptError);
      }
    }, 300); // Reduced to 300ms for faster popup

  } catch (err) {
    console.error("❌ Phishing check failed:", err);
    
    // Show error notification for network issues
    if (err.name === 'AbortError') {
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDgiIGhlaWdodD0iNDgiIHZpZXdCb3g9IjAgMCA0OCA0OCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTI0IDRDMzUuMDQ1NyA0IDQ0IDEyLjk1NDMgNDQgMjRDMjQgMzUuMDQ1NyAxMi45NTQzIDQ0IDI0IDQ0QzM1LjA0NTcgNDQgNDQgMzUuMDQ1NyA0NCAyNEM0NCAxMi45NTQzIDM1LjA0NTcgNCAyNCA0WiIgZmlsbD0iI0Y0NDM2Ii8+CjxwYXRoIGQ9Ik0yNCAyOEMyNS42NTY5IDI4IDI3IDI2LjY1NjkgMjcgMjVDMjcgMjMuMzQzMSAyNS42NTY5IDIyIDI0IDIyQzIyLjM0MzEgMjIgMjEgMjMuMzQzMSAyMSAyNUMyMSAyNi42NTY5IDIyLjM0MzEgMjggMjQgMjhaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4K',
        title: 'Phishing Shield Timeout',
        message: 'Website check timed out. Please try again.'
      });
    } else {
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDgiIGhlaWdodD0iNDgiIHZpZXdCb3g9IjAgMCA0OCA0OCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTI0IDRDMzUuMDQ1NyA0IDQ0IDEyLjk1NDMgNDQgMjRDMjQgMzUuMDQ1NyAxMi45NTQzIDQ0IDI0IDQ0QzM1LjA0NTcgNDQgNDQgMzUuMDQ1NyA0NCAyNEM0NCAxMi45NTQzIDM1LjA0NTcgNCAyNCA0WiIgZmlsbD0iI0Y0NDM2Ii8+CjxwYXRoIGQ9Ik0yNCAyOEMyNS42NTY5IDI4IDI3IDI2LjY1NjkgMjcgMjVDMjcgMjMuMzQzMSAyNS42NTY5IDIyIDI0IDIyQzIyLjM0MzEgMjIgMjEgMjMuMzQzMSAyMSAyNUMyMSAyNi42NTY5IDIyLjM0MzEgMjggMjQgMjhaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4K',
        title: 'Phishing Shield Error',
        message: 'Failed to check website. Please ensure backend is running.'
      });
    }
  }
});

// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "checkUrl") {
    fetchWithRetry("http://localhost:5000/check", {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({ url: message.url }),
      mode: 'cors',
      credentials: 'omit'
    })
    .then(res => {
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      return res.json();
    })
    .then(data => sendResponse({ success: true, data }))
    .catch(err => {
      console.error("Message handler fetch error:", err);
      sendResponse({ 
        success: false, 
        error: err.message,
        suggestion: "Please ensure the backend server is running on localhost:5000"
      });
    });
    
    return true; // Keep channel open for async response
  }
  
  if (message.action === "checkBackendHealth") {
    fetchWithRetry("http://localhost:5000/health", {
      method: "GET",
      headers: { "Accept": "application/json" },
      mode: 'cors',
      credentials: 'omit'
    })
    .then(res => {
      if (!res.ok) {
        throw new Error(`Backend health check failed: HTTP ${res.status}`);
      }
      return res.json();
    })
    .then(data => sendResponse({ success: true, data }))
    .catch(err => {
      console.error("Backend health check failed:", err);
      sendResponse({ 
        success: false, 
        error: err.message,
        suggestion: "Backend server is not running. Please start the backend server."
      });
    });
    
    return true; // Keep channel open for async response
  }
});