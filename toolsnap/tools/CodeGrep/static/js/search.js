// CodeGrep JavaScript - Search and results handling

(function() {
    'use strict';

    // DOM elements
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const clearBtn = document.getElementById('clearBtn');
    const regexCheck = document.getElementById('regexCheck');
    const caseCheck = document.getElementById('caseCheck');
    const wholeWordCheck = document.getElementById('wholeWordCheck');
    const searchStatus = document.getElementById('searchStatus');
    const searchResults = document.getElementById('searchResults');

    // Config from template
    const config = window.codeGrepConfig;

    // Initialize
    function init() {
        setupEventListeners();
        searchInput.focus();
    }

    function setupEventListeners() {
        // Search controls
        searchBtn.addEventListener('click', executeSearch);
        clearBtn.addEventListener('click', clearResults);
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') executeSearch();
        });

        // Disable whole word when regex is enabled
        regexCheck.addEventListener('change', (e) => {
            if (e.target.checked) {
                wholeWordCheck.checked = false;
                wholeWordCheck.disabled = true;
            } else {
                wholeWordCheck.disabled = false;
            }
        });
    }

    // Execute search
    async function executeSearch() {
        const query = searchInput.value.trim();
        
        if (!query) {
            updateStatus('Enter a search query', 'error');
            return;
        }

        const useRegex = regexCheck.checked;
        const caseSensitive = caseCheck.checked;
        const wholeWord = wholeWordCheck.checked;

        // Show loading
        searchResults.innerHTML = '<div class="loading">Searching...</div>';
        updateStatus('Searching...', '');

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    regex: useRegex,
                    case_sensitive: caseSensitive,
                    whole_word: wholeWord,
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }

            const data = await response.json();
            displayResults(data);
            
        } catch (error) {
            searchResults.innerHTML = `<div class="empty-state"><p style="color: var(--red);">Search error: ${error.message}</p></div>`;
            updateStatus(`Error: ${error.message}`, 'error');
        }
    }

    // Display search results
    function displayResults(data) {
        if (data.count === 0) {
            searchResults.innerHTML = '<div class="empty-state"><p>No matches found.</p></div>';
            updateStatus('No matches found', 'error');
            return;
        }

        let statusText = `Found ${data.count} match${data.count !== 1 ? 'es' : ''}`;
        if (data.truncated) {
            statusText += ` (limited to ${data.count})`;
        }
        updateStatus(statusText, 'success');

        // Group results by file
        const groupedResults = groupResultsByFile(data.results);

        // Render results
        let html = '';
        for (const [filePath, fileResults] of Object.entries(groupedResults)) {
            html += renderFileResults(filePath, fileResults);
        }

        searchResults.innerHTML = html;

        // Attach event listeners to open buttons
        attachOpenButtons();
    }

    // Group results by file
    function groupResultsByFile(results) {
        const grouped = {};
        for (const result of results) {
            const path = result.relative_path;
            if (!grouped[path]) {
                grouped[path] = [];
            }
            grouped[path].push(result);
        }
        return grouped;
    }

    // Render results for a single file
    function renderFileResults(filePath, results) {
        let html = '<div class="result-item">';
        
        // Header
        html += '<div class="result-header">';
        html += `<div>`;
        html += `<div class="result-file">${escapeHtml(filePath)}</div>`;
        html += `<div class="result-line">${results.length} match${results.length !== 1 ? 'es' : ''}</div>`;
        html += `</div>`;
        html += `<button class="open-in-editor" data-file="${escapeHtml(results[0].file_path)}" data-line="${results[0].line_number}">Open in VS Code</button>`;
        html += '</div>';

        // Content
        html += '<div class="result-content">';
        html += '<div class="code-block">';

        for (const result of results) {
            // Context before
            const startLine = result.line_number - result.context_before.length;
            for (let i = 0; i < result.context_before.length; i++) {
                html += renderCodeLine(startLine + i, result.context_before[i], false);
            }

            // Matching line
            html += renderCodeLine(result.line_number, result.line_text, true);

            // Context after
            for (let i = 0; i < result.context_after.length; i++) {
                html += renderCodeLine(result.line_number + i + 1, result.context_after[i], false);
            }

            // Separator between matches in same file
            if (results.indexOf(result) < results.length - 1) {
                html += '<div class="code-line context"><div class="line-number">...</div><div class="line-content"></div></div>';
            }
        }

        html += '</div>';
        html += '</div>';
        html += '</div>';

        return html;
    }

    // Render a single code line
    function renderCodeLine(lineNum, content, isMatch) {
        const className = isMatch ? 'match' : 'context';
        return `
            <div class="code-line ${className}">
                <div class="line-number">${lineNum}</div>
                <div class="line-content">${escapeHtml(content)}</div>
            </div>
        `;
    }

    // Attach click handlers to open buttons
    function attachOpenButtons() {
        const buttons = document.querySelectorAll('.open-in-editor');
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                const filePath = btn.getAttribute('data-file');
                const lineNumber = btn.getAttribute('data-line');
                openInEditor(filePath, lineNumber);
            });
        });
    }

    // Open file in VS Code at specific line
    function openInEditor(filePath, lineNumber) {
        // Use VS Code URL scheme
        // Format: vscode://file/PATH:LINE
        const url = `vscode://file/${encodeURIComponent(filePath)}:${lineNumber}`;
        
        // Try to open
        window.location.href = url;
        
        // Show confirmation
        updateStatus(`Opening ${filePath}:${lineNumber} in VS Code...`, 'success');
    }

    // Clear results
    function clearResults() {
        searchInput.value = '';
        searchResults.innerHTML = `
            <div class="empty-state">
                <p>Enter a search query to find code across your project.</p>
                <div class="examples">
                    <p class="examples-title">Examples:</p>
                    <ul>
                        <li><code>def calculate_position</code> - Find function definitions</li>
                        <li><code>import schwab_api</code> - Find imports</li>
                        <li><code>TODO|FIXME</code> - Find comments (use Regex)</li>
                        <li><code>API_KEY</code> - Find config references</li>
                    </ul>
                </div>
            </div>
        `;
        updateStatus('', '');
        searchInput.focus();
    }

    // Update status message
    function updateStatus(message, type) {
        if (!message) {
            searchStatus.classList.remove('visible', 'error', 'success');
            searchStatus.textContent = '';
            return;
        }

        searchStatus.textContent = message;
        searchStatus.classList.add('visible');
        searchStatus.classList.remove('error', 'success');
        
        if (type) {
            searchStatus.classList.add(type);
        }
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
