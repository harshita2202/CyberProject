document.addEventListener('DOMContentLoaded', function() {
    const urlDisplay = document.getElementById('urlDisplay');
    const checkingCard = document.getElementById('checkingCard');
    const safeCard = document.getElementById('safeCard');
    const unsafeCard = document.getElementById('unsafeCard');
    
    // Add event listeners to buttons
    document.getElementById('continueBtn').addEventListener('click', visitSite);
    document.getElementById('goBackBtn').addEventListener('click', goBack);
    document.getElementById('proceedBtn').addEventListener('click', proceedAnyway);
    
    showCard('checking');
    
    // Get current tab info
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        const currentTab = tabs[0];
        const currentUrl = currentTab.url;
        
        // Display the URL
        const displayUrl = shortenUrl(currentUrl);
        urlDisplay.textContent = displayUrl;
        
        // Get safety status from background script
        chrome.runtime.sendMessage(
            { action: "getSafetyStatus", url: currentUrl }, 
            (response) => {
                if (response.isSafe === true) {
                    showCard('safe');
                } else if (response.isSafe === false) {
                    showCard('unsafe');
                } else {
                    // If not checked yet, ask background to check now
                    checkUrlNow(currentUrl);
                }
            }
        );
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
    // Ask background script to check this URL immediately
    chrome.runtime.sendMessage(
        { action: "checkUrlNow", url: url }, 
        (response) => {
            if (response.isSafe === true) {
                showCard('safe');
            } else {
                showCard('unsafe');
            }
        }
    );
}

// Button functions
function visitSite() {
    console.log('Closing popup - continuing to site');
    window.close();
}

function goBack() {
    console.log('Going back to previous page');
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (tabs[0]) {
            chrome.tabs.goBack(tabs[0].id);
        }
        window.close();
    });
}

function proceedAnyway() {
    console.log('Proceeding to unsafe site');
    window.close();
}