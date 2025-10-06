// Content script injected to show an in-page phishing warning overlay
(function() {
    const OVERLAY_ID = '__phish_warning_overlay__';
    const COUNTDOWN_ID = '__phish_warning_countdown__';

    function removeExisting() {
        const existing = document.getElementById(OVERLAY_ID);
        if (existing) existing.remove();
    }

    function createOverlay(detail) {
        removeExisting();

        const url = detail && detail.url ? detail.url : location.href;
        const confidence = detail && typeof detail.confidence === 'number' ? detail.confidence : null;

        const overlay = document.createElement('div');
        overlay.id = OVERLAY_ID;
        overlay.style.position = 'fixed';
        overlay.style.inset = '0';
        overlay.style.zIndex = '2147483647';
        overlay.style.background = 'rgba(0,0,0,0.55)';
        overlay.style.backdropFilter = 'blur(2px)';
        overlay.style.display = 'flex';
        overlay.style.alignItems = 'center';
        overlay.style.justifyContent = 'center';

        const card = document.createElement('div');
        card.style.width = 'min(420px, 92vw)';
        card.style.borderRadius = '14px';
        card.style.boxShadow = '0 12px 40px rgba(0,0,0,0.25)';
        card.style.background = '#ffffff';
        card.style.fontFamily = 'Segoe UI, Arial, sans-serif';
        card.style.padding = '20px';
        card.style.textAlign = 'center';

        const title = document.createElement('div');
        title.textContent = '⚠️ Security Warning!';
        title.style.fontSize = '18px';
        title.style.fontWeight = '700';
        title.style.marginBottom = '10px';

        const urlBox = document.createElement('div');
        urlBox.textContent = url;
        urlBox.style.fontSize = '12px';
        urlBox.style.wordBreak = 'break-all';
        urlBox.style.background = '#f3f6ff';
        urlBox.style.padding = '8px 10px';
        urlBox.style.borderRadius = '8px';
        urlBox.style.margin = '10px 0';
        urlBox.style.color = '#333';

        const msg = document.createElement('div');
        msg.textContent = 'This site is flagged as potentially dangerous.';
        msg.style.color = '#555';
        msg.style.fontSize = '13px';
        msg.style.marginBottom = '8px';

        const conf = document.createElement('div');
        conf.textContent = confidence != null ? `Confidence: ${Number(confidence).toFixed(2)}%` : 'Confidence: Unknown';
        conf.style.fontSize = '12px';
        conf.style.fontWeight = '600';
        conf.style.marginBottom = '12px';

        const countdown = document.createElement('div');
        countdown.id = COUNTDOWN_ID;
        countdown.textContent = 'Auto going back in 10s...';
        countdown.style.fontSize = '12px';
        countdown.style.marginBottom = '12px';

        const row = document.createElement('div');
        row.style.display = 'flex';
        row.style.gap = '8px';

        const goBackBtn = document.createElement('button');
        goBackBtn.textContent = '← Go Back';
        goBackBtn.style.flex = '1';
        goBackBtn.style.padding = '10px';
        goBackBtn.style.border = '2px solid #e0e0e0';
        goBackBtn.style.background = '#f8f9fa';
        goBackBtn.style.borderRadius = '8px';
        goBackBtn.style.cursor = 'pointer';

        const proceedBtn = document.createElement('button');
        proceedBtn.textContent = '⚠️ Proceed Anyway';
        proceedBtn.style.flex = '1';
        proceedBtn.style.padding = '10px';
        proceedBtn.style.border = '0';
        proceedBtn.style.background = '#ff4444';
        proceedBtn.style.color = '#fff';
        proceedBtn.style.borderRadius = '8px';
        proceedBtn.style.cursor = 'pointer';

        row.appendChild(goBackBtn);
        row.appendChild(proceedBtn);

        card.appendChild(title);
        card.appendChild(urlBox);
        card.appendChild(msg);
        card.appendChild(conf);
        card.appendChild(countdown);
        card.appendChild(row);
        overlay.appendChild(card);
        document.documentElement.appendChild(overlay);

        // Countdown: 10s -> history.back()
        let remaining = 10;
        const timer = setInterval(() => {
            remaining -= 1;
            if (remaining <= 0) {
                clearInterval(timer);
                try { window.history.back(); } catch (e) {}
                removeExisting();
            } else {
                countdown.textContent = `Auto going back in ${remaining}s...`;
            }
        }, 1000);

        // Handlers
        goBackBtn.addEventListener('click', () => {
            clearInterval(timer);
            try { window.history.back(); } catch (e) {}
            removeExisting();
        });

        proceedBtn.addEventListener('click', () => {
            clearInterval(timer);
            // Ask background to temporarily allow this hostname
            const host = (function() { try { return new URL(url).hostname; } catch (e) { return location.hostname; } })();
            const expiresAt = Date.now() + 5 * 60 * 1000;
            chrome.runtime.sendMessage({ action: 'tempAllowHost', host, expiresAt });
            removeExisting();
        });
    }

    // Only create overlay once per navigation; listen for data event
    if (!window.__phish_warning_bound__) {
        window.__phish_warning_bound__ = true;
        window.addEventListener('phish-warning', (e) => {
            createOverlay(e.detail || {});
        }, { once: true });
    }
})();


