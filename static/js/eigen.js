/**
 * eigen.js
 * Reworked to produce Tailwind-styled matrix inputs and UI behaviour.
 * Expects an API POST to /api/linear-algebra that returns JSON:
 * { success: true, steps: [...html strings...] } or { success: false, error: "..." }
 *
 * Replace your existing static/js/eigen.js with this (or merge).
 */

(function () {
  // --- Helpers ---
  function el(id) { return document.getElementById(id); }

  function createInput(row, col) {
    const input = document.createElement('input');
    input.type = 'number';
    input.step = 'any';
    input.inputMode = 'decimal';
    input.setAttribute('aria-label', `matrix entry r${row+1}c${col+1}`);
    input.dataset.r = row;
    input.dataset.c = col;
    input.className = 'matrix-input w-20 p-2 text-center rounded border focus:outline-none focus:ring-2 focus:ring-purple-200';
    input.value = '0';
    return input;
  }

  // Renders a matrix grid into containerId with given size (n x n)
  function renderMatrixGrid(containerId, size) {
    const container = el(containerId);
    container.innerHTML = '';

    const gridWrap = document.createElement('div');
    gridWrap.className = 'w-full flex justify-center';

    const grid = document.createElement('div');
    grid.className = 'grid gap-2';
    grid.style.gridTemplateColumns = `repeat(${size}, minmax(3rem, 5rem))`;

    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        const input = createInput(r, c);
        grid.appendChild(input);
      }
    }

    gridWrap.appendChild(grid);
    container.appendChild(gridWrap);
  }

  function readMatrixFromContainer(containerId) {
    const container = el(containerId);
    const inputs = container.querySelectorAll('input[data-r][data-c]');
    if (!inputs || inputs.length === 0) return [];
    // find size (square)
    const maxR = Math.max(...Array.from(inputs).map(i => Number(i.dataset.r)));
    const size = maxR + 1;
    const matrix = Array.from({ length: size }, () => Array(size).fill(0));
    inputs.forEach(inp => {
      const r = Number(inp.dataset.r);
      const c = Number(inp.dataset.c);
      const raw = inp.value.trim();
      const num = raw === '' ? 0 : Number(raw);
      matrix[r][c] = Number.isFinite(num) ? num : raw;
    });
    return matrix;
  }

  // Fill an example matrix (2x2 or 3x3)
  function fillExampleForSize(size) {
    const examples = {
      2: {
        A: [[3, 1], [0, 2]],
        B: [[1, 0], [0, 1]]
      },
      3: {
        A: [[4, 2, 1], [0, 3, -1], [2, 0, 5]],
        B: [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
      }
    };
    const ex = examples[size] || examples[2];

    // fill A
    const aInputs = el('matrixA').querySelectorAll('input[data-r][data-c]');
    aInputs.forEach(inp => {
      const r = Number(inp.dataset.r), c = Number(inp.dataset.c);
      if (ex.A[r] && typeof ex.A[r][c] !== 'undefined') inp.value = ex.A[r][c];
      else inp.value = 0;
    });

    // fill B if visible
    if (!el('matrixBContainer').classList.contains('hidden')) {
      const bInputs = el('matrixB').querySelectorAll('input[data-r][data-c]');
      bInputs.forEach(inp => {
        const r = Number(inp.dataset.r), c = Number(inp.dataset.c);
        if (ex.B[r] && typeof ex.B[r][c] !== 'undefined') inp.value = ex.B[r][c];
        else inp.value = 0;
      });
    }
  }

  // Reset matrices to zeros
  function resetMatrices() {
    const allInputs = document.querySelectorAll('.matrix-input');
    allInputs.forEach(inp => inp.value = '0');
    const sol = el('solution');
    sol.innerHTML = '<p>Enter a matrix and click <strong>Solve</strong> to see steps here.</p>';
    if (window.MathJax) MathJax.typesetPromise?.();
  }

  // UI update: show/hide matrix B and re-render grids based on current size and task
  function updateMatrixInputs() {
    const size = Number(el('matrixSize').value) || 2;
    const task = el('taskSelect').value;

    renderMatrixGrid('matrixA', size);

    if (task === 'similarity') {
      el('matrixBContainer').classList.remove('hidden');
      renderMatrixGrid('matrixB', size);
    } else {
      el('matrixBContainer').classList.add('hidden');
      el('matrixB').innerHTML = '';
    }
  }

  // Show a short inline message or HTML in solution area
  function setSolutionHTMLFromSteps(stepsArray) {
  if (!Array.isArray(stepsArray) || stepsArray.length === 0) {
    setSolutionHTML('<p>No steps returned from server.</p>');
    return;
  }
  const items = stepsArray.map(s => `<li class="leading-relaxed">${s}</li>`).join('');
  const html = `<ol class="list-decimal pl-6 space-y-1">${items}</ol>`;
  setSolutionHTML(html);
}

function setSolutionHTML(html) {
  const sol = document.getElementById('solution');
  sol.innerHTML = html;
  if (window.MathJax) {
    if (MathJax.typesetPromise) MathJax.typesetPromise();
    else MathJax.typeset?.();
  }
}

  // Main solve: reads matrices and posts to backend
  async function solveMatrix() {
    try {
      const size = Number(el('matrixSize').value) || 2;
      const task = el('taskSelect').value;

      const payload = {
        task: task,
        size: size,
        A: readMatrixFromContainer('matrixA')
      };

      if (task === 'similarity') {
        payload.B = readMatrixFromContainer('matrixB');
      }

      // UI: disable solve and show spinner
      const solveBtn = el('solveBtn');
      const origHTML = solveBtn.innerHTML;
      solveBtn.disabled = true;
      solveBtn.classList.add('opacity-70', 'cursor-not-allowed');
      solveBtn.innerHTML = `<svg class="animate-spin h-5 w-5 mr-2 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a12 12 0 00-12 12h4z"></path></svg> Computing...`;

      // POST
      const res = await fetch('/api/linear-algebra', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const text = await res.text();
        setSolutionHTML(`<p class="text-red-600">Server error: ${res.status} ${res.statusText}</p><pre class="mt-2 bg-gray-100 p-2 rounded">${escapeHtml(text)}</pre>`);
        return;
      }

      const data = await res.json();

      if (!data.success) {
        setSolutionHTML(`<p class="text-red-600">Error: ${escapeHtml(data.error || 'Unknown error')}</p>`);
      } else {
        // Expect data.steps to be array of HTML strings or a single string
        if (Array.isArray(data.steps)) {
  setSolutionHTMLFromSteps(data.steps);
} else if (typeof data.steps === 'string') {
  setSolutionHTML(data.steps);
} else if (data.result) {
  setSolutionHTML(String(data.result));
} else {
  setSolutionHTML('<p>No steps returned from server.</p>');
}
      }
    } catch (err) {
      setSolutionHTML(`<p class="text-red-600">Request failed: ${escapeHtml(err.message || String(err))}</p>`);
    } finally {
      // restore button
      const solveBtn = el('solveBtn');
      solveBtn.disabled = false;
      solveBtn.classList.remove('opacity-70', 'cursor-not-allowed');
      solveBtn.innerHTML = '<i class="fas fa-calculator"></i> Solve';
    }
  }

  // Escape HTML for safe text display
  function escapeHtml(unsafe) {
    return String(unsafe)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  // --- Bind events on DOMContentLoaded ---
  document.addEventListener('DOMContentLoaded', () => {
    // element refs
    const taskSelect = el('taskSelect');
    const matrixSize = el('matrixSize');
    const exampleBtn = el('exampleBtn');
    const resetBtn = el('resetBtn');
    const solveBtn = el('solveBtn');

    // initial render
    updateMatrixInputs();

    // change handlers
    taskSelect.addEventListener('change', updateMatrixInputs);
    matrixSize.addEventListener('change', updateMatrixInputs);

    // Try example
    exampleBtn.addEventListener('click', () => {
      const size = Number(el('matrixSize').value) || 2;
      fillExampleForSize(size);
      setSolutionHTML('<p class="text-gray-700">Example loaded. Click <strong>Solve</strong> to compute steps.</p>');
    });

    // Reset
    resetBtn.addEventListener('click', () => {
      updateMatrixInputs();
      resetMatrices();
    });

    // Solve
    solveBtn.addEventListener('click', () => {
      setSolutionHTML('<p class="text-gray-700">Computing — please wait...</p>');
      solveMatrix();
    });

    // Accessibility: Enter on any input triggers Solve (optional)
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        solveBtn.click();
      }
    });
  });
})();
