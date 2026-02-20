// LogViewer JavaScript - Live tail, search, and filtering

(function() {
    'use strict';

    // State
    let autoRefreshEnabled = true;
    let refreshTimer = null;
    let currentFilter = '';
    let currentLines = [];

    // DOM elements
    const logContent = document.getElementById('logContent');
    const refreshBtn = document.getElementById('refreshBtn');
    const autoRefreshCheck = document.getElementById('autoRefreshCheck');
    const favoriteBtn = document.getElementById('favoriteBtn');
    const searchBtn = document.getElementById('searchBtn');
    const searchPanel = document.getElementById('searchPanel');
    const searchInput = document.getElementById('searchInput');
    const executeSearchBtn = document.getElementById('executeSearchBtn');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    const regexCheck = document.getElementById('regexCheck');
    const caseCheck = document.getElementById('caseCheck');
    const searchResults = document.getElementById('searchResults');
    const levelFilter = document.getElementById('levelFilter');
    const tailLinesSelect = document.getElementById('tailLines');
    const statusMessage = document.getElementById('statusMessage');

    // Config from template
    const config = window.logViewerConfig;

    // Initialize
    function init() {
        setupEventListeners();
        loadLog();
        startAutoRefresh();
    }

    function setupEventListeners() {
        // Refresh controls
        refreshBtn.addEventListener('click', () => loadLog());
        autoRefreshCheck.addEventListener('change', (e) => {
            autoRefreshEnabled = e.target.checked;
            if (autoRefreshEnabled) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });

        // Favorite toggle
        favoriteBtn.addEventListener('click', toggleFavorite);

        // Search controls
        searchBtn.addEventListener('click', toggleSearchPanel);
        executeSearchBtn.addEventListener('click', executeSearch);
        clearSearchBtn.addEventListener('click', clearSearch);
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') executeSearch();
        });

        // Filter controls
        levelFilter.addEventListener('change', (e) => {
            currentFilter = e.target.value;
            applyFilter();
        });

        tailLinesSelect.addEventListener('change', () => loadLog());
    }

    // Load log content
    async function loadLog() {
        const lines = tailLinesSelect.value;
        const url = `/api/tail/${config.logPath}?lines=${lines}`;

        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            currentLines = data.lines;
            renderLines(currentLines);
            updateStatus(`Loaded ${currentLines.length} line(s)`);
        } catch (error) {
            logContent.innerHTML = `<div class="loading" style="color: var(--red);">Error loading log: ${error.message}</div>`;
            updateStatus('Error loading log');
        }
    }

    // Render log lines
    function renderLines(lines) {
        if (lines.length === 0) {
            logContent.innerHTML = '<div class="loading">No content</div>';
            return;
        }

        const html = lines
            .map(line => {
                const className = getLineClass(line);
                const escaped = escapeHtml(line);
                return `<div class="log-line ${className}">${escaped}</div>`;
            })
            .join('');

        logContent.innerHTML = html;

        // Auto-scroll to bottom
        logContent.scrollTop = logContent.scrollHeight;
    }

    // Determine line CSS class based on content
    function getLineClass(line) {
        const upper = line.toUpperCase();
        if (upper.includes('ERROR')) return 'error';
        if (upper.includes('WARNING') || upper.includes('WARN')) return 'warning';
        if (upper.includes('INFO')) return 'info';
        if (upper.includes('DEBUG')) return 'debug';
        return '';
    }

    // Apply level filter
    function applyFilter() {
        if (!currentFilter) {
            renderLines(currentLines);
            updateStatus(`Showing all ${currentLines.length} line(s)`);
            return;
        }

        const filtered = currentLines.filter(line => {
            return line.toUpperCase().includes(currentFilter);
        });

        renderLines(filtered);
        updateStatus(`Filtered: ${filtered.length}/${currentLines.length} line(s)`);
    }

    // Auto-refresh
    function startAutoRefresh() {
        stopAutoRefresh();
        if (autoRefreshEnabled) {
            refreshTimer = setInterval(() => {
                loadLog();
            }, config.refreshInterval);
        }
    }

    function stopAutoRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
        }
    }

    // Favorite toggle
    async function toggleFavorite() {
        const isFavorite = favoriteBtn.getAttribute('data-favorite') === 'true';
        const url = `/api/favorite/${config.logPath}`;

        try {
            const response = await fetch(url, { method: 'POST' });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            
            // Update button
            favoriteBtn.setAttribute('data-favorite', data.is_favorite ? 'true' : 'false');
            favoriteBtn.textContent = data.is_favorite ? '⭐ Unfavorite' : '☆ Favorite';
            favoriteBtn.className = data.is_favorite ? 'btn btn-orange' : 'btn btn-secondary';
            
            updateStatus(data.is_favorite ? 'Added to favorites' : 'Removed from favorites');
        } catch (error) {
            updateStatus('Error toggling favorite');
        }
    }

    // Search panel toggle
    function toggleSearchPanel() {
        const isVisible = searchPanel.style.display !== 'none';
        searchPanel.style.display = isVisible ? 'none' : 'block';
        if (!isVisible) {
            searchInput.focus();
        }
    }

    // Execute search
    async function executeSearch() {
        const query = searchInput.value.trim();
        if (!query) {
            updateStatus('Enter a search query');
            return;
        }

        const useRegex = regexCheck.checked;
        const caseSensitive = caseCheck.checked;
        const url = `/api/search/${config.logPath}?q=${encodeURIComponent(query)}&regex=${useRegex ? 1 : 0}&case=${caseSensitive ? 1 : 0}`;

        searchResults.innerHTML = '<div class="loading">Searching...</div>';

        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            renderSearchResults(data.matches, data.query);
            updateStatus(`Found ${data.count} match(es)`);
        } catch (error) {
            searchResults.innerHTML = `<div class="loading" style="color: var(--red);">Search error: ${error.message}</div>`;
            updateStatus('Search failed');
        }
    }

    // Render search results
    function renderSearchResults(matches, query) {
        if (matches.length === 0) {
            searchResults.innerHTML = '<div class="loading">No matches found</div>';
            return;
        }

        const html = matches
            .map(match => {
                const escaped = escapeHtml(match.text);
                return `
                    <div class="search-result-line">
                        <span class="search-line-number">${match.line_number}:</span>
                        <span>${escaped}</span>
                    </div>
                `;
            })
            .join('');

        searchResults.innerHTML = html;
    }

    // Clear search
    function clearSearch() {
        searchInput.value = '';
        searchResults.innerHTML = '';
        updateStatus('Search cleared');
    }

    // Update status message
    function updateStatus(message) {
        statusMessage.textContent = message;
        setTimeout(() => {
            statusMessage.textContent = '';
        }, 3000);
    }

    // Escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Start the app
    init();
})();
