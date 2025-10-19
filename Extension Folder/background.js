// background.js
// Listen for navigation and check URL with backend
chrome.webNavigation.onCommitted.addListener(async (details) => {
  const url = details.url;

  if (!url.startsWith("http")) return; // skip chrome:// or internal pages

  try {
    const response = await fetch("http://localhost:5000/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });

    if (!response.ok) throw new Error("Backend error");

    const result = await response.json();

    // Inject content.js and pass data
    chrome.scripting.executeScript({
      target: { tabId: details.tabId },
      files: ["content.js"]
    }, () => {
      chrome.scripting.executeScript({
        target: { tabId: details.tabId },
        func: (data) => {
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
  }
});