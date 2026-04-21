// regression_frontend.js
// Usage: include this script in regression.html after MathJax and DOM elements exist.

// Helper to read comma-separated values and return array
function parseCSVValues(s) {
    if (!s) return [];
    return s.split(",").map(x => x.trim()).filter(x => x !== "");
}

// Renders steps array (LaTeX strings) into target element and calls MathJax
// Helper to render steps + results
function renderStepsAndResult(payload) {
    const solutionDiv = document.getElementById('solution');
    solutionDiv.innerHTML = '';

    if (!payload) {
        solutionDiv.innerHTML = '<p class="text-red-600">No payload</p>';
        return;
    }

    // ✅ TABLE
    if (payload.table && payload.table.headers && payload.table.rows) {
        const table = document.createElement('table');
        table.className = 'min-w-full border border-gray-300 text-sm text-left overflow-x-auto';

        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        payload.table.headers.forEach(h => {
            const th = document.createElement('th');
            th.className = 'border border-gray-300 px-2 py-1 font-semibold bg-gray-100';
            th.textContent = h;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        payload.table.rows.forEach(row => {
            const tr = document.createElement('tr');
            row.forEach(cell => {
                const td = document.createElement('td');
                td.className = 'border border-gray-300 px-2 py-1';
                td.textContent = cell;
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);

        solutionDiv.appendChild(table);
    }

    // ✅ STEPS
    if (payload.steps && payload.steps.length > 0) {
        const ol = document.createElement('ol');
        ol.className = 'list-decimal ml-6 space-y-2 mt-4';
        payload.steps.forEach(s => {
            const li = document.createElement('li');
            li.className = 'solution-step';
            li.innerHTML = `\\(${s}\\)`;
            ol.appendChild(li);
        });
        solutionDiv.appendChild(ol);
    }

    // ✅ RESULT
    if (payload.result) {
        const resBox = document.createElement('div');
        resBox.className = 'mt-4 p-3 bg-gray-50 border rounded solution-step';
        resBox.innerHTML = `<pre style="white-space:pre-wrap;">${JSON.stringify(payload.result, null, 2)}</pre>`;
        solutionDiv.appendChild(resBox);
    }

    // ✅ Render LaTeX
    if (window.MathJax && MathJax.typesetPromise) {
        MathJax.typesetPromise();
    }
}


// --- Example Loader (3️⃣) ---
function loadExample() {
    const type = document.getElementById('regType').value;

    let examples = {
        pearson: { x: "10,20,30,40,50", y: "15,25,35,45,55" },
        spearman: { x: "106,86,100,101,99,103,97,113,112,110", y: "7,0,27,50,28,29,20,12,6,17" },
        regression: { x: "1,2,3,4,5", y: "2,4,5,4,5" }
    };

    if (examples[type]) {
        document.getElementById('xValues').value = examples[type].x;
        document.getElementById('yValues').value = examples[type].y;
    }
}




// Main solve function (attach to Solve button)
async function solveRegression() {
    try {
        const typeSelect = document.getElementById('regType'); // e.g. select with options pearson,spearman,regression,all
        const type = typeSelect ? typeSelect.value : 'regression';
        // two input boxes for comma-separated values
        const xInput = document.getElementById('xValues').value;
        const yInput = document.getElementById('yValues').value;
        const xArr = parseCSVValues(xInput).map(v => v);
        const yArr = parseCSVValues(yInput).map(v => v);
        if (xArr.length === 0 || yArr.length === 0) {
            alert('Please enter both X and Y values (comma-separated).');
            return;
        }
        if (xArr.length !== yArr.length) {
            alert('X and Y must have the same number of entries.');
            return;
        }

        const payload = { type: type, x: xArr, y: yArr };

        const resp = await fetch('/api/regression', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await resp.json();
        if (!data.success) {
            document.getElementById('solution').innerHTML = `<p class="text-red-600">Error: ${data.error}</p>`;
            return;
        }

        // data.payload contains the solver return
        renderStepsAndResult(data.payload);
    } catch (err) {
        document.getElementById('solution').innerHTML = `<p class="text-red-600">Exception: ${err}</p>`;
        console.error(err);
    }
}

// Attach to button
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('tryExample').addEventListener('click', loadExample);
    const solveBtn = document.getElementById('solveBtn');
    if (solveBtn) solveBtn.addEventListener('click', solveRegression);
});
