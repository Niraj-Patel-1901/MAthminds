// static/js/beta-gamma.js
document.addEventListener("DOMContentLoaded", () => {
  const integralInput = document.getElementById("integralInput");
  const solveBtn = document.getElementById("solveBtn");
  const tryEx1 = document.getElementById("tryEx1");
  const tryEx2 = document.getElementById("tryEx2");
  const tryEx3 = document.getElementById("tryEx3");
  const resetBtn = document.getElementById("resetBtn");
  const solutionDiv = document.getElementById("solution");
  // Global selected step text
  window.selectedStepText = "";
  const askBtn = document.getElementById("ask-mathbot-btn");

  // Example lists for Gamma and Beta functions (exam-style). Use SymPy-friendly ** for powers.
  const gammaExamples = [
    "integrate(x**4*exp(-x),(x,0,oo))",
    "integrate(x**(1/2)*exp(-x),(x,0,oo))",
    // Use a Beta-type example in the third slot as requested
    "integrate(x**2*(1-x)**3,(x,0,1))"
  ];

  const betaExamples = [
    "integrate(x**2*(1-x)**3,(x,0,1))",
    "integrate(x**(a-1)*(1-x)**(b-1),(x,0,1))",
    "integrate(sqrt(x)*(1-x)**2,(x,0,1))"
  ];

  // Track indices per problem type so clicks cycle through examples
  const exampleIndices = { gamma: 0, beta: 0 };

  function getProblemType() {
    const sel = document.getElementById('problemType');
    if (!sel) return 'gamma';
    const v = String(sel.value || '').toLowerCase();
    if (v.includes('beta')) return 'beta';
    return 'gamma';
  }

  // Single handler used by example buttons — cycles through the chosen list
  function onTryExampleClick() {
    const type = getProblemType();
    const list = type === 'beta' ? betaExamples : gammaExamples;
    const idx = exampleIndices[type] % list.length;
    const example = list[idx];
    integralInput.value = example;
    exampleIndices[type] = (exampleIndices[type] + 1) % list.length;

    solutionDiv.innerHTML = '<p class="text-blue-600">Example loaded! Click Solve to view the solution.</p>';
    if (window.MathJax) {
      try { MathJax.typesetPromise(); } catch (e) { /* ignore */ }
    }
  }

  // Wire all three example buttons to the cycling handler so any acts as "Try Example"
  tryEx1.addEventListener('click', onTryExampleClick);
  tryEx2.addEventListener('click', onTryExampleClick);
  tryEx3.addEventListener('click', onTryExampleClick);

  resetBtn.addEventListener("click", () => {
    integralInput.value = "";
    solutionDiv.innerHTML = '<p>Enter an integral and click Solve. Examples: see buttons above.</p>';
  });

  solveBtn.addEventListener("click", async () => {
    const integralStr = integralInput.value.trim();
    if (!integralStr) {
      solutionDiv.innerHTML = '<p class="text-red-600">Please enter an integral (e.g. integrate(...)).</p>';
      return;
    }
    solutionDiv.innerHTML = '<p>Computing... (SymPy in backend)</p>';

    try {
      const res = await fetch("/api/special-integrals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "symbolic", params: { integral: integralStr } })
      });
      const data = await res.json();
      if (!data.success) {
        solutionDiv.innerHTML = `<p class="text-red-600">Error: ${data.error}</p>`;
        return;
      }

      // Build formatted output
      let html = `<div class="space-y-3">`;
      html += `<div><b>Input:</b> ${data.input}</div>`;
      if (data.steps && data.steps.length) {
        html += `<div><b>Steps:</b><div class="mt-2">`;
        data.steps.forEach((s, i) => {
          html += `<p><b>Step ${i+1}:</b> ${s}</p>`;
        });
        html += `</div></div>`;
      }
      html += `<div><b>Result:</b> <div class="text-blue-700 font-semibold">\\(${data.result}\\)</div></div>`;
      html += `</div>`;
      solutionDiv.innerHTML = html;
      if (window.MathJax) MathJax.typesetPromise().then(() => {
        // After MathJax finishes initial typesetting, attach step handlers
        attachStepClickHandlers();
      }).catch(() => { attachStepClickHandlers(); });
      else attachStepClickHandlers();
    } catch (err) {
      console.error(err);
      solutionDiv.innerHTML = `<p class="text-red-600">Unexpected error: ${err.message}</p>`;
    }
  });

  // Attach click handlers to solution steps, add class "solution-step"
  function attachStepClickHandlers() {
    if (!solutionDiv) return;
    // Find the Steps container (bold label 'Steps:')
    const bolds = Array.from(solutionDiv.querySelectorAll('b'));
    let stepsContainer = null;
    for (const b of bolds) {
      if (b.textContent && b.textContent.trim().startsWith('Steps')) {
        // the next element is the container with class mt-2
        const parent = b.parentElement;
        if (!parent) continue;
        stepsContainer = parent.querySelector('.mt-2') || parent.lastElementChild;
        break;
      }
    }
    if (!stepsContainer) return;

    const steps = Array.from(stepsContainer.querySelectorAll('p'));
    steps.forEach((p) => {
      p.classList.add('solution-step');
      p.style.cursor = 'pointer';
      // prevent duplicate handlers
      p.removeEventListener('click', onStepClick);
      p.addEventListener('click', onStepClick);
    });
  }

  function onStepClick(ev) {
    ev.stopPropagation();
    const el = ev.currentTarget;
    // Remove highlight from all steps
    const all = document.querySelectorAll('.solution-step');
    all.forEach(a => {
      a.classList.remove('selected-solution-step');
      a.style.background = '';
    });

    // Highlight clicked step (pink background)
    el.classList.add('selected-solution-step');
    el.style.background = 'linear-gradient(90deg, rgba(255,182,193,0.25), rgba(255,192,203,0.2))';

    // Store selected text globally
    window.selectedStepText = el.innerText.trim();

    // Ensure MathJax rendering unaffected (re-typeset the element if MathJax present)
    if (window.MathJax) {
      try { MathJax.typesetPromise([el]); } catch (e) { /* ignore */ }
    }

    // Show Ask button near the clicked step
    showAskButtonNearStep(el);
  }

  // Show floating ask button near a given step element
  function showAskButtonNearStep(stepEl) {
    if (!askBtn || !stepEl) return;
    // Unhide first to allow offset calculations
    askBtn.style.display = 'block';
    askBtn.style.position = 'absolute';
    askBtn.style.zIndex = 9999;

    // Small timeout to ensure layout updated
    setTimeout(() => {
      const rect = stepEl.getBoundingClientRect();
      const btnRect = askBtn.getBoundingClientRect();
      const left = rect.right + window.scrollX + 8; // 8px to the right
      // vertically center relative to step
      const top = rect.top + window.scrollY + (rect.height - btnRect.height) / 2;
      askBtn.style.left = `${Math.max(8, left)}px`;
      askBtn.style.top = `${Math.max(8, top)}px`;
      askBtn.style.display = 'block';
    }, 10);
  }

  function hideAskButton() {
    if (!askBtn) return;
    askBtn.style.display = 'none';
  }

  // Hide when clicking outside any step or the ask button
  document.addEventListener('click', (e) => {
    const isStep = e.target.closest && e.target.closest('.solution-step');
    const isAsk = e.target.closest && e.target.closest('#ask-mathbot-btn');
    if (!isStep && !isAsk) {
      // remove highlights
      const all = document.querySelectorAll('.solution-step');
      all.forEach(a => { a.classList.remove('selected-solution-step'); a.style.background = ''; });
      window.selectedStepText = "";
      hideAskButton();
    }
  });

  // Ask button behavior: open MathBot and send message
  if (askBtn) {
    askBtn.addEventListener('click', (ev) => {
      ev.stopPropagation();
      if (!window.selectedStepText) return;
      const message = `Explain this Beta/Gamma integral step clearly in exam-oriented language: ${window.selectedStepText}`;
      // Open MathBot panel and send message (main.js exposes openMathBot)
      if (typeof window.openMathBot === 'function') {
        window.openMathBot(message);
      } else {
        // fallback: try to show panel and send via elements
        try { window.openMathBot(message); } catch (e) { console.warn('MathBot not available'); }
      }
    });
  }
});
