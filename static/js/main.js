// // Module data structure with icons
// const el = document.getElementById("something");
// if (!el) return;
const modules = {
    1: [
        {
            title: "Complex Numbers",
            subtitle: "D'Moivre's Theorem, expansions, powers & roots",
            description: "Solve complex number problems including powers, roots, and expansions using D'Moivre's Theorem.",
            path: "pages/complex-numbers.html",
            icon: "fa-square-root-alt"
        },
        {
            title: "Hyperbolic & Log Functions",
            subtitle: "Real/imag parts, inverse hyperbolic",
            description: "Work with hyperbolic functions, logarithms, and their properties.",
            path: "pages/hyperbolic-log.html",
            icon: "fa-wave-square"
        },
        {
            title: "Partial Differentiation",
            subtitle: "Chain rule, Euler's theorem",
            description: "Solve partial differentiation problems using chain rule and Euler's theorem.",
            path: "pages/partial-diff.html",
            icon: "fa-superscript"
        },
        {
            title: "Maxima & Minima",
            subtitle: "Lagrange's method",
            description: "Find maxima and minima using Lagrange's method of multipliers.",
            path: "pages/maxima-minima.html",
            icon: "fa-chart-line"
        },
        {
            title: "Matrices",
            subtitle: "Echelon form, rank, PAQ",
            description: "Work with matrices, including echelon form, rank, and PAQ decomposition.",
            path: "pages/matrices.html",
            icon: "fa-table"
        },
        {
            title: "Numerical Methods",
            subtitle: "Newton-Raphson, Gauss-Seidel, Taylor series",
            description: "Solve numerical problems using various methods including Newton-Raphson and Taylor series.",
            path: "pages/numerical-methods.html",
            icon: "fa-calculator"
        }
    ],
    2: [
        {
            title: "1st Order ODEs",
            subtitle: "Exact, Bernoulli, linear",
            description: "Solve first-order ordinary differential equations using various methods.",
            path: "pages/first-order-odes.html",
            icon: "fa-function"
        },
        {
            title: "Higher Order DEs",
            subtitle: "Constant coefficients, variation of parameters",
            description: "Solve higher-order differential equations with constant coefficients.",
            path: "pages/higher-order-des.html",
            icon: "fa-superscript"
        },
        {
            title: "Beta & Gamma Functions",
            subtitle: "Properties and evaluation",
            description: "Work with Beta and Gamma functions and their properties.",
            path: "pages/beta-gamma.html",
            icon: "fa-infinity"
        },
        {
            title: "Double/Triple Integrals",
            subtitle: "Cartesian, polar, cylindrical",
            description: "Solve multiple integrals in various coordinate systems.",
            path: "pages/multiple-integrals.html",
            icon: "fa-cube"
        },
        {
            title: "Rectification",
            subtitle: "Length of curves",
            description: "Calculate the length of curves using integration.",
            path: "pages/rectification.html",
            icon: "fa-ruler"
        },
        {
            title: "Numerical Integration",
            subtitle: "Trapezoidal, Simpson's rules",
            description: "Approximate definite integrals using numerical methods.",
            path: "pages/numerical-integration.html",
            icon: "fa-chart-area"
        }
    ],
    3: [
        {
            title: "Laplace Transform",
            subtitle: "Properties, real integrals",
            description: "Apply Laplace transforms to solve differential equations.",
            path: "pages/laplace-transform.html",
            icon: "fa-wave-square"
        },
        {
            title: "Inverse Laplace",
            subtitle: "Partial fractions, convolution",
            description: "Find inverse Laplace transforms using various methods.",
            path: "pages/inverse-laplace.html",
            icon: "fa-undo"
        },
        {
            title: "Fourier Series",
            subtitle: "Full range, half-range, even/odd",
            description: "Work with Fourier series expansions and their properties.",
            path: "pages/fourier-series.html",
            icon: "fa-chart-bar"
        },
        {
            title: "Complex Variables",
            subtitle: "Analytic, harmonic, Milne-Thomson",
            description: "Study complex variables and their applications.",
            path: "pages/complex-variables.html",
            icon: "fa-circle"
        },
        {
            title: "Regression & Curve Fit",
            subtitle: "Pearson, Spearman, least squares",
            description: "Perform regression analysis and curve fitting.",
            path: "pages/regression.html",
            icon: "fa-chart-bar"
        },
        {
            title: "Probability",
            subtitle: "Bayes, PDF/PMF, expectation, variance",
            description: "Solve probability problems and statistical analysis.",
            path: "pages/probability.html",
            icon: "fa-dice"
        }
    ],
    4: [
        {
            title: "Eigenvalues & Vectors",
            subtitle: "Characteristic eqn, diagonalization",
            description: "Find eigenvalues and eigenvectors of matrices.",
            path: "pages/eigenvalues.html",
            icon: "fa-vector-square"
        },
        {
            title: "Complex Integration",
            subtitle: "Cauchy's theorem, residues",
            description: "Perform complex integration using Cauchy's theorem.",
            path: "pages/complex-integration.html",
            icon: "fa-circle-dot"
        },
        {
            title: "Z-Transform",
            subtitle: "Standard functions, ROC",
            description: "Apply Z-transforms to discrete-time signals.",
            path: "pages/z-transform.html",
            icon: "fa-wave-square"
        },
        {
            title: "Inverse Z-Transform",
            subtitle: "Partial fractions, convolution",
            description: "Find inverse Z-transforms using various methods.",
            path: "pages/inverse-z-transform.html",
            icon: "fa-rotate"
        },
        {
            title: "Linear Programming",
            subtitle: "Simplex, dual, Big-M",
            description: "Solve linear programming problems using the simplex method.",
            path: "pages/linear-programming.html",
            icon: "fa-diagram-project"
        },
        {
            title: "Non-Linear Programming",
            subtitle: "Lagrange multipliers, Kuhn-Tucker",
            description: "Solve non-linear optimization problems.",
            path: "pages/nonlinear-programming.html",
            icon: "fa-diagram-project"
        }
    ]
};

