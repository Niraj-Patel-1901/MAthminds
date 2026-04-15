// Check for saved theme preference, otherwise use system preference
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const savedTheme = localStorage.getItem('theme');
const isDark = savedTheme === 'dark' || (!savedTheme && prefersDark);

// Function to toggle theme
function toggleTheme() {
    const body = document.body;
    const isDarkMode = body.classList.contains('dark-theme');
    
    if (isDarkMode) {
        body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
        updateThemeIcon(false);
    } else {
        body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
        updateThemeIcon(true);
    }
}

// Function to update theme icon
function updateThemeIcon(isDark) {
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        themeIcon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// Initialize theme
document.addEventListener('DOMContentLoaded', () => {
    if (isDark) {
        document.body.classList.add('dark-theme');
        updateThemeIcon(true);
    } else {
        updateThemeIcon(false);
    }
}); 