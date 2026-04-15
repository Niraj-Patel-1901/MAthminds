// matrices.js - Externalized matrix UI and MathBot integration
// Assumes TailwindCSS and MathJax v3 are available.
(function () {
    'use strict';

    // State
    let numRows = 2, numCols = 2;
    let numRowsB = 2, numColsB = 2;
    let selectedStepText = '';

    // Helpers
    function qs(sel) { return document.querySelector(sel); }
    function qsa(sel) { return Array.from(document.querySelectorAll(sel)); }

    // Create CSS for steps hover/active and ask button placement using CSS variables
    function injectStyles() {
        const css = `
            .solution-step { transition: background-color .12s, border-color .12s; }
            .solution-step:hover { background-color: rgba(236, 72, 153, 0.12); }
            .solution-step.active { background-color: rgba(236, 72, 153, 0.24); border-color: rgba(236,72,153,.4); }
            /* Use fixed positioning so placement is relative to viewport (stable) */
            #ask-mathbot-btn { position: fixed; left: var(--ask-mathbot-left, 0px); top: var(--ask-mathbot-top, 0px); z-index: 9999; }
        `;
        const style = document.createElement('style');
        style.setAttribute('data-generated-by','matrices.js');
        style.appendChild(document.createTextNode(css));
        document.head.appendChild(style);
    }

    // Render matrix grid for a given element id
    function renderMatrixGrid(gridId, rows, cols) {
        const grid = document.getElementById(gridId);
        if (!grid) return;
        let html = '<div class="grid gap-2" style="grid-template-columns:repeat(' + cols + ',minmax(2.5rem,1fr));">';
        for (let i = 0; i < rows; i++) {
            for (let j = 0; j < cols; j++) {
                html += `<input type='text' class='math-input w-16 text-center' id='${gridId}_${i}_${j}' placeholder='${gridId === "matrixGridA" ? "A" : "B"}${i+1}${j+1}'>`;
            }
        }
        html += '</div>';
        grid.innerHTML = html;
    }

    // Update matrix visibility based on selections
    function updateMatrixVisibility() {
        const problemTypeSelect = qs('#problemType');
        const operationSelect = qs('#operation');
        const matrixAWrapper = qs('#matrixAWrapper');
        const matrixBWrapper = qs('#matrixBWrapper');
        const operationDiv = qs('#operationDiv');
        const typeCheckDiv = qs('#typeCheckDiv');
        const scalarDiv = qs('#scalarDiv');
        const typeCheckConstantDiv = qs('#typeCheckConstantDiv');

        const type = problemTypeSelect.value;
        if (type === 'operations') {
            operationDiv.style.display = 'block';
            typeCheckDiv.style.display = 'none';
            matrixAWrapper.style.display = 'block';
            const op = operationSelect.value;
            if (["add","subtract","multiply"].includes(op)) {
                matrixBWrapper.style.display = 'block';
            } else {
                matrixBWrapper.style.display = 'none';
            }
            if (op === 'scalar') scalarDiv.style.display = 'block'; else scalarDiv.style.display = 'none';
            typeCheckConstantDiv.style.display = 'none';
        } else if (type === 'typecheck') {
            operationDiv.style.display = 'none';
            typeCheckDiv.style.display = 'block';
            matrixAWrapper.style.display = 'block';
            matrixBWrapper.style.display = 'none';
            scalarDiv.style.display = 'none';
            typeCheckConstantDiv.style.display = 'block';
        } else {
            operationDiv.style.display = 'none';
            typeCheckDiv.style.display = 'none';
            matrixAWrapper.style.display = 'block';
            matrixBWrapper.style.display = 'none';
            scalarDiv.style.display = 'none';
            typeCheckConstantDiv.style.display = 'none';
        }
    }

    // Position the ask button using CSS variables (no inline style on the button itself)
    function positionAskButton(x, y) {
        document.documentElement.style.setProperty('--ask-mathbot-left', x + 'px');
        document.documentElement.style.setProperty('--ask-mathbot-top', y + 'px');
    }

    // Show Ask MathBot button near an element
    function showAskButtonNear(stepEl) {
        const askBtn = qs('#ask-mathbot-btn');
        if (!askBtn) return;
        // Compute position using viewport coordinates (fixed positioning)
        const rect = stepEl.getBoundingClientRect();
        const gap = 8;
        // Measure button size; if it's hidden, offsetWidth may be 0 — use sensible defaults
        const btnWidth = askBtn.offsetWidth || 120;
        const btnHeight = askBtn.offsetHeight || 36;
        let left = rect.right + gap;
        // If placing right would overflow viewport, place to left of element
        if (left + btnWidth > window.innerWidth - 8) {
            left = rect.left - (btnWidth + gap);
        }
        const top = rect.top + (rect.height - btnHeight) / 2;
        const finalLeft = Math.max(8, Math.round(left));
        const finalTop = Math.max(8, Math.round(top));
        positionAskButton(finalLeft, finalTop);
        console.log('[matrices.js] showAskButtonNear:', { left: finalLeft, top: finalTop, btnWidth, btnHeight });
        // Ensure button is visible: remove utility hiding classes and force inline display/position
        askBtn.classList.remove('hidden', 'invisible', 'opacity-0');
        askBtn.classList.add('inline-flex');
        askBtn.setAttribute('aria-hidden', 'false');
        askBtn.style.pointerEvents = 'auto';
        // Force inline styles to override any CSS that may keep it hidden
        askBtn.style.position = 'fixed';
        askBtn.style.left = finalLeft + 'px';
        askBtn.style.top = finalTop + 'px';
        askBtn.style.display = 'inline-flex';
        askBtn.style.visibility = 'visible';
        askBtn.style.opacity = '1';
        askBtn.style.zIndex = '9999';
        // Ensure the button is in the document body (avoid clipping by transformed ancestors)
        if (askBtn.parentElement !== document.body) {
            document.body.appendChild(askBtn);
            console.log('[matrices.js] ask button appended to body');
        }
    }

    // Attach click handlers for steps using event delegation
    function attachStepClickHandlers() {
        console.log('[matrices.js] attachStepClickHandlers() called');
        const solutionDiv = qs('#solution');
        if (!solutionDiv) return;
        solutionDiv.addEventListener('click', function (e) {
            const stepEl = e.target.closest('.solution-step');
            if (!stepEl) return;
            // Remove previous active classes
            qsa('.solution-step').forEach(el => el.classList.remove('active'));
            stepEl.classList.add('active');
            // Store selected text
            selectedStepText = stepEl.innerText || stepEl.textContent || '';
            console.log('[matrices.js] step clicked:', selectedStepText);
            // Show ask button near this step
            showAskButtonNear(stepEl);
        });
    }

    // Open MathBot, inject message and send
    function openMathBot(message) {
        const toggle = qs('#mathbot-toggle');
        const input = qs('#mathbot-input');
        const send = qs('#mathbot-send');
        if (toggle) {
            try { toggle.click(); } catch (e) { /* ignore */ }
        }
        if (!input) return;
        input.focus();
        input.value = message;
        // Fire input events to ensure frameworks pick up the change
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        if (send) {
            try { send.click(); } catch (e) { /* ignore */ }
        }
    }

    // Initialize and wire up UI
    document.addEventListener('DOMContentLoaded', () => {
        console.log('[matrices.js] DOMContentLoaded');
        injectStyles();

        const matrixAWrapper = qs('#matrixAWrapper');
        const matrixBWrapper = qs('#matrixBWrapper');
        const problemTypeSelect = qs('#problemType');
        const operationSelect = qs('#operation');
        const solveBtn = qs('#solveBtn');
        const resetBtn = qs('#resetBtn');
        const solutionDiv = qs('#solution');
        const tryExampleBtn = qs('#tryExample');

        // Initial render
        renderMatrixGrid('matrixGridA', numRows, numCols);
        renderMatrixGrid('matrixGridB', numRowsB, numColsB);
        if (matrixBWrapper) matrixBWrapper.style.display = 'none';

        // Row/Col handlers
        qs('#addRow').addEventListener('click', () => { numRows++; numRowsB++; renderMatrixGrid('matrixGridA', numRows, numCols); renderMatrixGrid('matrixGridB', numRowsB, numColsB); });
        qs('#removeRow').addEventListener('click', () => { if (numRows>1) { numRows--; numRowsB--; renderMatrixGrid('matrixGridA', numRows, numCols); renderMatrixGrid('matrixGridB', numRowsB, numColsB); } });
        qs('#addCol').addEventListener('click', () => { numCols++; numColsB++; renderMatrixGrid('matrixGridA', numRows, numCols); renderMatrixGrid('matrixGridB', numRowsB, numColsB); });
        qs('#removeCol').addEventListener('click', () => { if (numCols>1) { numCols--; numColsB--; renderMatrixGrid('matrixGridA', numRows, numCols); renderMatrixGrid('matrixGridB', numRowsB, numColsB); } });

        // Visibility updates
        if (problemTypeSelect) problemTypeSelect.addEventListener('change', updateMatrixVisibility);
        if (operationSelect) operationSelect.addEventListener('change', updateMatrixVisibility);
        updateMatrixVisibility();

        // Try Example
        if (tryExampleBtn) tryExampleBtn.addEventListener('click', () => {
            const problemType = problemTypeSelect.value;
            if (problemType === 'operations') {
                numRows = 2; numCols = 2; numRowsB = 2; numColsB = 2;
                renderMatrixGrid('matrixGridA', numRows, numCols); renderMatrixGrid('matrixGridB', numRowsB, numColsB);
                const exampleA = [[2,1],[3,4]]; const exampleB = [[1,2],[0,1]];
                for(let i=0;i<2;i++) for(let j=0;j<2;j++){ qs(`#matrixGridA_${i}_${j}`).value = exampleA[i][j]; qs(`#matrixGridB_${i}_${j}`).value = exampleB[i][j]; }
                operationSelect.value = 'add'; if (matrixBWrapper) matrixBWrapper.style.display = 'block';
            } else if (problemType === 'determinant') {
                numRows = 3; numCols = 3; numRowsB = 3; numColsB = 3; renderMatrixGrid('matrixGridA', numRows, numCols); renderMatrixGrid('matrixGridB', numRowsB, numColsB);
                const example = [[2,1,3],[1,0,2],[4,1,5]]; for(let i=0;i<3;i++) for(let j=0;j<3;j++) qs(`#matrixGridA_${i}_${j}`).value = example[i][j]; if (matrixBWrapper) matrixBWrapper.style.display = 'none';
            } else if (problemType === 'echelon') {
                numRows = 3; numCols = 4; numRowsB = 3; numColsB = 4; renderMatrixGrid('matrixGridA', numRows, numCols); renderMatrixGrid('matrixGridB', numRowsB, numColsB);
                const example = [[1,2,3,4],[2,4,6,8],[1,1,1,1]]; for(let i=0;i<3;i++) for(let j=0;j<4;j++) qs(`#matrixGridA_${i}_${j}`).value = example[i][j]; if (matrixBWrapper) matrixBWrapper.style.display = 'none';
            } else if (problemType === 'paq') {
                numRows = 3; numCols = 3; numRowsB = 3; numColsB = 3; renderMatrixGrid('matrixGridA', numRows, numCols); renderMatrixGrid('matrixGridB', numRowsB, numColsB);
                const example = [[0,1,2],[1,0,1],[2,1,0]]; for(let i=0;i<3;i++) for(let j=0;j<3;j++) qs(`#matrixGridA_${i}_${j}`).value = example[i][j]; if (matrixBWrapper) matrixBWrapper.style.display = 'none';
            } else if (problemType === 'typecheck') {
                numRows = 2; numCols = 2; numRowsB = 2; numColsB = 2; renderMatrixGrid('matrixGridA', numRows, numCols); renderMatrixGrid('matrixGridB', numRowsB, numColsB);
                const example = [[1,2],[2,1]]; for(let i=0;i<2;i++) for(let j=0;j<2;j++) qs(`#matrixGridA_${i}_${j}`).value = example[i][j]; if (matrixBWrapper) matrixBWrapper.style.display = 'none';
            }
            solutionDiv.innerHTML = `<div class="space-y-4"><div class="bg-blue-50 border-l-4 border-blue-400 p-4"><div class="flex"><div class="flex-shrink-0"><i class="fas fa-info-circle text-blue-400"></i></div><div class="ml-3"><p class="text-sm text-blue-700"><strong>Example loaded!</strong> This is a sample ${problemType} problem. You can modify the values or try solving it as-is.</p></div></div></div><p class="text-gray-700">Click "Solve" to see the step-by-step solution.</p></div>`;
            problemTypeSelect.dispatchEvent(new Event('change'));
        });

        // Solve button
        if (solveBtn) solveBtn.addEventListener('click', () => {
            const problemType = problemTypeSelect.value;
            const matrixA = [];
            const matrixB = [];
            for (let i=0;i<numRows;i++){
                const row = [];
                for (let j=0;j<numCols;j++) row.push(qs(`#matrixGridA_${i}_${j}`)?.value || '');
                matrixA.push(row);
            }
            if (matrixBWrapper && matrixBWrapper.style.display !== 'none'){
                for (let i=0;i<numRowsB;i++){
                    const row = [];
                    for (let j=0;j<numColsB;j++) row.push(qs(`#matrixGridB_${i}_${j}`)?.value || '');
                    matrixB.push(row);
                }
            }
            const operation = operationSelect ? operationSelect.value : null;
            // Validation: determinant/inverse require square
            if ((problemType === 'operations' && operation === 'inverse') || problemType === 'determinant'){
                if (numRows !== numCols) {
                    solutionDiv.innerHTML = `<div class='text-red-600 font-semibold'>Error: For inverse and determinant, matrix A must be square.</div>`;
                    return;
                }
            }

            let payload = { type: problemType, A: matrixA, operation };
            if (matrixB.length) payload.B = matrixB;
            if (problemType === 'typecheck') {
                payload.typeCheck = qs('#typeCheck')?.value || 'all';
                payload.typeCheckConstant = qs('#typeCheckConstantInput')?.value || '1';
            }
            if (problemType === 'operations' && operation === 'scalar') payload.scalar = qs('#scalarInput')?.value || '1';

            solutionDiv.innerHTML = 'Solving...';
            fetch('/api/matrix', {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
            })
            .then(r => r.json())
            .then(data => {
                if (!data || !data.success) {
                    solutionDiv.innerHTML = `<div class='text-red-600 font-semibold'>${(data && (data.error || data.error_message)) || 'Unknown error'}</div>`;
                    return;
                }

                const steps = data.steps || [];
                const stepsHtml = steps.map((s,i) => `<div class="step-block solution-step border border-transparent p-3 rounded my-2 cursor-pointer select-text" data-step-index="${i}">\\(${s}\\)</div>`).join('');

                // Special renderings follow the existing patterns
                if (problemType === 'paq'){
                    let paqDetails = '';
                    if (data.P) paqDetails += `<div>P: \\(${data.P}\\)</div>`;
                    if (data.Q) paqDetails += `<div>Q: \\(${data.Q}\\)</div>`;
                    if (data.rank !== undefined) paqDetails += `<div>Rank: ${data.rank}</div>`;
                    if (data.inverse_latex) paqDetails += `<div>Inverse: \\(${data.inverse_latex}\\)</div>`;
                    solutionDiv.innerHTML = `
                        <div class="space-y-2">
                            <div>PAQ Result: \\(${data.result_latex || ''}\\)</div>
                            ${paqDetails}
                            <div>
                                <strong>Steps:</strong>
                                <div id="solution-steps">${stepsHtml}</div>
                            </div>
                        </div>
                    `;
                } else if (problemType === 'determinant'){
                    let invHtml = data.inverse_latex ? `<div>Inverse: \\(${data.inverse_latex}\\)</div>` : '';
                    solutionDiv.innerHTML = `
                        <div class="space-y-2">
                            <div>Determinant: \\(${data.result_latex || ''}\\)</div>
                            ${invHtml}
                            <div>
                                <strong>Steps:</strong>
                                <div id="solution-steps">${stepsHtml}</div>
                            </div>
                        </div>
                    `;
                } else if (problemType === 'typecheck' && data.solutions){
                    const solHtml = `<div>Solutions: <pre>${JSON.stringify(data.solutions, null, 2)}</pre></div>`;
                    solutionDiv.innerHTML = `
                        <div class="space-y-2">
                            <div>Result: \\(${data.result_latex || ''}\\)</div>
                            ${solHtml}
                            <div>
                                <strong>Steps:</strong>
                                <div id="solution-steps">${stepsHtml}</div>
                            </div>
                        </div>
                    `;
                } else {
                    solutionDiv.innerHTML = `
                        <div class="space-y-2">
                            <div>Result: \\(${data.result_latex || ''}\\)</div>
                            <div>
                                <strong>Steps:</strong>
                                <div id="solution-steps">${stepsHtml}</div>
                            </div>
                        </div>
                    `;
                }

                // Typeset MathJax and attach handlers after DOM update
                if (window.MathJax && window.MathJax.typesetPromise) {
                    window.MathJax.typesetPromise().then(() => {
                        attachStepClickHandlers();
                    }).catch(() => { attachStepClickHandlers(); });
                } else {
                    attachStepClickHandlers();
                }
            })
            .catch(err => { solutionDiv.innerHTML = `<div class='text-red-600 font-semibold'>${err}</div>`; });
        });

        // Reset
        if (resetBtn) resetBtn.addEventListener('click', () => {
            problemTypeSelect.value = 'operations';
            if (operationSelect) operationSelect.value = 'add';
            qs('#typeCheck').value = 'all';
            numRows = 2; numCols = 2; numRowsB = 2; numColsB = 2;
            renderMatrixGrid('matrixGridA', numRows, numCols); renderMatrixGrid('matrixGridB', numRowsB, numColsB);
            if (matrixBWrapper) matrixBWrapper.style.display = 'none';
            solutionDiv.innerHTML = '<p class="text-gray-700">Enter matrices to perform operations.</p>';
            problemTypeSelect.dispatchEvent(new Event('change'));
        });

        // Ask MathBot button behavior
        const askBtn = qs('#ask-mathbot-btn');
        if (askBtn) {
            // Helper: stringify matrices for MathBot prompt
            function matrixToString(mat) {
                if (!mat || !mat.length) return 'N/A';
                return mat.map(r => '[' + r.join(', ') + ']').join('\n');
            }

            function gatherMatrixContext() {
                const type = qs('#problemType')?.value || '';
                const op = qs('#operation')?.value || '';
                const A = [];
                for (let i = 0; i < numRows; i++) {
                    const row = [];
                    for (let j = 0; j < numCols; j++) row.push(qs(`#matrixGridA_${i}_${j}`)?.value || '0');
                    A.push(row);
                }
                const B = [];
                if (qs('#matrixBWrapper') && qs('#matrixBWrapper').style.display !== 'none') {
                    for (let i = 0; i < numRowsB; i++) {
                        const row = [];
                        for (let j = 0; j < numColsB; j++) row.push(qs(`#matrixGridB_${i}_${j}`)?.value || '0');
                        B.push(row);
                    }
                }
                return { type, op, A, B };
            }
            // Ensure no inline style stays on the button
            askBtn.removeAttribute('style');
            // Ensure it has `fixed` positioning class (per HTML requirement)
            askBtn.classList.add('fixed');
            askBtn.classList.remove('absolute');
            // Hide initially
            askBtn.classList.add('hidden');
            askBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (!selectedStepText) return;
                const ctx = gatherMatrixContext();
                let problemText = `Problem type: ${ctx.type}${ctx.op ? ' (operation: ' + ctx.op + ')' : ''}\nMatrix A:\n${matrixToString(ctx.A)}`;
                if (ctx.B && ctx.B.length) problemText += '\nMatrix B:\n' + matrixToString(ctx.B);
                const message = `Please explain the following matrix step in exam-oriented language.\n\n${problemText}\n\nStep:\n${selectedStepText}`;
                openMathBot(message);
            });
        }
    });

    // matrices.js will call the global `openMathBot` provided by main.js

})();
