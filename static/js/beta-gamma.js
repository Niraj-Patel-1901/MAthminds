// static/js/beta-gamma.js
document.addEventListener("DOMContentLoaded", () => {
  const integralInput = document.getElementById("integralInput");
  const solveBtn = document.getElementById("solveBtn");
  const tryExampleBtn = document.getElementById("tryExample");
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

  // Wire the example button to the cycling handler
  if (tryExampleBtn) {
    tryExampleBtn.addEventListener('click', onTryExampleClick);
  }

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
      html += `<div><strong>Input:</strong> ${data.input}</div>`;
      if (data.steps && data.steps.length) {
        html += `<div><strong>Steps:</strong><div class="mt-2 space-y-2">`;
        data.steps.forEach((s, i) => {
          html += `<div data-step-index="${i}" class="solution-step p-3 rounded cursor-pointer select-text border border-transparent"><strong>Step ${i+1}:</strong> ${s}</div>`;
        });
        html += `</div></div>`;
      }
      html += `<div><strong>Result:</strong> <div data-step-index="final" class="solution-step p-3 rounded cursor-pointer select-text border border-transparent text-blue-700 font-semibold">\\(${data.result}\\)</div></div>`;
      html += `</div>`;
      solutionDiv.innerHTML = html;
      if (window.MathJax) {
        MathJax.typesetPromise();
      }
    } catch (err) {
      console.error(err);
      solutionDiv.innerHTML = `<p class="text-red-600">Unexpected error: ${err.message}</p>`;
    }
  });

  resetBtn.addEventListener("click", () => {
    integralInput.value = "";
    solutionDiv.innerHTML = '<p>Enter an integral and click Solve. Examples: see buttons above.</p>';
  });
});
