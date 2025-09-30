// List of safe websites (whitelist)
const SAFE_WEBSITES = [
    'google.com',
    'github.com',
    'stackoverflow.com',
    'wikipedia.org',
    'microsoft.com',
    'apple.com',
    'youtube.com',
    'facebook.com',
    'instagram.com',
    'twitter.com',
    'linkedin.com',
    'reddit.com',
    'amazon.com',
    'netflix.com',
    'spotify.com'
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

// Function to check if URL is safe
function checkUrlSafety(url, tabId) {
    // Avoid checking the same tab multiple times
    if (checkingTabs.has(tabId)) return;
    checkingTabs.add(tabId);
    
    console.log('🔍 Checking URL:', url);
    
    try {
        const urlObj = new URL(url);
        const hostname = urlObj.hostname;
        
        // Check if website is in our safe list
        const isSafe = SAFE_WEBSITES.some(safeSite => 
            hostname.includes(safeSite) || hostname.endsWith('.' + safeSite)
        );
        
        console.log(`✅ Safety result for ${hostname}: ${isSafe ? 'SAFE' : 'UNSAFE'}`);
        
        // Store the result
        chrome.storage.local.set({ 
            [url]: { 
                isSafe: isSafe, 
                checkedAt: new Date().toISOString(),
                hostname: hostname
            } 
        });
        
        if (!isSafe) {
            // Unsafe website - show warning and block
            showWarningPage(tabId, url);
        }
        // Safe websites just load normally
        
    } catch (error) {
        console.error('❌ Error checking URL:', error);
    } finally {
        // Remove from checking set
        checkingTabs.delete(tabId);
    }
}

// Function to check if URL is safe (reusable)
function checkIfUrlIsSafe(url) {
    try {
        const urlObj = new URL(url);
        const hostname = urlObj.hostname;
        
        return SAFE_WEBSITES.some(safeSite => 
            hostname.includes(safeSite) || hostname.endsWith('.' + safeSite)
        );
    } catch (error) {
        return false;
    }
}

// Function to show warning page for unsafe websites
function showWarningPage(tabId, originalUrl) {
    console.log('🔴 Unsafe website - blocking:', originalUrl);
    
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
            <p>This website is not in our safe list and may pose security risks.</p>
            <div class="url">${originalUrl}</div>
            <p>We recommend only visiting trusted websites.</p>
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
        return true;
    }
    
    if (request.action === "checkUrlNow") {
        const isSafe = checkIfUrlIsSafe(request.url);
        sendResponse({ isSafe: isSafe });
        return true;
    }
});