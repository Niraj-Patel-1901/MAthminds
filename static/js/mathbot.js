// mathbot.js
// Adds click-to-select behavior to elements with class "solution-step",
// highlights the selected step, shows the Ask button, and sends the selected
// step + module name to /api/mathbot when the Ask button is clicked.

document.addEventListener('DOMContentLoaded', () => {
    const moduleEl = document.getElementById('module-name');
    const moduleName = moduleEl && moduleEl.dataset ? moduleEl.dataset.module : 'Unknown';
    const askBtn = document.getElementById('ask-mathbot-btn');
    if (!askBtn) return; // nothing to do if ask button missing

    // Inject small CSS for the selected step if not already present
    const styleId = 'mathbot-inline-style';
    if (!document.getElementById(styleId)) {
        const s = document.createElement('style');
        s.id = styleId;
        s.textContent = `
        .mathbot-selected { background: rgba(255,228,230,0.9) !important; border-radius: 6px; padding: 0.35rem !important; }
        #ask-mathbot-btn { transition: opacity 0.12s ease; }
        `;
        document.head.appendChild(s);
    }

    let selectedStep = null;

    function hideAsk() {
        askBtn.style.display = 'none';
    }

    function showAskNear(elem) {
        const rect = elem.getBoundingClientRect();
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const scrollLeft = window.scrollX || document.documentElement.scrollLeft;
        // Position to the right of the element where space allows, otherwise left
        let top = rect.top + scrollTop + rect.height / 2 - 18;
        let left = rect.right + scrollLeft + 10;
        // If off-screen to right, position to left side
        if (left + 140 > window.innerWidth + scrollLeft) {
            left = rect.left + scrollLeft - 140 - 10;
        }
        askBtn.style.top = Math.max(8, top) + 'px';
        askBtn.style.left = Math.max(8, left) + 'px';
        askBtn.style.display = 'block';
    }

    // Add handlers to steps
    const steps = Array.from(document.querySelectorAll('.solution-step'));
    steps.forEach((step) => {
        // make keyboard-focusable and pointer-friendly
        step.tabIndex = 0;
        step.style.cursor = 'pointer';

        step.addEventListener('click', (e) => {
            e.stopPropagation();
            if (selectedStep && selectedStep !== step) {
                selectedStep.classList.remove('mathbot-selected');
            }
            selectedStep = step;
            step.classList.add('mathbot-selected');
            showAskNear(step);
        });

        // support keyboard selection (Enter)
        step.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                step.click();
            }
        });
    });

    // Click outside -> deselect
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.solution-step') && e.target !== askBtn) {
            if (selectedStep) selectedStep.classList.remove('mathbot-selected');
            selectedStep = null;
            hideAsk();
        }
    });

    // Ask button click -> send POST
    askBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (!selectedStep) return;
        const stepHtml = selectedStep.innerHTML;
        const stepText = (selectedStep.innerText || selectedStep.textContent || '').trim();

        const payload = { module: moduleName, step_html: stepHtml, step_text: stepText };

        askBtn.disabled = true;
        const origText = askBtn.innerText;
        askBtn.innerText = 'Sending...';

        try {
            const res = await fetch('/api/mathbot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await res.json().catch(() => ({}));
            // Basic feedback: show returned text if present
            if (data && (data.answer || data.response || data.message)) {
                const msg = data.answer || data.response || data.message;
                // use a simple browser alert for now
                window.alert(String(msg));
            } else if (!res.ok) {
                window.alert('MathBot request failed.');
            } else {
                window.alert('MathBot responded.');
            }
        } catch (err) {
            console.error('MathBot error:', err);
            window.alert('Error contacting MathBot.');
        } finally {
            askBtn.disabled = false;
            askBtn.innerText = origText;
        }
    });

    // Hide the ask button initially
    hideAsk();
});
