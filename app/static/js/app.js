document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('postcard-form');
    const themeSelect = document.getElementById('theme');
    const themePreview = document.getElementById('theme-preview');
    const distanceSlider = document.getElementById('distance');
    const distanceValue = document.getElementById('distance-value');
    const generateBtn = document.getElementById('generate-btn');
    const loadingMessage = document.getElementById('loading-message');
    const resultSection = document.getElementById('result');
    const errorSection = document.getElementById('error');
    const postcardImage = document.getElementById('postcard-image');
    const downloadBtn = document.getElementById('download-btn');
    const newBtn = document.getElementById('new-btn');
    const retryBtn = document.getElementById('retry-btn');
    const errorMessage = document.getElementById('error-message');

    let themes = [];

    // Load themes on page load
    async function loadThemes() {
        try {
            const response = await fetch('/api/themes');
            const data = await response.json();
            themes = data.themes;

            themeSelect.innerHTML = themes.map(theme =>
                `<option value="${theme.id}">${theme.name}</option>`
            ).join('');

            // Select warm_beige as default if available
            const defaultTheme = themes.find(t => t.id === 'warm_beige');
            if (defaultTheme) {
                themeSelect.value = 'warm_beige';
            }

            updateThemePreview();
        } catch (error) {
            console.error('Failed to load themes:', error);
            themeSelect.innerHTML = '<option value="warm_beige">Warm Beige</option>';
        }
    }

    // Update theme preview colors
    function updateThemePreview() {
        const selectedTheme = themes.find(t => t.id === themeSelect.value);
        if (!selectedTheme) {
            themePreview.innerHTML = '';
            return;
        }

        const colors = selectedTheme.colors;
        themePreview.innerHTML = `
            <div class="color-swatch" style="background-color: ${colors.bg}" title="Background"></div>
            <div class="color-swatch" style="background-color: ${colors.text}" title="Text"></div>
            <div class="color-swatch" style="background-color: ${colors.road_primary}" title="Roads"></div>
            <div class="color-swatch" style="background-color: ${colors.water}" title="Water"></div>
            <div class="color-swatch" style="background-color: ${colors.parks}" title="Parks"></div>
            <span class="theme-description">${selectedTheme.description}</span>
        `;
    }

    // Update distance display
    function updateDistanceDisplay() {
        distanceValue.textContent = distanceSlider.value;
    }

    // Show/hide sections
    function showForm() {
        form.classList.remove('hidden');
        loadingMessage.classList.add('hidden');
        resultSection.classList.add('hidden');
        errorSection.classList.add('hidden');
        generateBtn.disabled = false;
        generateBtn.querySelector('.btn-text').classList.remove('hidden');
        generateBtn.querySelector('.btn-loading').classList.add('hidden');
    }

    function showLoading() {
        form.classList.add('hidden');
        loadingMessage.classList.remove('hidden');
        resultSection.classList.add('hidden');
        errorSection.classList.add('hidden');
    }

    function showResult(imageUrl) {
        form.classList.add('hidden');
        loadingMessage.classList.add('hidden');
        resultSection.classList.remove('hidden');
        errorSection.classList.add('hidden');
        postcardImage.src = imageUrl;
        downloadBtn.href = imageUrl;
    }

    function showError(message) {
        form.classList.remove('hidden');
        loadingMessage.classList.add('hidden');
        resultSection.classList.add('hidden');
        errorSection.classList.remove('hidden');
        errorMessage.textContent = message;
        generateBtn.disabled = false;
        generateBtn.querySelector('.btn-text').classList.remove('hidden');
        generateBtn.querySelector('.btn-loading').classList.add('hidden');
    }

    // Generate postcard
    async function generatePostcard(e) {
        e.preventDefault();

        const city = document.getElementById('city').value.trim();
        const country = document.getElementById('country').value.trim();
        const theme = themeSelect.value;
        const distance = parseInt(distanceSlider.value);
        const message = document.getElementById('message').value;
        const fast = document.getElementById('fast').checked;

        if (!city || !country) {
            showError('Please enter both city and country.');
            return;
        }

        // Show loading state
        generateBtn.disabled = true;
        generateBtn.querySelector('.btn-text').classList.add('hidden');
        generateBtn.querySelector('.btn-loading').classList.remove('hidden');

        showLoading();

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    city,
                    country,
                    theme,
                    distance,
                    message,
                    fast
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to generate postcard');
            }

            showResult(data.url);
        } catch (error) {
            console.error('Generation error:', error);
            showError(error.message);
        }
    }

    // Event listeners
    themeSelect.addEventListener('change', updateThemePreview);
    distanceSlider.addEventListener('input', updateDistanceDisplay);
    form.addEventListener('submit', generatePostcard);
    newBtn.addEventListener('click', showForm);
    retryBtn.addEventListener('click', () => {
        errorSection.classList.add('hidden');
    });

    // Dark mode toggle
    const themeToggle = document.getElementById('theme-toggle');

    function setTheme(isDark) {
        document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
        themeToggle.textContent = isDark ? '☀️' : '🌙';
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }

    function initTheme() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            setTheme(savedTheme === 'dark');
        } else {
            // Check system preference
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            setTheme(prefersDark);
        }
    }

    themeToggle.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        setTheme(!isDark);
    });

    // Initialize
    loadThemes();
    updateDistanceDisplay();
    initTheme();
});
