/* RakshaRide Theme Manager */

function initTheme() {
    const savedTheme = localStorage.getItem('raksharide-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('raksharide-theme', newTheme);
    updateThemeIcon(newTheme);

    // Smooth transition effect
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 50);
}

function updateThemeIcon(theme) {
    const icon = document.querySelector('.theme-toggle i');
    if (icon) {
        if (theme === 'dark') {
            icon.setAttribute('data-lucide', 'sun');
            icon.style.color = '#ff9933';
        } else {
            icon.setAttribute('data-lucide', 'moon');
            icon.style.color = '#ffffff';
        }
        if (window.lucide) lucide.createIcons();
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    // Add toggle button to DOM if not present
    if (!document.querySelector('.theme-toggle')) {
        const toggle = document.createElement('button');
        toggle.className = 'theme-toggle';
        toggle.innerHTML = '<i data-lucide="moon"></i>';
        toggle.onclick = toggleTheme;
        toggle.title = "Toggle Dark Mode";
        document.body.appendChild(toggle);
    }

    initTheme();
    if (window.lucide) lucide.createIcons();
});
