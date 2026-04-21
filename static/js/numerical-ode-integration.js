document.addEventListener("DOMContentLoaded", () => {
  const problemType = document.getElementById("problemType");
  const odeFields = document.getElementById("odeFields");
  const integrationFields = document.getElementById("integrationFields");
  const solveBtn = document.getElementById("solveBtn");
  const resetBtn = document.getElementById("resetBtn");
  const exampleBtn = document.getElementById("exampleBtn");
  const solutionDiv = document.getElementById("solution");

  // formula toggle (keeps your existing behavior)
  const toggleBtn = document.getElementById("toggleFormula");
  const formulaContent = document.getElementById("formulaContent");
  const dropdownIcon = document.getElementById("dropdownIcon");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      formulaContent.classList.toggle("hidden");
      dropdownIcon.classList.toggle("rotate-180");
      if (!formulaContent.classList.contains("hidden")) {
        setTimeout(() => { if (window.MathJax && window.MathJax.typesetPromise) MathJax.typesetPromise(); }, 120);
      }
    });
  }

  // robust function to determine type: check data-type attribute first
  function getSelectedType() {
    const opt = problemType.options[problemType.selectedIndex];
    if (opt && opt.dataset && opt.dataset.type) return opt.dataset.type; // "ode" or "integration"
    // fallback: old-style check
    return ["euler", "modified_euler", "rk4"].includes(problemType.value) ? "ode" : "integration";
  }

  // show/hide inputs based on selected type
  function updateFields() {
    const type = getSelectedType();
    if (type === "ode") {
      odeFields.style.display = "grid";
      integrationFields.style.display = "none";
    } else {
      odeFields.style.display = "none";
      integrationFields.style.display = "grid";
    }
    // re-render MathJax for any small inline formulas
    if (window.MathJax && window.MathJax.typesetPromise) MathJax.typesetPromise();
    console.log("[UI] updateFields -> type:", type, "method:", problemType.value);
  }

  problemType.addEventListener("change", updateFields);
  updateFields(); // initial

  // fill examples
  exampleBtn.addEventListener("click", () => {
    const method = problemType.value;
    const type = getSelectedType();
    document.getElementById("functionInput").value = "";
    if (type === "ode") {
      // ODE example
      document.getElementById("functionInput").value = "x + y";
      document.getElementById("x0").value = 0;
      document.getElementById("y0").value = 1;
      document.getElementById("h").value = 0.1;
      document.getElementById("xn").value = 0.2;
    } else {
      // integration examples
      if (method === "simpson38") {
        document.getElementById("functionInput").value = "x**3";
        document.getElementById("a").value = 0;
        document.getElementById("b").value = 1;
        document.getElementById("n").value = 3;
      } else {
        // trapezoidal / simpson13
        document.getElementById("functionInput").value = "x**2";
        document.getElementById("a").value = 0;
        document.getElementById("b").value = 1;
        document.getElementById("n").value = 4;
      }
    }
  });

  // reset
  resetBtn.addEventListener("click", () => {
    document.getElementById("functionInput").value = "";
    document.querySelectorAll("#odeFields input, #integrationFields input").forEach(i => i.value = "");
    solutionDiv.innerHTML = "<p>Enter inputs and click Solve.</p>";
    problemType.value = "euler";
    updateFields();
  });

  // Solve: build correct payload and call backend
  solveBtn.addEventListener("click", async () => {
    solutionDiv.innerHTML = "<p>Processing...</p>";
    const method = problemType.value;
    const type = getSelectedType();
    const expr = (document.getElementById("functionInput").value || "").trim();

    if (!expr) {
      solutionDiv.innerHTML = "<p class='text-red-600'>Please enter a function/expression.</p>";
      return;
    }

    let payload = {};
    if (type === "ode") {
      const x0 = parseFloat(document.getElementById("x0").value);
      const y0 = parseFloat(document.getElementById("y0").value);
      const h = parseFloat(document.getElementById("h").value);
      const xn = parseFloat(document.getElementById("xn").value);
      if (![x0, y0, h, xn].every(v => Number.isFinite(v))) {
        solutionDiv.innerHTML = "<p class='text-red-600'>Please enter valid ODE parameters (x0,y0,h,xn).</p>";
        return;
      }
      payload = { action: "ode", payload: { method, expr, x0, y0, h, xn } };
    } else {
      const a = parseFloat(document.getElementById("a").value);
      const b = parseFloat(document.getElementById("b").value);
      const n = parseInt(document.getElementById("n").value);
      if (![a, b].every(v => Number.isFinite(v)) || !Number.isInteger(n) || n <= 0) {
        solutionDiv.innerHTML = "<p class='text-red-600'>Please enter valid integration limits and integer n.</p>";
        return;
      }
      // additional checks for simpson
      if (method === "simpson13" && (n % 2 !== 0)) {
        solutionDiv.innerHTML = "<p class='text-red-600'>Simpson 1/3 requires n to be even.</p>";
        return;
      }
      if (method === "simpson38" && (n % 3 !== 0)) {
        solutionDiv.innerHTML = "<p class='text-red-600'>Simpson 3/8 requires n to be multiple of 3.</p>";
        return;
      }
      payload = { action: "integration", payload: { method, expr, a, b, n } };
    }

    console.log("[API] payload:", payload);

    try {
      const res = await fetch("/api/ode_integration", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!data.success) {
        solutionDiv.innerHTML = `<p class="text-red-600">⚠️ ${data.message}</p>`;
        return;
      }
      // nice rendering
      const stepsHtml = (data.steps || []).map(s => `<div class="solution-step">\\(${s}\\)</div>`).join("");
      solutionDiv.innerHTML = `<div class="space-y-2">${stepsHtml}<div class="solution-step mt-4"><h3 class="font-bold">Result: \\(${data.result}\\)</h3></div></div>`;
      if (window.MathJax && window.MathJax.typesetPromise) MathJax.typesetPromise();
    } catch (err) {
      console.error(err);
      solutionDiv.innerHTML = `<p class='text-red-600'>Server error: ${err.message}</p>`;
    }
  });

  // initial fields setup
  updateFields();
});
