// static/js/partial-diff.js
document.addEventListener('DOMContentLoaded', () => {
  // elements
  const problemType = document.getElementById('problemType');
  const functionInput = document.getElementById('functionInput');
  const solveBtn = document.getElementById('solveBtn');
  const resetBtn = document.getElementById('resetBtn');
  const solutionDiv = document.getElementById('solution');

  const firstInputs = document.getElementById('firstInputs');
  const higherInputs = document.getElementById('higherInputs');
  const subsInputs = document.getElementById('subsInputs');
  const totalDiffInputs = document.getElementById('totalDiffInputs');
  const varTransformInputs = document.getElementById('varTransformInputs');
  const evalInputs = document.getElementById('evalInputs');

  // inputs
  const varInput = document.getElementById('varInput');
  const sequenceInput = document.getElementById('sequenceInput');
  const subsInput = document.getElementById('subsInput');
  const wrtInput = document.getElementById('wrtInput');
  const paramSubsInput = document.getElementById('paramSubsInput');
  const paramInput = document.getElementById('paramInput');
  const transformInput = document.getElementById('transformInput');
  const newCoordsInput = document.getElementById('newCoordsInput');
  const evalAtInput = document.getElementById('evalAtInput');

  function parseKeyValuePairs(str) {
    const pairs = str.split(',').map(s => s.trim()).filter(Boolean);
    const obj = {};
    pairs.forEach(p => {
      const idx = p.indexOf('=');
      if (idx > 0) {
        const k = p.slice(0, idx).trim();
        const v = p.slice(idx + 1).trim();
        if (k && v) obj[k] = v;
      }
    });
    return obj;
  }

  // show/hide UI sections
  function updateUI() {
    const t = problemType.value;
    firstInputs.classList.toggle('hidden', t !== 'first');
    higherInputs.classList.toggle('hidden', t !== 'higher');
    subsInputs.classList.toggle('hidden', !(t === 'composite' || t === 'multi_chain'));
    totalDiffInputs.classList.toggle('hidden', t !== 'total_diff');
    varTransformInputs.classList.toggle('hidden', t !== 'variable_transform');
    evalInputs.classList.toggle('hidden', false); // show eval always (optional)
  }

  problemType.addEventListener('change', updateUI);
  updateUI(); // initial

  // render steps (MathJax friendly)
  function renderResult(data) {
    if (!data) {
      solutionDiv.innerHTML = '<p class="text-red-500">No data returned</p>';
      return;
    }
    // If your backend wraps with {success: true, ...}, adapt as needed
    // Expect data to be the JSON object returned (with "steps" and optional "table")
    const steps = data.steps || [];
    let html = '';
    steps.forEach((s, idx) => {
      // step strings are MathJax-ready; keep them as-is
      html += `<div data-step-index="${idx}" class="solution-step p-3 rounded my-2 cursor-pointer select-text border border-transparent">${s}</div>`;
    });
    if (data.table) {
      html += `<div class="mt-4 overflow-x-auto"><table class="table-auto border-collapse border border-gray-300">`;
      html += `<thead><tr>`;
      data.table.headers.forEach(h => {
        html += `<th class="border border-gray-300 px-2 py-1 bg-gray-50">${h}</th>`;
      });
      html += `</tr></thead><tbody>`;
      data.table.rows.forEach(r => {
        html += `<tr>`;
        r.forEach(cell => {
          // cell expected to be latex or plain string
          html += `<td class="border border-gray-300 px-2 py-1">\\(${cell}\\)</td>`;
        });
        html += `</tr>`;
      });
      html += `</tbody></table></div>`;
    }
    // final result summary if present
    if (data.result) {
      html += `<div class="mt-4"><strong>Result:</strong> <span data-step-index="final" class="solution-step p-2 rounded cursor-pointer select-text border border-transparent">\\(${data.result}\\)</span></div>`;
    }
    solutionDiv.innerHTML = html;
    if (window.MathJax && MathJax.typesetPromise) MathJax.typesetPromise();
  }

  // call backend
  solveBtn.addEventListener('click', async () => {
    const func = functionInput.value.trim();
    if (!func) {
      solutionDiv.innerHTML = `<p class="text-red-600">Please enter a function.</p>`;
      return;
    }

    const mode = problemType.value;
    const payload = { mode, function: func };

    // build mode-specific payload
    if (mode === 'first') {
      payload.var = varInput.value.trim() || 'x';
    } else if (mode === 'higher') {
      const seq = sequenceInput.value.split(',').map(s => s.trim()).filter(Boolean);
      payload.sequence = seq.length ? seq : ['x','x'];
    } else if (mode === 'composite' || mode === 'multi_chain') {
      payload.subs = parseKeyValuePairs(subsInput.value);
      payload.wrt = (wrtInput.value || 'x').trim();
    } else if (mode === 'total_diff') {
      payload.param_subs = parseKeyValuePairs(paramSubsInput.value);
      payload.param = (paramInput.value || 't').trim();
    } else if (mode === 'variable_transform') {
      payload.transform = parseKeyValuePairs(transformInput.value);
      payload.new_coords = newCoordsInput.value.split(',').map(s => s.trim()).filter(Boolean);
    } // euler needs nothing

    // optional numeric evaluation mapping
    const evalStr = evalAtInput.value.trim();
    if (evalStr) payload.evaluate_at = parseKeyValuePairs(evalStr);

    // show loading
    solutionDiv.innerHTML = `<p class="text-gray-600">Computing...</p>`;

    try {
      const resp = await fetch('/api/partial_diff', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await resp.json();
      if (json.success === false) {
        solutionDiv.innerHTML = `<p class="text-red-600">Error: ${json.error || JSON.stringify(json)}</p>`;
        return;
      }
      // the solver result may be returned under the top-level (with success true)
      // if your app returns {"success":true, **result}, json will include type/result/steps
      renderResult(json);
    } catch (err) {
      solutionDiv.innerHTML = `<p class="text-red-600">Network or server error: ${err.message}</p>`;
      console.error(err);
    }
  });


  // reset
  resetBtn.addEventListener('click', () => {
    functionInput.value = '';
    varInput.value = '';
    sequenceInput.value = '';
    subsInput.value = '';
    wrtInput.value = '';
    paramSubsInput.value = '';
    paramInput.value = '';
    transformInput.value = '';
    newCoordsInput.value = '';
    evalAtInput.value = '';
    problemType.value = 'first';
    updateUI();
    solutionDiv.innerHTML = '<p class="text-gray-700">Enter a function and press Solve.</p>';
  });
});
// ============================
// Formula Reference Toggle
// ============================
document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.getElementById('toggleFormula');
    const content = document.getElementById('formulaContent');
    const icon = document.getElementById('dropdownIcon');

    if (toggleBtn && content && icon) {
        toggleBtn.addEventListener('click', function() {
            content.classList.toggle('hidden');
            icon.classList.toggle('rotate-180');

            // Re-render MathJax after showing
            if (!content.classList.contains('hidden') && window.MathJax) {
                MathJax.typesetPromise();
            }
        });
    }
});
