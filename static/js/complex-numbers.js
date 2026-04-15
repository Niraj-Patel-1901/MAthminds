// complex-numbers.js
// Put this file in your site JS folder and include it instead of the inline module script.
// Expects MathJax v3 to be loaded on the page.

(function () {
    // Configuration
    const API_URL = '/api/complex/solve'; // blueprint route

    // DOM elements
    const solveBtn = document.getElementById('solveBtn');
    const resetBtn = document.getElementById('resetBtn');
    const problemTypeSelect = document.getElementById('problemType');
    const complex1Input = document.getElementById('complex1');
    const complex2Input = document.getElementById('complex2');
    const powerInput = document.getElementById('power');
    const rootsInput = document.getElementById('roots');
    const solutionDiv = document.getElementById('solution');
    const tryExampleBtn = document.getElementById('tryExample');
    const formulaToggle = document.getElementById('toggleFormula');
    const formulaContent = document.getElementById('formulaContent');

    let selectedStepText = "";
    function setBusy(state) {
        if (state) {
            solveBtn.disabled = true;
            solveBtn.classList.add('opacity-50', 'cursor-wait');
        } else {
            solveBtn.disabled = false;
            solveBtn.classList.remove('opacity-50', 'cursor-wait');
        }
    }

function renderSteps(stepsArr, meta = {}) {
    const container = document.createElement('div');
    container.className = "space-y-4";

    if (meta.sympy_available === false) {
        const warn = document.createElement('div');
        warn.className = "bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded";
        warn.innerHTML = `<strong>Note:</strong> Symbolic expansions require <code>sympy</code>.`;
        container.appendChild(warn);
    }

    stepsArr.forEach((s, index) => {
        const p = document.createElement('div');
        p.className = "prose text-gray-700 p-2 rounded transition";

        // Hover highlight
        p.addEventListener('mouseenter', () => {
            p.classList.add('bg-pink-50', 'cursor-pointer');
        });

        p.addEventListener('mouseleave', () => {
            p.classList.remove('bg-pink-50');
        });

        // Click → select step
        p.addEventListener('click', () => {
            selectedStepText = `Step ${index + 1}: ${s}`;


            document.querySelectorAll('.selected-step')
                .forEach(el => el.classList.remove('selected-step', 'bg-pink-100'));

            p.classList.add('selected-step', 'bg-pink-100');

            const askBtn = document.getElementById('ask-mathbot-btn');
            if (askBtn) askBtn.style.display = 'block';
        });

        // Step numbering (exam-friendly)
        const stepLabel = `<strong>Step ${index + 1}:</strong> `;

        const latexHint = /\\|\\cos|\\sin|\^|_|e\^|theta|pi|\\cdot/.test(s);
        if (latexHint) {
            p.innerHTML = `${stepLabel} \\[ ${s} \\]`;
        } else {
            p.innerHTML = `${stepLabel} ${s}`;
        }

        container.appendChild(p);
    });

    solutionDiv.innerHTML = '';
    solutionDiv.appendChild(container);

    if (window.MathJax && MathJax.typesetPromise) {
        MathJax.typesetPromise();
    }
}


    function showError(errText) {
        solutionDiv.innerHTML = `
            <div class="bg-red-50 border-l-4 border-red-400 p-4 rounded">
                <div class="flex">
                    <div class="flex-shrink-0"><i class="fas fa-exclamation-triangle text-red-400"></i></div>
                    <div class="ml-3">
                        <p class="text-sm text-red-700">${errText}</p>
                    </div>
                </div>
            </div>
        `;
    }

    // Hook up try example (keeps same behavior but dispatches change)
    tryExampleBtn.addEventListener('click', () => {
        const problemType = problemTypeSelect.value;

        if (problemType === 'arithmetic') {
            complex1Input.value = '3+4i';
            complex2Input.value = '1-2i';
            powerInput.value = '';
            rootsInput.value = '';
        } else if (problemType === 'polar') {
            complex1Input.value = '5exp(i*pi/3)';
            complex2Input.value = '';
            powerInput.value = '';
            rootsInput.value = '';
        } else if (problemType === 'demoivre') {
            complex1Input.value = '2+2i';
            complex2Input.value = '';
            powerInput.value = '3';
            rootsInput.value = '';
        }   else if (problemType === 'trig_expand') {
    powerInput.value = '4';
}
        else if (problemType === 'roots') {
            complex1Input.value = '1';
            complex2Input.value = '';
            powerInput.value = '';
            rootsInput.value = '4';
        }

        solutionDiv.innerHTML = `
            <div class="space-y-4">
                <div class="bg-blue-50 border-l-4 border-blue-400 p-4">
                    <div class="flex">
                        <div class="flex-shrink-0">
                            <i class="fas fa-info-circle text-blue-400"></i>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-blue-700">
                                <strong>Example loaded!</strong> This is a sample ${problemType} problem.
                                Click "Solve" to see the step-by-step solution.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    // Solve — call backend API
    solveBtn.addEventListener('click', async () => {
        selectedStepText = "";
const askBtn = document.getElementById('ask-mathbot-btn');
if (askBtn) askBtn.style.display = 'none';
        const payload = {
            problemType: problemTypeSelect.value,
            complex1: complex1Input.value,
            complex2: complex2Input.value,
            power: powerInput.value,
            roots: rootsInput.value
        };
        setBusy(true);
        try {
            const resp = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await resp.json();
            if (!data.ok) {
                const err = data.error || 'Server returned an error.';
                showError(err);
                setBusy(false);
                return;
            }
            // Render steps
            const steps = data.steps || [];
            renderSteps(steps, { sympy_available: data.sympy_available });
            // Optionally show a brief result summary
            if (data.result) {
                // append a compact card with final results
                const resCard = document.createElement('div');
                resCard.className = "mt-4 bg-gray-50 p-4 rounded";
                let html = `<h4 class="font-semibold">Result summary</h4><ul class="mt-2 space-y-1 text-sm text-gray-700">`;
                if (data.result.power !== undefined) {
                    html += `<li>Power (n): ${data.result.power} — Result: \\(${data.result.result_cartesian || ''}\\)</li>`;
                } else if (data.result.roots) {
                    html += `<li>${data.result.roots.length} roots computed.</li>`;
                } else if (data.result.polar) {
                    html += `<li>Polar: \\(${data.result.polar}\\)</li><li>Exponential: \\(${data.result.exponential}\\)</li>`;
                } else if (data.result.addition) {
                    html += `<li>Addition: \\(${data.result.addition.latex}\\)</li>`;
                    html += `<li>Multiplication: \\(${data.result.multiplication.latex}\\)</li>`;
                }
                html += `</ul>`;
                resCard.innerHTML = html;
                solutionDiv.appendChild(resCard);
                if (window.MathJax && MathJax.typesetPromise) MathJax.typesetPromise();
            }
        } catch (err) {
            console.error(err);
            showError('Network or server error. Check console for details.');
        } finally {
            setBusy(false);
        }
    });

    resetBtn.addEventListener('click', () => {
    problemTypeSelect.value = 'arithmetic';
    complex1Input.value = '';
    complex2Input.value = '';
    powerInput.value = '';
    rootsInput.value = '';
    solutionDiv.innerHTML = '<p class="text-gray-700">Enter complex numbers to perform calculations.</p>';

    const askBtn = document.getElementById('ask-mathbot-btn');
    if (askBtn) askBtn.style.display = 'none';
    selectedStepText = "";

    problemTypeSelect.dispatchEvent(new Event('change'));
});

    // Show/hide inputs based on problem type
    problemTypeSelect.addEventListener('change', () => {
        const type = problemTypeSelect.value;
        // second complex only for arithmetic
            document.getElementById('power-wrapper').style.display =
        (type === 'demoivre' || type === 'trig_expand') ? 'block' : 'none';

    document.getElementById('roots-wrapper').style.display =
        (type === 'roots') ? 'block' : 'none';
        if (complex2Input && complex2Input.parentElement) {
            complex2Input.parentElement.style.display = (type === 'arithmetic') ? 'block' : 'none';
        }

    });

    // Formula sheet toggle: re-typeset math when opened
    if (formulaToggle && formulaContent) {
        formulaToggle.addEventListener('click', () => {
            formulaContent.classList.toggle('hidden');
            const icon = document.getElementById('dropdownIcon');
            if (icon) icon.classList.toggle('rotate-180');
            if (!formulaContent.classList.contains('hidden') && window.MathJax && MathJax.typesetPromise) {
                MathJax.typesetPromise().catch(() => {});
            }
        });
    }

    // Initial setup
    document.addEventListener('DOMContentLoaded', () => {
        problemTypeSelect.dispatchEvent(new Event('change'));
    });
const askMathBotBtn = document.getElementById('ask-mathbot-btn');

if (askMathBotBtn) {
    askMathBotBtn.addEventListener('click', () => {
        if (!selectedStepText || selectedStepText.trim() === "") {
    alert("Please select a step first.");
    return;
}

        // This function already exists in main.js
        openMathBot(
            `Explain this mathematical step clearly with reasoning:\n\n${selectedStepText}`
        );
    });
}

})();
// complex-numbers.js
// Put this file in your site JS folder and include it instead of the inline module script.
// Expects MathJax v3 to be loaded on the page.

