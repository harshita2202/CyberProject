document.addEventListener('DOMContentLoaded', function() {
    const urlDisplay = document.getElementById('urlDisplay');
    const checkingCard = document.getElementById('checkingCard');
    const safeCard = document.getElementById('safeCard');
    const unsafeCard = document.getElementById('unsafeCard');

    const continueBtn = document.getElementById('continueBtn');
    const goBackBtn = document.getElementById('goBackBtn');
    const proceedBtn = document.getElementById('proceedBtn');

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

    // Get current tab info
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
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        const tabId = tabs[0].id;
        chrome.scripting.executeScript({
            target: { tabId: tabId },
            func: () => window.history.back()
        });
        window.close();
    });
}

function proceedAnyway() {
    window.close(); 
}
