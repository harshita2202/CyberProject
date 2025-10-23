function showPhishingResult(data) {
  const { status, confidence, isSafe, category } = data;

  // Inject styles dynamically
  const style = document.createElement("style");
  style.textContent = `
    .safe-popup {
      position: fixed;
      top: 20px;
      right: 20px;
      background: rgba(0, 150, 0, 0.9);
      color: white;
      padding: 12px 16px;
      border-radius: 10px;
      font-family: Arial, sans-serif;
      font-size: 14px;
      z-index: 999999;
      box-shadow: 0 4px 8px rgba(0,0,0,0.3);
      animation: fadeIn 0.5s ease;
    }
    .warning-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.75);
      z-index: 999999;
      display: flex;
      justify-content: center;
      align-items: center;
    }
    .warning-box {
      background: white;
      color: black;
      padding: 30px;
      border-radius: 12px;
      text-align: center;
      width: 320px;
      box-shadow: 0 6px 20px rgba(0,0,0,0.4);
      font-family: Arial, sans-serif;
    }
    .warning-box h2 { color: red; margin-bottom: 10px; }
    .warning-box .buttons { margin-top: 15px; display: flex; justify-content: space-around; }
    .warning-box button {
      padding: 8px 14px;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-weight: bold;
    }
    #continueBtn { background-color: #4CAF50; color: white; }
    #goBackBtn { background-color: #f44336; color: white; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
  `;
  document.head.appendChild(style);

  // Remove existing elements
  document.querySelector(".safe-popup")?.remove();
  document.querySelector(".warning-overlay")?.remove();

  if (isSafe) {
    const popup = document.createElement("div");
    popup.className = "safe-popup";
    popup.innerHTML = `✅ ${status}<br>Category: ${category || 'Unknown'}<br>Confidence: ${confidence.toFixed(2)}%`;
    document.body.appendChild(popup);
    setTimeout(() => popup.remove(), 4000);
  } else {
    const overlay = document.createElement("div");
    overlay.className = "warning-overlay";
    overlay.innerHTML = `
      <div class="warning-box">
        <h2>⚠️ ${status}</h2>
        <p>This website may be harmful.</p>
        <p>Category: ${category || 'Unknown'}</p>
        <p>Confidence: ${confidence.toFixed(2)}%</p>
        <div class="buttons">
          <button id="continueBtn">Continue Anyway</button>
          <button id="goBackBtn">Go Back</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    const timer = setTimeout(() => window.history.back(), 10000);

    document.getElementById("continueBtn").addEventListener("click", () => {
      clearTimeout(timer);
      overlay.remove();
    });
    document.getElementById("goBackBtn").addEventListener("click", () => {
      clearTimeout(timer);
      window.history.back();
    });
  }
}