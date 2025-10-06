// background.js

// Track which tabs are currently being checked
const checkingTabs = new Set();

// Threshold for auto-popup (adjust as needed)
const POPUP_CONFIDENCE_THRESHOLD = 60; // percent

// Listen when user navigates to any website (main frame only)
chrome.webNavigation.onBeforeNavigate.addListener((details) => {
    if (details.frameId === 0) {
        // Only check http/https pages; skip internal/extension pages
        if (typeof details.url === 'string' && /^https?:\/\//i.test(details.url)) {
            checkUrlSafety(details.url, details.tabId);
        }
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

        // Normalize confidence to percentage if backend returns 0-1
        let confidence = result.confidence;
        if (typeof confidence === 'number' && confidence <= 1.0) confidence = confidence * 100;
        const confidencePercent = Number(confidence);

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

// Helper: check if hostname is temporarily allowed (user chose Proceed Anyway)
async function isTemporarilyAllowed(hostname) {
    return new Promise((resolve) => {
        chrome.storage.local.get(['temporaryAllowlist'], (res) => {
            const list = res.temporaryAllowlist || {};
            const now = Date.now();
            // prune expired entries
            let changed = false;
            for (const [host, expires] of Object.entries(list)) {
                if (typeof expires === 'number' && expires < now) {
                    delete list[host];
                    changed = true;
                }
            }
            if (changed) {
                chrome.storage.local.set({ temporaryAllowlist: list });
            }
            const allowedUntil = list[hostname];
            resolve(typeof allowedUntil === 'number' && allowedUntil > now);
        });
    });
}

// Helper: read the auto-block toggle
async function isAutoBlockEnabled() {
    return new Promise((resolve) => {
        chrome.storage.local.get(['autoBlockEnabled'], (res) => {
            resolve(Boolean(res.autoBlockEnabled));
        });
    });
}

// Helper: check if a warning popup for the same blocked URL already exists
async function warningPopupExists(blockedUrl) {
    return new Promise((resolve) => {
        chrome.windows.getAll({ populate: true }, (windows) => {
            for (const win of windows) {
                for (const tab of win.tabs || []) {
                    try {
                        if (!tab || !tab.url) continue;
                        // create URL object safely (some tab.url values may be chrome:// or extension URLs)
                        const parsed = new URL(tab.url, 'https://example.com');
                        // match popup.html path and check query param
                        if (parsed.pathname.endsWith('/popup.html') || parsed.pathname.endsWith('popup.html')) {
                            const params = new URLSearchParams(parsed.search);
                            const existingBlocked = params.get('blocked');
                            if (existingBlocked && decodeURIComponent(existingBlocked) === blockedUrl) {
                                resolve(true);
                                return;
                            }
                        }
                    } catch (e) {
                        // ignore malformed tab url
                    }
                }
            }
            resolve(false);
        });
    });
}

// Main function to check URL safety
function checkUrlSafety(url, tabId) {
    // Guard: only process http/https URLs
    if (typeof url !== 'string' || !/^https?:\/\//i.test(url)) {
        return;
    }
    if (checkingTabs.has(tabId)) return;
    checkingTabs.add(tabId);

    checkIfUrlIsSafe(url).then(async (result) => {
        const hostname = (() => {
            try { return new URL(url).hostname; } catch (e) { return url; }
        })();

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

        // ⚠️ Show in-page warning overlay for phishing sites
        if (result.isPhishing && result.confidence >= POPUP_CONFIDENCE_THRESHOLD) {
            try {
                // Skip overlay if temporarily allowed
                const temporarilyAllowed = await isTemporarilyAllowed(hostname);
                if (temporarilyAllowed) return;

                if (typeof tabId === 'number') {
                    // Inject overlay script and dispatch data event
                    chrome.scripting.executeScript({
                        target: { tabId },
                        files: ['warning_overlay.js']
                    }, () => {
                        if (chrome.runtime.lastError) {
                            console.error('Failed to inject overlay script:', chrome.runtime.lastError);
                            return;
                        }
                        chrome.scripting.executeScript({
                            target: { tabId },
                            func: (blockedUrl, confidence) => {
                                window.dispatchEvent(new CustomEvent('phish-warning', {
                                    detail: { url: blockedUrl, confidence }
                                }));
                            },
                            args: [url, result.confidence]
                        });
                    });
                }
            } catch (err) {
                console.error('Failed to show in-page warning overlay:', err);
            }
        }

    }).catch(error => {
        console.error('Safety check failed:', error);
        chrome.storage.local.set({
            [url]: { url, hostname: (() => { try { return new URL(url).hostname } catch (e) { return url } })(), isSafe: false, isPhishing: true, confidence: 0, riskScore: 100, checkedAt: new Date().toISOString() }
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

    // From overlay: temporarily allow a host
    if (request.action === 'tempAllowHost') {
        const { host, expiresAt } = request;
        if (!host || typeof expiresAt !== 'number') { sendResponse({ ok: false }); return; }
        chrome.storage.local.get(['temporaryAllowlist'], (res) => {
            const list = res.temporaryAllowlist || {};
            list[host] = expiresAt;
            chrome.storage.local.set({ temporaryAllowlist: list }, () => sendResponse({ ok: true }));
        });
        return true;
    }
});
