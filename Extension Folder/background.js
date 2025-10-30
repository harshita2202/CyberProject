chrome.webNavigation.onCommitted.addListener(async (details) => {
  const url = details.url;
  if (!url.startsWith("http")) return;

  // Inject "checking" popup immediately
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
      const existing = document.querySelector(".checking-popup");
      if (!existing) {
        const popup = document.createElement("div");
        popup.className = "checking-popup";
        popup.innerText = "🔄 Checking site safety...";
        document.body.appendChild(popup);
      }
    }
  });

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000); // ⏱️ allow long processing (20s)

    const response = await fetch("http://localhost:5000/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
      signal: controller.signal
    });

    clearTimeout(timeout);
    if (!response.ok) throw new Error("Backend error");

    const result = await response.json();

    // ✅ Save latest result for this tab
    chrome.storage.local.set({ [`result_${details.tabId}`]: result });

    // Inject content.js if not already injected
    chrome.scripting.executeScript({
      target: { tabId: details.tabId },
      files: ["content.js"]
    }, () => {
      // Now update popup with actual result
      chrome.scripting.executeScript({
        target: { tabId: details.tabId },
        func: (data) => {
          // Remove the loading popup
          document.querySelector(".checking-popup")?.remove();
          window.phishingData = data;
          if (typeof showPhishingResult === "function") {
            showPhishingResult(window.phishingData);
          }
        },
        args: [result]
      });
    });

  } catch (err) {
    console.error("❌ Phishing check failed:", err);

    // Show timeout or error popup on the webpage
    chrome.scripting.executeScript({
      target: { tabId: details.tabId },
      func: () => {
        const popup = document.querySelector(".checking-popup");
        if (popup) popup.textContent = "⚠️ Taking too long... please wait or reload.";
      }
    });
  }
});


// ✅ Re-show popup when clicking the extension icon
chrome.action.onClicked.addListener(async (tab) => {
  chrome.storage.local.get([`result_${tab.id}`], (data) => {
    const result = data[`result_${tab.id}`];
    if (result) {
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ["content.js"]
      }, () => {
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: (storedData) => {
            if (typeof showPhishingResult === "function") {
              showPhishingResult(storedData);
            }
          },
          args: [result]
        });
      });
    } else {
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          const existing = document.querySelector(".checking-popup");
          if (!existing) {
            const popup = document.createElement("div");
            popup.className = "checking-popup";
            popup.innerText = "ℹ️ No recent result. Please reload the page.";
            document.body.appendChild(popup);
            setTimeout(() => popup.remove(), 4000);
          }
        }
      });
    }
  });
});