function showBlockedOverlay(category) {
  const categoryEl = document.getElementById("blocked-category");
  const redirectTextEl = document.getElementById("redirect-text");
  
  categoryEl.textContent = category || "Unknown";
  
  // Remove the timer text and show simple message
  redirectTextEl.textContent = "This site is blocked in your settings";
}

// 🧩 Try to get category from URL param first
const urlParams = new URLSearchParams(window.location.search);
const categoryFromUrl = urlParams.get("category");

if (categoryFromUrl) {
  showBlockedOverlay(categoryFromUrl);
} else {
  // 🧩 Fallback: read from storage
  chrome.storage.local.get("currentBlockedCategory", (data) => {
    if (data.currentBlockedCategory) {
      showBlockedOverlay(data.currentBlockedCategory);
    } else {
      showBlockedOverlay("Unknown");
    }
  });
}