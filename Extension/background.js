// Track which tabs are currently being checked
const checkingTabs = new Set();

// Listen when user navigates to any website (main frame only)
chrome.webNavigation.onBeforeNavigate.addListener((details) => {
    if (details.frameId === 0) {
        checkUrlSafety(details.url, details.tabId);
    }
});

// Send URL to backend and get safety info
async function checkIfUrlIsSafe(url) {
    try {
        const response = await fetch('http://localhost:5000/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        if (!response.ok) {
            throw new Error(`Backend error: ${response.status}`);
        }

        const result = await response.json();

        // Convert confidence to percentage
        const confidencePercent = result.confidence;

        // Map model label: 0 = Safe, 1 = Phishing
        const isPhishing = result.label === 1;
        const isSafe = !isPhishing;

        return {
            isSafe,
            isPhishing,
            confidence: confidencePercent,
            riskScore: isPhishing ? confidencePercent : 0.0
        };

    } catch (error) {
        console.error('Backend check failed, defaulting to unsafe', error);
        return { isSafe: false, isPhishing: true, confidence: 0, riskScore: 100 };
    }
}

// Main function to check URL safety
function checkUrlSafety(url, tabId) {
    if (checkingTabs.has(tabId)) return;
    checkingTabs.add(tabId);

    checkIfUrlIsSafe(url).then(result => {
        const hostname = new URL(url).hostname;

        console.log(`ML Verdict for ${hostname}: Safe=${result.isSafe}, Confidence=${result.confidence}%`);

        // Store the result in chrome.storage.local for popup.html
        const fullResult = {
            url,
            hostname,
            isSafe: result.isSafe,
            isPhishing: result.isPhishing,
            confidence: result.confidence,
            riskScore: result.riskScore,
            checkedAt: new Date().toISOString()
        };
        chrome.storage.local.set({ [url]: fullResult });

    }).catch(error => {
        console.error('Safety check failed:', error);
        chrome.storage.local.set({
            [url]: { url, hostname: new URL(url).hostname, isSafe: false, isPhishing: true, confidence: 0, riskScore: 100, checkedAt: new Date().toISOString() }
        });
    }).finally(() => {
        checkingTabs.delete(tabId);
    });
}

// Listen for messages from popup.html
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getSafetyStatus") {
        chrome.storage.local.get([request.url], (result) => {
            if (result[request.url]) {
                sendResponse(result[request.url]);
            } else {
                sendResponse({ isSafe: null, isPhishing: null, hostname: 'Unknown', confidence: 0 });
            }
        });
        return true; // Keep message channel open for async response
    }

    if (request.action === "checkUrlNow") {
        checkIfUrlIsSafe(request.url).then(result => {
            sendResponse(result);
        }).catch(error => {
            console.error('Manual check failed:', error);
            sendResponse({ isSafe: false, isPhishing: true, confidence: 0 });
        });
        return true; // Async response
    }
});