// Tab functionality
function initTabs() {
    const tabs = document.querySelectorAll('.semester-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            tab.classList.add('active');
            // Update module cards
            updateModuleCards(tab.dataset.semester);
        });
    });
}

// Update module cards with animations
function updateModuleCards(semester) {
    const container = document.getElementById('moduleCards');
    container.innerHTML = ''; // Clear existing cards

    modules[semester].forEach((module, index) => {
        const card = document.createElement('div');
        card.className = 'module-card animate-fade-in';
        card.style.animationDelay = `${index * 0.1}s`;
        card.innerHTML = `
            <div class="module-card-header">
                <h3 class="module-card-title">
                    <i class="fas ${module.icon}"></i>
                    ${module.title}
                </h3>
                <p class="module-card-subtitle">${module.subtitle}</p>
            </div>
            <div class="module-card-content">
                <p class="module-card-description">${module.description}</p>
                <a href="${module.path}" class="btn-primary mt-4 inline-block">
                    <i class="fas fa-arrow-right mr-2"></i>
                    Open Module
                </a>
            </div>
        `;
        container.appendChild(card);
    });
}

// Theme toggle logic
function setTheme(theme) {
    if (theme === 'dark') {
        document.documentElement.classList.add('dark');
        document.body.classList.add('dark');
        localStorage.setItem('theme', 'dark');
    } else {
        document.documentElement.classList.remove('dark');
        document.body.classList.remove('dark');
        localStorage.setItem('theme', 'light');
    }
}

function getPreferredTheme() {
    const stored = localStorage.getItem('theme');
    if (stored) return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (!icon) return;
    icon.className = theme === 'dark'
        ? 'fas fa-sun'
        : 'fas fa-moon';
}

function toggleTheme() {
    const current = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    setTheme(next);
    updateThemeIcon(next);
}

// Initialize theme immediately to prevent flash
function initTheme() {
    const theme = getPreferredTheme();
    setTheme(theme);
    updateThemeIcon(theme);
}

// Call theme initialization immediately
initTheme();

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    // Show Maths 1 modules by default
    updateModuleCards('1');

    // Set initial theme
    const theme = getPreferredTheme();
    setTheme(theme);
    updateThemeIcon(theme);

    // Theme toggle button - use onclick for better compatibility
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        toggleBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleTheme();
            return false;
        };
    }

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            setTheme(e.matches ? 'dark' : 'light');
            updateThemeIcon(e.matches ? 'dark' : 'light');
        }
    });
}); 

// Expose global function to open MathBot and auto-send a message
window.openMathBot = function (message) {
    const panel = document.getElementById("mathbot-panel");
    const input = document.getElementById("mathbot-input");
    const sendBtn = document.getElementById("mathbot-send");
    const toggleBtn = document.getElementById("mathbot-btn");

    // If UI isn't ready yet, wait for DOMContentLoaded then try again once
    if (!panel || !input || !sendBtn) {
        document.addEventListener('DOMContentLoaded', function once() {
            document.removeEventListener('DOMContentLoaded', once);
            window.openMathBot(message);
        }, { once: true });
        return;
    }

    // Ensure panel is visible. Prefer using the toggle button handler if present
    if (panel.classList.contains('hidden')) {
        if (toggleBtn) {
            try { toggleBtn.click(); } catch (e) { panel.classList.remove('hidden'); }
        } else {
            panel.classList.remove('hidden');
        }
    }

    // Focus and set the message, trigger input events
    input.focus();
    input.value = message;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));

    // Small delay to ensure the panel has become visible and input rendered
    setTimeout(() => {
        try { sendBtn.click(); } catch (e) { /* ignore */ }
    }, 60);
};

