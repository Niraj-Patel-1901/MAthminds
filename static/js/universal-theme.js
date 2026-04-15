// Universal Theme Toggle Script
// Works on all pages

(function() {
    'use strict';
    
    // Apply saved theme immediately to prevent flash
    function applyTheme() {
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const isDark = savedTheme === 'dark' || (!savedTheme && prefersDark);
        
        if (isDark) {
            document.documentElement.classList.add('dark');
            document.body.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
            document.body.classList.remove('dark');
        }
        
        return isDark;
    }
    
    // Update theme icon
    function updateIcon(isDark) {
        const icon = document.getElementById('theme-icon');
        if (icon) {
            icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
    
    // Toggle theme function
    function toggleTheme() {
        const isDark = document.documentElement.classList.contains('dark');
        
        if (isDark) {
            document.documentElement.classList.remove('dark');
            document.body.classList.remove('dark');
            localStorage.setItem('theme', 'light');
            updateIcon(false);
        } else {
            document.documentElement.classList.add('dark');
            document.body.classList.add('dark');
            localStorage.setItem('theme', 'dark');
            updateIcon(true);
        }
    }
    
    // Apply theme immediately
    const isDark = applyTheme();
    
    // Setup theme toggle when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        updateIcon(isDark);
        
        const themeBtn = document.getElementById('theme-toggle');
        if (themeBtn) {
            themeBtn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                toggleTheme();
                return false;
            };
        }
    });
    
    // Also setup after window load as backup
    window.addEventListener('load', function() {
        const currentIsDark = document.documentElement.classList.contains('dark');
        updateIcon(currentIsDark);
        
        const themeBtn = document.getElementById('theme-toggle');
        if (themeBtn && !themeBtn.onclick) {
            themeBtn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                toggleTheme();
                return false;
            };
        }
    });
    
    // Make toggle function globally available
    window.toggleTheme = toggleTheme;
    
})();
