// popup.js
document.addEventListener('DOMContentLoaded', function() {
    const urlDisplay = document.getElementById('urlDisplay');
    const checkingCard = document.getElementById('checkingCard');
    const safeCard = document.getElementById('safeCard');
    const unsafeCard = document.getElementById('unsafeCard');

    const continueBtn = document.getElementById('continueBtn');
    const goBackBtn = document.getElementById('goBackBtn');
    const proceedBtn = document.getElementById('proceedBtn');

	// Settings: Auto-block toggle elements
	const autoBlockToggle = document.getElementById('autoBlockToggle');
	const autoBlockLabel = document.getElementById('autoBlockLabel');

    // Create confidence display elements dynamically
    const safeConfidence = document.createElement('div');
    safeConfidence.id = 'safeConfidence';
    safeConfidence.style.marginTop = '10px';
    safeCard.appendChild(safeConfidence);

    const unsafeConfidence = document.createElement('div');
    unsafeConfidence.id = 'unsafeConfidence';
    unsafeConfidence.style.marginTop = '10px';
    unsafeCard.appendChild(unsafeConfidence);

    // Event listeners for buttons
    continueBtn.addEventListener('click', visitSite);
    goBackBtn.addEventListener('click', goBack);
    proceedBtn.addEventListener('click', proceedAnyway);

	showCard('checking');

	// Initialize auto-block toggle from storage
	if (autoBlockToggle) {
		chrome.storage.local.get(['autoBlockEnabled'], (res) => {
			const enabled = Boolean(res.autoBlockEnabled);
			autoBlockToggle.checked = enabled;
			autoBlockLabel.textContent = enabled ? 'On' : 'Off';
		});
		autoBlockToggle.addEventListener('change', () => {
			const enabled = autoBlockToggle.checked;
			autoBlockLabel.textContent = enabled ? 'On' : 'Off';
			chrome.storage.local.set({ autoBlockEnabled: enabled });
		});
	}

    // If opened as an auto-warning popup, there will be a blocked param
    const params = new URLSearchParams(window.location.search);
    const blockedUrl = params.get('blocked');
    if (blockedUrl) {
        const decoded = decodeURIComponent(blockedUrl);
        urlDisplay.textContent = decoded;
        // Get stored result if available to show confidence
        chrome.storage.local.get([decoded], (res) => {
            const r = res[decoded];
            if (r && r.confidence !== undefined) {
                unsafeConfidence.textContent = `Confidence: ${Number(r.confidence).toFixed(2)}%`;
            } else {
                unsafeConfidence.textContent = `Confidence: Unknown`;
            }
        });
        showCard('unsafe');
        return;
    }

    // Normal behaviour: popup invoked from action icon
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        const currentTab = tabs[0];
        const currentUrl = currentTab.url;

        // Display the URL (shortened)
        const displayUrl = shortenUrl(currentUrl);
        urlDisplay.textContent = displayUrl;

        // Ask background script for safety status
        chrome.runtime.sendMessage({ action: "getSafetyStatus", url: currentUrl }, (response) => {
            if (response.isSafe === true) {
                // Show safe card
                safeConfidence.textContent = `Confidence: ${response.confidence.toFixed(2)}%`;
                showCard('safe');
            } else if (response.isSafe === false) {
                // Show unsafe card
                unsafeConfidence.textContent = `Confidence: ${response.confidence.toFixed(2)}%`;
                showCard('unsafe');
            } else {
                // If not checked yet, ask background to check now
                checkUrlNow(currentUrl);
            }
        });
    });
});

function showCard(cardType) {
    document.getElementById('checkingCard').style.display = 'none';
    document.getElementById('safeCard').style.display = 'none';
    document.getElementById('unsafeCard').style.display = 'none';

    switch(cardType) {
        case 'checking':
            document.getElementById('checkingCard').style.display = 'block';
            break;
        case 'safe':
            document.getElementById('safeCard').style.display = 'block';
            break;
        case 'unsafe':
            document.getElementById('unsafeCard').style.display = 'block';
            break;
    }
}

function shortenUrl(url) {
    try {
        const urlObj = new URL(url);
        return urlObj.hostname;
    } catch (e) {
        return url;
    }
}

function checkUrlNow(url) {
    chrome.runtime.sendMessage({ action: "checkUrlNow", url: url }, (response) => {
        if (response.isSafe === true) {
            document.getElementById('safeConfidence').textContent = `Confidence: ${response.confidence.toFixed(2)}%`;
            showCard('safe');
        } else {
            document.getElementById('unsafeConfidence').textContent = `Confidence: ${response.confidence.toFixed(2)}%`;
            showCard('unsafe');
        }
    });
}

// Button functions
function visitSite() {
    window.close();
}

function goBack() {
    // For the auto-popup case the user may not have the original tab in focus.
    // We'll attempt to find any tab with the blocked URL and navigate it back.
    const params = new URLSearchParams(window.location.search);
    const blockedUrl = params.get('blocked');
    if (blockedUrl) {
        const target = decodeURIComponent(blockedUrl);
        // find any tab that matches the blocked URL and navigate it back
        chrome.tabs.query({}, (tabs) => {
            for (const t of tabs) {
                if (t.url && t.url.startsWith(target)) {
                    // navigate back in that tab
                    chrome.scripting.executeScript({
                        target: { tabId: t.id },
                        func: () => window.history.back()
                    });
                    break;
                }
            }
            window.close();
        });
    } else {
        // normal popup: just navigate the current tab back
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            const tabId = tabs[0].id;
            chrome.scripting.executeScript({
                target: { tabId: tabId },
                func: () => window.history.back()
            });
            window.close();
        });
    }
}

function proceedAnyway() {
	// If auto-popup, temporarily allow the domain and reopen the URL in a new tab
	const params = new URLSearchParams(window.location.search);
	const blockedUrl = params.get('blocked');
	if (blockedUrl) {
		const decoded = decodeURIComponent(blockedUrl);
		let hostname = decoded;
		try { hostname = new URL(decoded).hostname; } catch (e) { /* keep as is */ }
		const expiresAt = Date.now() + 5 * 60 * 1000; // 5 minutes temporary allow
		chrome.storage.local.get(['temporaryAllowlist'], (res) => {
			const list = res.temporaryAllowlist || {};
			list[hostname] = expiresAt;
			chrome.storage.local.set({ temporaryAllowlist: list }, () => {
				chrome.tabs.create({ url: decoded });
				window.close();
			});
		});
	} else {
		// Normal popup: simply close
		window.close();
	}
}
