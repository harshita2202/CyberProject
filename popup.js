document.getElementById("checkBtn").addEventListener("click", () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    let currentURL = tabs[0].url;
    document.getElementById("result").innerText = "Current URL: " + currentURL;

    
  });
});