// =================== MathBot UI ===================

document.addEventListener("DOMContentLoaded", () => {

    const botHTML = `
    <div id="mathbot-container" class="fixed bottom-6 right-6 z-50">
        <button id="mathbot-btn" class="w-14 h-14 rounded-full bg-pink-600 text-white shadow-lg flex items-center justify-center hover:bg-pink-700 transition">
            <i class="fas fa-robot text-xl"></i>
        </button>

        <div id="mathbot-panel" class="hidden fixed bottom-24 right-6 w-80 bg-white rounded-xl shadow-xl border flex flex-col overflow-hidden">

            <div class="bg-gradient-to-r from-pink-600 to-purple-600 p-5 text-white font-bold flex justify-between items-center">
                <span>MathBot</span>
                <button id="mathbot-close" class="text-white text-lg">&times;</button>
            </div>

            <div id="mathbot-messages" class="p-3 h-64 overflow-y-auto text-sm space-y-2 bg-gray-50"></div>

            <div class="p-2 border-t flex">
                <input id="mathbot-input" class="flex-1 p-2 border rounded text-sm" placeholder="Ask me about this step or topic...">
                <button id="mathbot-send" class="ml-2 bg-pink-600 text-white px-3 rounded hover:bg-pink-700">
                    Send
                </button>
            </div>
        </div>
    </div>
    `;

    document.body.insertAdjacentHTML("beforeend", botHTML);

    const btn = document.getElementById("mathbot-btn");
    const panel = document.getElementById("mathbot-panel");
    const close = document.getElementById("mathbot-close");
    const send = document.getElementById("mathbot-send");
    const input = document.getElementById("mathbot-input");
    const messages = document.getElementById("mathbot-messages");

    btn.addEventListener("click", () => {
        panel.classList.toggle("hidden");
        if (!panel.classList.contains("hidden")) {
            messages.innerHTML += `<div class="text-gray-700">👋 Hi! I'm MathBot. Ask me anything about this module.</div>`;
        }
    });

    close.addEventListener("click", () => {
        panel.classList.add("hidden");
    });


});


// ===============================
// MathBot (AI Tutor) Integration
// ===============================

document.addEventListener("DOMContentLoaded", () => {

    const botInput = document.getElementById("mathbot-input");
    const botSend = document.getElementById("mathbot-send");
    const botMessages = document.getElementById("mathbot-messages");

    if (!botInput || !botSend || !botMessages) {
        console.log("MathBot UI not found on this page");
        return;
    }

   function getCurrentModule() {
    const moduleDiv = document.getElementById("module-name");
    return moduleDiv
        ? moduleDiv.dataset.module
        : "General Mathematics";
}

    function addMessage(text, sender) {
    const div = document.createElement("div");

    div.className = sender === "user"
        ? "bg-pink-100 p-2 rounded text-right ml-8"
        : "bg-white p-2 rounded shadow mr-8";

    // Convert Gemini markdown → HTML
    const html = text.replace(/\n/g, "<br>");

    div.innerHTML = html;
    botMessages.appendChild(div);
    botMessages.scrollTop = botMessages.scrollHeight;

    // Robust MathJax rendering: prefer typesetPromise (v3), fallback to typeset (v2),
    // and poll briefly if MathJax hasn't loaded yet.
    function typesetTarget(target) {
        try {
            if (window.MathJax) {
                if (MathJax.typesetPromise) {
                    MathJax.typesetPromise([target]).catch(() => {});
                    return true;
                }
                if (MathJax.typeset) {
                    try { MathJax.typeset([target]); } catch (e) { /* ignore */ }
                    return true;
                }
            }
        } catch (e) { /* ignore */ }
        return false;
    }

    if (!typesetTarget(div)) {
        // If MathJax isn't present yet, poll for a short time and then typeset.
        const start = Date.now();
        const iv = setInterval(() => {
            if (typesetTarget(div) || Date.now() - start > 5000) {
                clearInterval(iv);
            }
        }, 120);
    }
}

async function sendToMathBot(question) {
    addMessage(question, "user");

    const thinking = document.createElement("div");
    thinking.className = "bg-white p-2 rounded shadow mr-8 thinking";
    thinking.innerText = "Thinking...";
    botMessages.appendChild(thinking);

    const module = getCurrentModule();

    try {
        const res = await fetch("/api/mathbot", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question: question,
                module: module,
                step: ""
            })
        });

        const data = await res.json();

        const thinkingEl = botMessages.querySelector(".thinking");
        if (thinkingEl) thinkingEl.remove();

        if (!data.success) {
            addMessage("❌ " + data.error, "bot");
            return;
        }

        addMessage(data.reply, "bot");

    } catch (err) {
        const thinkingEl = botMessages.querySelector(".thinking");
        if (thinkingEl) thinkingEl.remove();
        addMessage("❌ Server not responding", "bot");
    }
}

    botSend.addEventListener("click", () => {
        const text = botInput.value.trim();
        if (!text) return;
        botInput.value = "";
        sendToMathBot(text);
    });

    botInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            botSend.click();
        }
    });

});


