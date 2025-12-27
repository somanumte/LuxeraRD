// ============================================
// SISTEMA DE TEMAS Y PERSONALIZACIÓN LUXERA
// ============================================

const THEME_CONFIG = {
    THEME_KEY: 'luxera-theme',
    PRIMARY_COLOR_KEY: 'luxera-primary',
    DEFAULT_COLORS: {
        light: {
            primary: '#6366f1',
            background: '#ffffff',
            text: '#1f2937'
        },
        dark: {
            primary: '#818cf8',
            background: '#111827',
            text: '#f9fafb'
        }
    }
};

class ThemeManager {
    constructor() {
        this.init();
    }

    init() {
        const savedTheme = localStorage.getItem(THEME_CONFIG.THEME_KEY);
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        const initialTheme = savedTheme || systemTheme;

        this.setTheme(initialTheme, false);
        this.loadCustomColors();
        this.watchSystemTheme();
        this.setupEventListeners();
    }

    setTheme(theme, save = true) {
        const html = document.documentElement;

        if (theme === 'dark') {
            html.classList.add('dark');
        } else {
            html.classList.remove('dark');
        }

        if (save) {
            localStorage.setItem(THEME_CONFIG.THEME_KEY, theme);
        }

        this.updateToggle(theme);
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }

    toggleTheme() {
        const currentTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    getCurrentTheme() {
        return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    }

    updateToggle(theme) {
        const toggleBtn = document.getElementById('theme-toggle');
        if (!toggleBtn) return;

        const sunIcon = toggleBtn.querySelector('.sun-icon');
        const moonIcon = toggleBtn.querySelector('.moon-icon');

        if (theme === 'dark') {
            sunIcon?.classList.remove('hidden');
            moonIcon?.classList.add('hidden');
        } else {
            sunIcon?.classList.add('hidden');
            moonIcon?.classList.remove('hidden');
        }
    }

    setCustomColor(color) {
        localStorage.setItem(THEME_CONFIG.PRIMARY_COLOR_KEY, color);
        document.documentElement.style.setProperty('--color-primary', color);
        window.dispatchEvent(new CustomEvent('colorChanged', { detail: { color } }));
    }

    loadCustomColors() {
        const savedColor = localStorage.getItem(THEME_CONFIG.PRIMARY_COLOR_KEY);
        if (savedColor) {
            document.documentElement.style.setProperty('--color-primary', savedColor);
        }
    }

    resetColors() {
        localStorage.removeItem(THEME_CONFIG.PRIMARY_COLOR_KEY);
        document.documentElement.style.removeProperty('--color-primary');
    }

    watchSystemTheme() {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            if (!localStorage.getItem(THEME_CONFIG.THEME_KEY)) {
                this.setTheme(e.matches ? 'dark' : 'light', false);
            }
        });
    }

    setupEventListeners() {
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleTheme());
        }

        const colorPicker = document.getElementById('color-picker');
        if (colorPicker) {
            colorPicker.addEventListener('input', (e) => {
                this.setCustomColor(e.target.value);
            });
        }

        const resetBtn = document.getElementById('reset-colors');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetColors();
                location.reload();
            });
        }
    }
}

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

function getContrastColor(hexColor) {
    const rgb = hexToRgb(hexColor);
    if (!rgb) return '#000000';
    const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255;
    return luminance > 0.5 ? '#000000' : '#ffffff';
}

let themeManager;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        themeManager = new ThemeManager();
    });
} else {
    themeManager = new ThemeManager();
}

window.ThemeManager = ThemeManager;
window.themeManager = themeManager;