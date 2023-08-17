function displayLoading() {
    const loader = document.getElementById('loader');
    loader.style.display = "block";
}

// Toggle function to switch between dark and light mode, and save the preference
function toggleDarkMode() {
    const body = document.querySelector('body');
    
    if (body.classList.contains('dark-mode')) {
        body.classList.remove('dark-mode');
        localStorage.setItem('theme', 'light');  // Save theme preference
    } else {
        body.classList.add('dark-mode');
        localStorage.setItem('theme', 'dark');   // Save theme preference
    }
}

// On page load, check the theme preference and apply it
document.addEventListener('DOMContentLoaded', function() {
    const currentTheme = localStorage.getItem('theme');

    if (currentTheme === 'dark') {
        document.querySelector('body').classList.add('dark-mode');
    } else {
        document.querySelector('body').classList.remove('dark-mode');
    }
});
