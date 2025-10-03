// Global fallback whitelist (for when backend is down)
const SAFE_WEBSITES = [
    'google.com', 'github.com', 'stackoverflow.com', 'wikipedia.org',
    'microsoft.com', 'apple.com', 'youtube.com', 'facebook.com',
    'instagram.com', 'twitter.com', 'linkedin.com', 'reddit.com',
    'amazon.com', 'netflix.com', 'spotify.com'
];

// Track which tabs we're currently checking to avoid duplicates
const checkingTabs = new Set();

// Listen when user navigates to any website
chrome.webNavigation.onBeforeNavigate.addListener((details) => {
    // Only check main frame (not iframes)
    if (details.frameId === 0) {
        checkUrlSafety(details.url, details.tabId);
    }
});

// Function to check if URL is safe (reusable, now with ML backend)
async function checkIfUrlIsSafe(url) {
    try {
        const response = await fetch('http://localhost:5000/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        const result = await response.json();
        console.log(`Backend ML Check: ${url} - Confidence: ${result.confidence}`);
        return { isSafe: result.isSafe, confidence: result.confidence };
    } catch (error) {
        console.error('Backend check failed—using whitelist fallback');
        // Fallback to old whitelist
        try {
            const urlObj = new URL(url);
            const hostname = urlObj.hostname;
            const isSafe = SAFE_WEBSITES.some(safeSite => 
                hostname.includes(safeSite) || hostname.endsWith('.' + safeSite)
            );
            return { isSafe: isSafe, confidence: 1.0 };  // Full confidence on fallback
        } catch (parseError) {
            console.error('URL parse failed—default unsafe');
            return { isSafe: false, confidence: 0.0 };
        }
    }
}

// Function to check URL safety on navigation
function checkUrlSafety(url, tabId) {
    // Avoid checking the same tab multiple times
    if (checkingTabs.has(tabId)) return;
    checkingTabs.add(tabId);
    
    console.log('🔍 Checking URL for phishing:', url);
    
    try {
        const urlObj = new URL(url);
        const hostname = urlObj.hostname;
        
        // Async ML backend check
        checkIfUrlIsSafe(url).then(result => {
            const isSafe = result.isSafe;
            console.log(`Phish Verdict for ${hostname}: ${isSafe ? 'SAFE' : 'UNSAFE'} (Conf: ${result.confidence})`);
            
            // Store the full result (including confidence for popup)
            const fullResult = { isSafe, confidence: result.confidence, checkedAt: new Date().toISOString(), hostname };
            chrome.storage.local.set({ [url]: fullResult });
            
            if (!isSafe) {
                // Unsafe—block with warning
                showWarningPage(tabId, url);
            }
            // Safe sites load normally
        }).catch(error => {
            console.error('Safety check failed:', error);
            // Default to unsafe on total failure
            chrome.storage.local.set({ [url]: { isSafe: false, confidence: 0.0 } });
            showWarningPage(tabId, url);
        });
        
    } catch (error) {
        console.error('Error parsing URL:', error);
    } finally {
        // Clean up
        checkingTabs.delete(tabId);
    }
}

// Function to show warning page for unsafe websites
function showWarningPage(tabId, originalUrl) {
    console.log('🔴 Blocking phishing site:', originalUrl);
    
    // Create a simple HTML file for the warning page
    const warningHtml = `
    <!DOCTYPE html>
    <html>
    <head>
        <title>Security Warning - SafeBrowse</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #ff4444;
                margin: 0;
                padding: 40px;
                color: white;
                text-align: center;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                color: #333;
                max-width: 500px;
                margin: 0 auto;
            }
            h1 {
                color: #ff4444;
                margin-bottom: 20px;
            }
            .url {
                background: #fff5f5;
                padding: 10px;
                border-radius: 5px;
                margin: 20px 0;
                font-family: monospace;
                word-break: break-all;
            }
            .buttons {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
            button {
                flex: 1;
                padding: 12px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                cursor: pointer;
            }
            .back-btn {
                background: #4285f4;
                color: white;
            }
            .proceed-btn {
                background: #ff4444;
                color: white;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚠️ SECURITY WARNING</h1>
            <p>This website has been flagged as a potential phishing risk by our AI detector.</p>
            <div class="url">${originalUrl}</div>
            <p>Proceed at your own risk—consider going back to safety.</p>
            <div class="buttons">
                <button class="back-btn" id="backButton">← Go Back to Safety</button>
                <button class="proceed-btn" id="proceedButton">⚠️ Proceed Anyway</button>
            </div>
        </div>
        <script>
            document.getElementById('backButton').addEventListener('click', function() {
                if (window.history.length > 1) {
                    window.history.back();
                } else {
                    window.location.href = 'https://www.google.com';
                }
            });
            
            document.getElementById('proceedButton').addEventListener('click', function() {
                window.location.href = '${originalUrl}';
            });
        </script>
    </body>
    </html>
    `;
    
    // Update the tab to show warning page
    chrome.tabs.update(tabId, { 
        url: `data:text/html;charset=utf-8,${encodeURIComponent(warningHtml)}` 
    });
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getSafetyStatus") {
        chrome.storage.local.get([request.url], (result) => {
            if (result[request.url]) {
                sendResponse(result[request.url]);
            } else {
                sendResponse({ isSafe: null, hostname: 'Unknown' });
            }
        });
        return true;  // Keep message channel open for async
    }
    
    if (request.action === "checkUrlNow") {
        checkIfUrlIsSafe(request.url).then(result => {
            sendResponse({ isSafe: result.isSafe, confidence: result.confidence });
        }).catch(error => {
            console.error('Manual check failed:', error);
            sendResponse({ isSafe: false, confidence: 0.0 });  // Default to unsafe on error
        });
        return true;  // Async response
    }
});