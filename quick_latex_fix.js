// Quick LaTeX Fix - Add this to your browser console
console.log('Forcing MathJax rendering...');

// Method 1: Try immediate rendering
if (typeof MathJax !== 'undefined' && MathJax.typeset) {
    MathJax.typeset();
    console.log('MathJax.typeset() called');
}

// Method 2: Try with promise
if (typeof MathJax !== 'undefined' && MathJax.typesetPromise) {
    MathJax.typesetPromise().then(() => {
        console.log('MathJax.typesetPromise() completed');
    });
}

// Method 3: Force re-render all math
if (typeof MathJax !== 'undefined') {
    MathJax.typesetClear();
    MathJax.typeset();
    console.log('MathJax cleared and re-rendered');
}

// Check if MathJax is loaded
console.log('MathJax loaded:', typeof MathJax !== 'undefined');
console.log('MathJax.typeset available:', typeof MathJax !== 'undefined' && MathJax.typeset); 