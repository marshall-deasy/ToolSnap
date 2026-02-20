// DependencyAnalyzer JavaScript - Analysis and cleanup workflow

(function() {
    'use strict';

    // State
    let currentAnalysis = null;

    // DOM elements
    const folderItems = document.querySelectorAll('.folder-item');
    const customPath = document.getElementById('customPath');
    const analyzeCustomBtn = document.getElementById('analyzeCustomBtn');
    const analysisStatus = document.getElementById('analysisStatus');
    const analysisResults = document.getElementById('analysisResults');

    // Config from template
    const config = window.analyzerConfig;

    // Initialize
    function init() {
        setupEventListeners();
    }

    function setupEventListeners() {
        // Folder item clicks
        folderItems.forEach(item => {
            item.addEventListener('click', () => {
                const path = item.getAttribute('data-path');
                analyzePath(path);
            });
        });

        // Custom path analysis
        analyzeCustomBtn.addEventListener('click', () => {
            const path = customPath.value.trim();
            if (path) {
                analyzePath(path);
            }
        });

        customPath.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const path = customPath.value.trim();
                if (path) {
                    analyzePath(path);
                }
            }
        });
    }

    // Analyze a folder path
    async function analyzePath(targetFolder) {
        // Show loading status
        analysisStatus.style.display = 'block';
        analysisStatus.className = 'analysis-status loading';
        analysisStatus.textContent = `Analyzing ${targetFolder}...`;
        analysisResults.style.display = 'none';

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    target_folder: targetFolder,
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }

            const data = await response.json();
            currentAnalysis = data;
            displayResults(data);

        } catch (error) {
            analysisStatus.className = 'analysis-status error';
            analysisStatus.textContent = `Error: ${error.message}`;
        }
    }

    // Display analysis results
    function displayResults(data) {
        // Update status
        analysisStatus.className = 'analysis-status success';
        analysisStatus.textContent = 'Analysis complete!';

        // Calculate totals
        const categories = data.categories;
        const totals = {
            active: categories.active.length,
            orphaned: categories.orphaned.length,
            scripts: categories.scripts.length,
            outputs: categories.outputs.length,
            temp: categories.temp.length,
            shortcuts: categories.shortcuts.length,
            duplicates: categories.duplicates.length,
            unknown: categories.unknown.length,
        };

        // Build results HTML
        let html = '';

        // Header with summary
        html += `
            <div class="result-header">
                <h2>Analysis Results: ${data.target_folder}</h2>
                <p class="hint">Entry points: ${data.entry_points.join(', ')}</p>
                <div class="result-summary">
                    <div class="summary-item">
                        <span class="summary-value">${totals.active}</span>
                        <span class="summary-label">Active Files</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-value">${totals.orphaned}</span>
                        <span class="summary-label">Orphaned</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-value">${totals.scripts}</span>
                        <span class="summary-label">Scripts</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-value">${totals.outputs}</span>
                        <span class="summary-label">Outputs</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-value">${totals.temp + totals.shortcuts + totals.duplicates}</span>
                        <span class="summary-label">Cleanable</span>
                    </div>
                </div>
            </div>
        `;

        // Category sections
        html += renderCategory('Active Files', 'active', categories.active, 'These files are in the import chain and should be kept.', false);
        html += renderCategory('Orphaned Python Files', 'orphaned', categories.orphaned, 'Python files not imported. Archive these if not needed.', true);
        html += renderCategory('Script Files', 'scripts', categories.scripts, 'Batch and PowerShell scripts. Move to scripts/ folder.', true);
        html += renderCategory('Output Files', 'outputs', categories.outputs, 'Generated output files. Move to output/ folder.', true);
        html += renderCategory('Temporary Files', 'temp', categories.temp, 'Compiled Python files. Safe to delete.', true);
        html += renderCategory('Shortcuts', 'shortcuts', categories.shortcuts, 'Shortcut files. Safe to delete.', true);
        html += renderCategory('Duplicates', 'duplicates', categories.duplicates, 'Backup and duplicate files. Archive or delete.', true);
        html += renderCategory('Unknown Files', 'unknown', categories.unknown, 'Uncategorized files. Review manually.', false);

        // Execute button
        html += `
            <div style="text-align: center; margin-top: 24px;">
                <button id="executeCleanupBtn" class="btn btn-green" style="padding: 12px 32px; font-size: 15px;">
                    Execute Cleanup
                </button>
            </div>
        `;

        analysisResults.innerHTML = html;
        analysisResults.style.display = 'block';

        // Attach event listener to execute button
        document.getElementById('executeCleanupBtn').addEventListener('click', executeCleanup);
    }

    // Render a category section
    function renderCategory(title, categoryId, files, description, hasActions) {
        if (files.length === 0) {
            return '';
        }

        let html = `
            <div class="category-section" data-category="${categoryId}">
                <div class="category-header">
                    <div>
                        <div class="category-title">${title}</div>
                        <div class="category-count">${files.length} file${files.length !== 1 ? 's' : ''}</div>
                    </div>
                    ${hasActions ? `
                        <div class="category-actions">
                            <button class="btn btn-secondary select-all-btn" data-category="${categoryId}">Select All</button>
                        </div>
                    ` : ''}
                </div>
                <div class="category-content">
                    <p class="hint" style="margin-bottom: 12px;">${description}</p>
                    <div class="file-list">
        `;

        files.forEach(file => {
            html += `
                <div class="file-item">
                    <div class="file-info">
                        <div class="file-name">${escapeHtml(file.filename)}</div>
                        <div class="file-meta">${file.size} • Modified: ${file.modified} • ${file.reason}</div>
                    </div>
                    ${hasActions ? `
                        <input type="checkbox" class="file-checkbox" data-category="${categoryId}" data-filepath="${escapeHtml(file.filepath)}" checked>
                    ` : ''}
                </div>
            `;
        });

        html += `
                    </div>
                </div>
            </div>
        `;

        // Attach select-all event listeners after render
        setTimeout(() => {
            const selectAllBtn = document.querySelector(`.select-all-btn[data-category="${categoryId}"]`);
            if (selectAllBtn) {
                selectAllBtn.addEventListener('click', () => {
                    const checkboxes = document.querySelectorAll(`.file-checkbox[data-category="${categoryId}"]`);
                    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
                    checkboxes.forEach(cb => cb.checked = !allChecked);
                    selectAllBtn.textContent = allChecked ? 'Select All' : 'Deselect All';
                });
            }
        }, 0);

        return html;
    }

    // Execute cleanup
    async function executeCleanup() {
        if (!currentAnalysis) {
            return;
        }

        if (!confirm('Are you sure you want to execute the cleanup? Files will be moved/archived.')) {
            return;
        }

        // Collect selected files by category
        const actions = {};
        const checkboxes = document.querySelectorAll('.file-checkbox:checked');

        checkboxes.forEach(cb => {
            const category = cb.getAttribute('data-category');
            const filepath = cb.getAttribute('data-filepath');

            if (!actions[category]) {
                actions[category] = [];
            }
            actions[category].push(filepath);
        });

        // Show loading
        analysisStatus.className = 'analysis-status loading';
        analysisStatus.textContent = 'Executing cleanup...';

        try {
            const response = await fetch('/api/execute_cleanup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    target_folder: currentAnalysis.target_folder,
                    actions: actions,
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }

            const results = await response.json();
            displayExecutionResults(results);

        } catch (error) {
            analysisStatus.className = 'analysis-status error';
            analysisStatus.textContent = `Error: ${error.message}`;
        }
    }

    // Display execution results
    function displayExecutionResults(results) {
        analysisStatus.className = 'analysis-status success';
        analysisStatus.textContent = 'Cleanup completed successfully!';

        const html = `
            <div class="execution-summary">
                <h3>Cleanup Summary</h3>
                <div class="execution-stat">Archived: ${results.archived.length} file(s)</div>
                <div class="execution-stat">Moved: ${results.moved.length} file(s)</div>
                <div class="execution-stat">Deleted: ${results.deleted.length} file(s)</div>
                ${results.errors.length > 0 ? `<div class="execution-stat" style="color: var(--red);">Errors: ${results.errors.length}</div>` : ''}
                <div style="margin-top: 16px; text-align: center;">
                    <button class="btn btn-blue" onclick="window.location.reload()">Analyze Another Folder</button>
                </div>
            </div>
        `;

        analysisResults.innerHTML = html;
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
