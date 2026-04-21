document.addEventListener("DOMContentLoaded", () => {
  const methodSelect = document.getElementById("method");
  const functionContainer = document.getElementById("functionContainer");
  const initialGuessContainer = document.getElementById("initialGuessContainer");
  const intervalContainer = document.getElementById("intervalContainer");
  const matrixContainer = document.getElementById("matrixContainer");

  const solveBtn = document.getElementById("solveBtn");
  const resetBtn = document.getElementById("resetBtn");
  const exampleBtn = document.getElementById("exampleBtn");
  const solutionDiv = document.getElementById("solution");

  const updateFields = () => {
    const method = methodSelect.value;
    functionContainer.classList.toggle("hidden", method === "gauss_jacobi" || method === "gauss_seidel");
    initialGuessContainer.classList.toggle("hidden", method !== "newton");
    intervalContainer.classList.toggle("hidden", method !== "regula_falsi");
    matrixContainer.classList.toggle("hidden", method !== "gauss_jacobi" && method !== "gauss_seidel");
  };

  methodSelect.addEventListener("change", updateFields);
  updateFields();

  solveBtn.addEventListener("click", async () => {
    const method = methodSelect.value;
    const tol = parseFloat(document.getElementById("tolerance").value) || 1e-6;
    const maxIter = parseInt(document.getElementById("maxIter").value) || 50;
    let payload = {};

    try {
      if (method === "newton") {
        payload = {
          expr: document.getElementById("functionInput").value,
          x0: parseFloat(document.getElementById("initialGuess").value),
          tol,
          max_iter: maxIter
        };
      } else if (method === "regula_falsi") {
        payload = {
          expr: document.getElementById("functionInput").value,
          a: parseFloat(document.getElementById("aValue").value),
          b: parseFloat(document.getElementById("bValue").value),
          tol,
          max_iter: maxIter
        };
      } else {
        payload = {
          A: JSON.parse(document.getElementById("matrixA").value),
          b: JSON.parse(document.getElementById("vectorB").value),
          tol,
          max_iter: maxIter
        };
      }
    } catch (err) {
      solutionDiv.innerHTML = `<p style="color:red;">Invalid input: ${err}</p>`;
      return;
    }

    solutionDiv.innerHTML = `<p class="text-gray-500">⏳ Solving... Please wait.</p>`;

    try {
      const res = await fetch("/api/numerical", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ method, payload })
      });
      const data = await res.json();

      if (!data.success) {
        solutionDiv.innerHTML = `<p style="color:red;">${data.message}</p>`;
        return;
      }

      solutionDiv.innerHTML = `
        <h3 class="font-semibold text-green-700">${data.message}</h3>
        ${data.warning ? `<p style="color:orange;"><strong>⚠ ${data.warning}</strong></p>` : ""}
        ${data.latex_steps.map(step => `<div class="solution-step">$$${step}$$</div>`).join("")}
      `;
      if (window.MathJax) MathJax.typeset();
    } catch (err) {
      solutionDiv.innerHTML = `<p style="color:red;">Error contacting server: ${err}</p>`;
    }
  });

  resetBtn.addEventListener("click", () => {
    document.getElementById("functionInput").value = "";
    document.getElementById("initialGuess").value = "";
    document.getElementById("aValue").value = "";
    document.getElementById("bValue").value = "";
    document.getElementById("matrixA").value = "";
    document.getElementById("vectorB").value = "";
    document.getElementById("tolerance").value = "";
    document.getElementById("maxIter").value = "";
    solutionDiv.innerHTML = `<p class="text-gray-700">Enter inputs and click "Solve" to see the step-by-step solution.</p>`;
    updateFields();
  });

  exampleBtn.addEventListener("click", () => {
    const method = methodSelect.value;
    if (method === "newton") {
      document.getElementById("functionInput").value = "x**3 - 2*x - 5";
      document.getElementById("initialGuess").value = "2";
    } else if (method === "regula_falsi") {
      document.getElementById("functionInput").value = "x**3 - x - 2";
      document.getElementById("aValue").value = "1";
      document.getElementById("bValue").value = "2";
    } else {
      document.getElementById("matrixA").value = "[[4,-1,0],[-1,4,-1],[0,-1,4]]";
      document.getElementById("vectorB").value = "[15,10,10]";
    }
  });

  // Formula sheet toggle
  document.getElementById("toggleFormula").addEventListener("click", () => {
    const content = document.getElementById("formulaContent");
    const icon = document.getElementById("dropdownIcon");
    content.classList.toggle("hidden");
    icon.classList.toggle("rotate-180");
    if (!content.classList.contains("hidden") && window.MathJax) {
      MathJax.typeset();
    }
  });
});
