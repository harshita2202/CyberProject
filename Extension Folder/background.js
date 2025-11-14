// Add at top before listener
const processedNavigations = new Map();

chrome.tabs.onRemoved.addListener((tabId) => {
  processedNavigations.delete(tabId);
});

chrome.webNavigation.onCommitted.addListener(async (details) => {
  const url = details.url;
  if (!url.startsWith("http")) return;
  if (details.frameId !== 0) return; // only top-level frame

  const normalizedUrl = url.split('#')[0];
  const now = Date.now();
  const lastEntry = processedNavigations.get(details.tabId);
  if (lastEntry && lastEntry.url === normalizedUrl && (now - lastEntry.time) < 2000) {
    return; // avoid duplicate processing for the same navigation
  }
  processedNavigations.set(details.tabId, { url: normalizedUrl, time: now });

  // 🔹 Step 1: Inject a temporary "checking" popup immediately
  chrome.scripting.executeScript({
    target: { tabId: details.tabId },
    func: () => {
      const style = document.createElement("style");
      style.textContent = `
        .checking-popup {
          position: fixed;
          top: 20px;
          right: 20px;
          background: rgba(0,0,0,0.85);
          color: white;
          padding: 12px 16px;
          border-radius: 10px;
          font-family: Arial, sans-serif;
          font-size: 14px;
          z-index: 999999;
          box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
      `;
      document.head.appendChild(style);
      if (!document.querySelector(".checking-popup")) {
        const popup = document.createElement("div");
        popup.className = "checking-popup";
        popup.innerText = "🔄 Checking site safety...";
        document.body.appendChild(popup);
      }
    }
  });

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);

    const response = await fetch("http://localhost:5000/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
      signal: controller.signal
    });

    clearTimeout(timeout);
    if (!response.ok) throw new Error("Backend error");

    const result = await response.json();
    chrome.storage.local.set({ [`result_${details.tabId}`]: result });

    // 🔹 Step 2: Get user's blocked categories
    chrome.storage.sync.get(["blockedCategories"], (data) => {
      const blocked = (data.blockedCategories || []).map(c => c.toLowerCase());
      const siteCategory = (result.category || "").toLowerCase();


      // 🚫 If blocked, redirect to our blockedOverlay page
      if (blocked.includes(siteCategory)) {
        // Remove checking popup first
        chrome.scripting.executeScript({
          target: { tabId: details.tabId },
          func: () => {
            document.querySelector(".checking-popup")?.remove();
          }
        });
        
        // Save category name to storage
        chrome.storage.local.set({ currentBlockedCategory: result.category }, () => {
          // Redirect to blocked overlay page (with category in URL)
          chrome.tabs.update(details.tabId, {
            url: chrome.runtime.getURL(
              `blockedOverlay/blockedOverlay.html?category=${encodeURIComponent(result.category)}`
            )
          });
        });
        return; // stop further processing
      }

      // ✅ Otherwise show phishing/safe result popup
      chrome.scripting.executeScript({
        target: { tabId: details.tabId },
        files: ["content.js"]
      }, () => {
        chrome.scripting.executeScript({
          target: { tabId: details.tabId },
          func: (data) => {
            document.querySelector(".checking-popup")?.remove();
            window.phishingData = data;
            if (typeof showPhishingResult === "function") {
              showPhishingResult(window.phishingData);
            }
          },
          args: [result]
        });
      });
    });

  } catch (err) {
    console.error("❌ Phishing check failed:", err);
    chrome.scripting.executeScript({
      target: { tabId: details.tabId },
      func: () => {
        const popup = document.querySelector(".checking-popup");
        if (popup) popup.textContent = "⚠️ Taking too long... please wait or reload.";
      }
    });
  }
});


// 🔹 When extension icon is clicked: open options/settings overlay
chrome.action.onClicked.addListener((tab) => {

  // If user is on an extension page, clicking icon should open settings
  if (tab.url.startsWith("chrome-extension://")) {
    chrome.runtime.openOptionsPage();
    return;
  }

  // Otherwise show phishing popup again
  chrome.tabs.sendMessage(tab.id, {
    action: "showLastPopup",
    tabId: tab.id
  });

});