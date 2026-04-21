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


    // Initialize and wire up UI
    document.addEventListener('DOMContentLoaded', () => {
        console.log('[matrices.js] DOMContentLoaded');

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
                const stepsHtml = steps.map((s,i) => `<div class="step-block solution-step p-3 rounded my-2 cursor-pointer select-text" data-step-index="${i}">\\(${s}\\)</div>`).join('');

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

                // Typeset MathJax after DOM update
                if (window.MathJax && window.MathJax.typesetPromise) {
                    window.MathJax.typesetPromise();
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

        // Ask MathBot logic removed - now handled globally by main.js
    });

    // matrices.js will call the global `openMathBot` provided by main.js

})();