// Removed text-selection and inline step-selection logic. Step selection and
// Ask MathBot behavior is handled in `static/js/matrices.js` for the Matrices
// page. This keeps selection behavior centralized and avoids duplicate
// handlers that caused the Ask button to be hidden or misplaced.

// Global Step selection + Ask MathBot button (delegated, works on all pages)
document.addEventListener('DOMContentLoaded', () => {
    // Ensure a single Ask MathBot floating button exists
    let askBtn = document.getElementById('ask-mathbot-btn');
    if (!askBtn) {
        askBtn = document.createElement('button');
        askBtn.id = 'ask-mathbot-btn';
        askBtn.style.display = 'none';
        askBtn.style.position = 'absolute';
        askBtn.className = 'fixed z-50 bg-pink-600 text-white text-xs px-2 py-1 rounded shadow-lg';
        askBtn.innerText = 'Ask MathBot';
        document.body.appendChild(askBtn);
    }

    // Inject minimal CSS for selected step if not present
    if (!document.getElementById('mathbot-inline-style')) {
        const s = document.createElement('style');
        s.id = 'mathbot-inline-style';
        s.textContent = `
        .mathbot-selected { background: rgba(255,228,230,0.9) !important; border-radius: 6px; padding: 0.35rem !important; }
        #ask-mathbot-btn { transition: opacity 0.12s ease; }
        `;
        document.head.appendChild(s);
    }

    let selectedStep = null;

    function hideAsk() {
        askBtn.style.display = 'none';
    }

    function showAskNear(elem) {
        const rect = elem.getBoundingClientRect();
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const scrollLeft = window.scrollX || document.documentElement.scrollLeft;
        let top = rect.top + scrollTop + rect.height / 2 - 18;
        let left = rect.right + scrollLeft + 10;
        if (left + 160 > window.innerWidth + scrollLeft) {
            left = rect.left + scrollLeft - 160 - 10;
        }
        askBtn.style.top = Math.max(8, top) + 'px';
        askBtn.style.left = Math.max(8, left) + 'px';
        askBtn.style.display = 'block';
    }

    // Click on any .solution-step (delegated)
    document.addEventListener('click', (e) => {
        const step = e.target.closest && e.target.closest('.solution-step');
        if (step) {
            e.stopPropagation();
            if (selectedStep && selectedStep !== step) selectedStep.classList.remove('mathbot-selected');
            selectedStep = step;
            step.classList.add('mathbot-selected');
            showAskNear(step);
            return;
        }

        // clicked outside a step -> deselect
        if (!e.target.closest || !e.target.closest('#ask-mathbot-btn')) {
            if (selectedStep) selectedStep.classList.remove('mathbot-selected');
            selectedStep = null;
            hideAsk();
        }
    });

    // Keyboard support: Enter/Space to select when focused
    document.addEventListener('keydown', (e) => {
        const el = document.activeElement;
        if (el && el.classList && el.classList.contains('solution-step')) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                el.click();
            }
        }
    });

    // Ask button behavior: open MathBot panel and send selected step text
    askBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (!selectedStep) return;
        const stepText = (selectedStep.innerText || selectedStep.textContent || '').trim();
        const moduleName = (document.getElementById('module-name') && document.getElementById('module-name').dataset.module) || document.title || 'Math';
        const message = `Module: ${moduleName}\nPlease explain this step:\n${stepText}`;
        try {
            if (typeof window.openMathBot === 'function') {
                window.openMathBot(message);
            } else {
                const inp = document.getElementById('mathbot-input');
                const send = document.getElementById('mathbot-send');
                if (inp) inp.value = message;
                if (send) send.click();
            }
        } catch (err) { console.warn('Could not open MathBot', err); }
    });

    hideAsk();
});