document.addEventListener("DOMContentLoaded", () => {
  const problemType = document.getElementById("problemType");
  const solveBtn = document.getElementById("solveBtn");
  const resetBtn = document.getElementById("resetBtn");
  const exampleBtn = document.getElementById("exampleBtn");
  const solutionDiv = document.getElementById("solution");

  // Formula sheet toggle
  const toggleFormula = document.getElementById("toggleFormula");
  const formulaContent = document.getElementById("formulaContent");
  const dropdownIcon = document.getElementById("dropdownIcon");

  toggleFormula.addEventListener("click", () => {
    formulaContent.classList.toggle("hidden");
    dropdownIcon.classList.toggle("rotate-180");
    if (window.MathJax) MathJax.typesetPromise();
  });

  // Reset button
  resetBtn.addEventListener("click", () => {
    document.querySelectorAll("#inputFields input").forEach(inp => inp.value = "");
    problemType.value = "definition";
    solutionDiv.innerHTML = `<p>Enter a problem and click "Solve" to view step-by-step solution.</p>`;
    if (window.MathJax) MathJax.typesetPromise();
  });

  // Try Example button
  exampleBtn.addEventListener("click", () => {
    const type = problemType.value;
    document.querySelectorAll("#inputFields input").forEach(inp => inp.value = "");

    switch (type) {
      case "definition":
        document.getElementById("functionInput").value = "2**k";
        break;
      case "a_pow_k":
        document.getElementById("a").value = 2;
        break;
      case "k_a_pow_k":
        document.getElementById("a").value = 2;
        break;
      case "a_abs_k":
        document.getElementById("a").value = 0.5;
        break;
      case "C_a_k_plus_n":
        document.getElementById("C").value = 3;
        document.getElementById("a").value = 2;
        document.getElementById("n").value = 1;
        break;
      case "sin_alpha_beta":
        document.getElementById("alpha").value = 0.5;
        document.getElementById("beta").value = 0.2;
        document.getElementById("C").value = 1;
        break;
      case "sinh":
        document.getElementById("alpha").value = 0.3;
        break;
      case "cosh":
        document.getElementById("alpha").value = 0.3;
        break;
      case "scaling":
        document.getElementById("functionInput").value = "2**k";
        document.getElementById("a").value = 3;
        break;
      case "shifting":
        document.getElementById("functionInput").value = "2**k";
        document.getElementById("n").value = 2;
        break;
    }
  });

  // Solve button
  solveBtn.addEventListener("click", async () => {
    const type = problemType.value;
    const func = document.getElementById("functionInput").value.trim();
    const a = document.getElementById("a").value.trim();
    const C = document.getElementById("C").value.trim();
    const n = document.getElementById("n").value.trim();
    const alpha = document.getElementById("alpha").value.trim();
    const beta = document.getElementById("beta").value.trim();

    let payload = {};
    let action = "standard";

    if (type === "definition") {
      action = "definition";
      payload = { expr: func || "a**k" };
    } 
    else if (["a_pow_k", "k_a_pow_k", "a_abs_k", "C_a_k_plus_n", "sin_alpha_beta", "sinh", "cosh"].includes(type)) {
      action = "standard";
      payload = { standard_type: type };
      if (a) payload.a = parseFloat(a);
      if (C) payload.C = parseFloat(C);
      if (n) payload.n = parseFloat(n);
      if (alpha) payload.alpha = parseFloat(alpha);
      if (beta) payload.beta = parseFloat(beta);
    } 
    else if (["scaling", "shifting"].includes(type)) {
      action = "property";
      payload = { property: type, expr: func || "a**k" };
      if (a) payload.a = parseFloat(a);
      if (n) payload.n = parseInt(n);
    }

    try {
      const response = await fetch("/api/z_transform", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, payload })
      });

      const data = await response.json();
      if (!data.success) {
        solutionDiv.innerHTML = `<p class="text-red-600 font-semibold">⚠️ ${data.message}</p>`;
      } else {
        solutionDiv.innerHTML = `
          <div class="space-y-4">
            <h3 class="text-lg font-semibold text-gray-900">Step-by-Step Solution:</h3>
            ${data.steps?.map(s => `<p>\\(${s}\\)</p>`).join("") || ""}
            <h3 class="text-lg font-semibold text-pink-700 mt-4">✅ Final Result:</h3>
            <p class="text-xl">\\(${data.result}\\)</p>
            ${data.roc ? `<p class="text-sm text-gray-600 italic mt-2">ROC: ${data.roc}</p>` : ""}
          </div>
        `;
      }

      if (window.MathJax) MathJax.typesetPromise();
    } catch (err) {
      solutionDiv.innerHTML = `<p class="text-red-600 font-semibold">❌ Server error: ${err.message}</p>`;
    }
  });
});
