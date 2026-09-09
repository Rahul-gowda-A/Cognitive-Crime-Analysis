/**
 * theme.js
 * Dynamic Dark / Light Theme Manager for Cognitive Crime Analysis System
 * Navy Operational (Dark Mode - Default) <-> Governmental Tactical (Light Mode)
 * Persists theme selection via localStorage ('app-theme')
 */

(function () {
    'use strict';

    const STORAGE_KEY = 'app-theme';
    const THEME_DARK = 'dark';
    const THEME_LIGHT = 'light';

    /**
     * Get stored theme or default to dark
     */
    function getSavedTheme() {
        try {
            return localStorage.getItem(STORAGE_KEY) || THEME_DARK;
        } catch (e) {
            return THEME_DARK;
        }
    }

    /**
     * Apply theme attribute to document and update all toggle buttons
     */
    function applyTheme(theme) {
        const isLight = theme === THEME_LIGHT;
        document.documentElement.setAttribute('data-theme', theme);
        if (document.body) {
            document.body.setAttribute('data-theme', theme);
        }

        // Update all toggle buttons in DOM
        const toggleButtons = document.querySelectorAll('#theme-toggle-btn, .theme-toggle-btn');
        toggleButtons.forEach(btn => {
            const icon = btn.querySelector('.theme-icon, i');
            const label = btn.querySelector('.theme-text, span:not(.theme-icon)');

            if (icon) {
                icon.className = isLight ? 'fas fa-sun theme-icon' : 'fas fa-moon theme-icon';
                icon.style.color = isLight ? '#f59e0b' : '#38bdf8';
            }
            if (label) {
                label.textContent = isLight ? 'Light Mode' : 'Dark Mode';
            }
            btn.setAttribute('aria-checked', isLight ? 'true' : 'false');
            btn.setAttribute('title', isLight ? 'Switch to Dark Mode (Navy Operational)' : 'Switch to Light Mode (Governmental Tactical)');
        });
    }

    /**
     * Toggle current theme and save to localStorage
     */
    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme') || THEME_DARK;
        const nextTheme = current === THEME_LIGHT ? THEME_DARK : THEME_LIGHT;
        try {
            localStorage.setItem(STORAGE_KEY, nextTheme);
        } catch (e) {
            console.warn('localStorage is unavailable', e);
        }
        applyTheme(nextTheme);
    }

    // Apply saved theme immediately
    const initialTheme = getSavedTheme();
    document.documentElement.setAttribute('data-theme', initialTheme);

    // Bind event listeners when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    function init() {
        applyTheme(getSavedTheme());

        // Delegate or bind to all theme toggle buttons
        document.querySelectorAll('#theme-toggle-btn, .theme-toggle-btn').forEach(btn => {
            btn.removeEventListener('click', toggleTheme);
            btn.addEventListener('click', toggleTheme);
        });
    }

    // Expose toggle function globally
    window.toggleAppTheme = toggleTheme;
    window.applyAppTheme = applyTheme;
})();
