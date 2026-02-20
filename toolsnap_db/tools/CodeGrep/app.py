"""
CodeGrep Flask application.

Auto-discovers code files from project root and provides search interface.
"""

import os
import sys
import webbrowser
from threading import Timer
from flask import Flask, render_template, jsonify, request
from core import Config, PathResolver, CodeScanner

# ---------------------------------------------------------------------------
# Self-awareness - where am I?
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

# ---------------------------------------------------------------------------
# Initialize app and core components
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = 'codegrep-secret-key'

# Load configuration
config = Config(CONFIG_PATH)

# Detect project root
path_resolver = PathResolver(SCRIPT_DIR, config.levels_up_to_root)
PROJECT_ROOT = path_resolver.get_project_root()

# Initialize code scanner
code_scanner = CodeScanner(
    PROJECT_ROOT,
    config.file_patterns,
    config.exclude_dirs,
    config.exclude_files,
    config.context_lines,
    config.max_results,
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Show search interface with project info."""
    # Get file statistics
    code_files = code_scanner.get_code_files()
    file_stats = code_scanner.get_file_stats()

    return render_template(
        'index.html',
        project_root=PROJECT_ROOT,
        total_files=len(code_files),
        file_stats=file_stats,
        context_lines=config.context_lines,
        max_results=config.max_results,
        config=config,
    )


@app.route('/api/search', methods=['POST'])
def api_search():
    """
    API endpoint to search code files.

    JSON body:
        query: Search query string
        regex: Boolean, use regex
        case_sensitive: Boolean, case-sensitive search
        whole_word: Boolean, match whole words only

    Returns:
        JSON with search results
    """
    data = request.get_json()

    query = data.get('query', '').strip()
    use_regex = data.get('regex', False)
    case_sensitive = data.get('case_sensitive', False)
    whole_word = data.get('whole_word', False)

    if not query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        results = code_scanner.search(
            query,
            use_regex=use_regex,
            case_sensitive=case_sensitive,
            whole_word=whole_word,
        )

        # Convert to JSON-serializable format
        results_data = [r.to_dict() for r in results]

        return jsonify({
            'results': results_data,
            'query': query,
            'count': len(results),
            'truncated': len(results) >= config.max_results,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/files')
def api_files():
    """
    API endpoint to get list of all code files.

    Returns:
        JSON with file list and statistics
    """
    code_files = code_scanner.get_code_files()
    file_stats = code_scanner.get_file_stats()

    # Get relative paths
    relative_files = [
        path_resolver.get_relative_path(f, PROJECT_ROOT)
        for f in code_files
    ]

    return jsonify({
        'files': relative_files,
        'total': len(code_files),
        'stats': file_stats,
    })


@app.route('/api/refresh')
def api_refresh():
    """
    API endpoint to refresh file cache.

    Returns:
        JSON with updated file count
    """
    code_files = code_scanner.get_code_files(force_refresh=True)

    return jsonify({
        'total_files': len(code_files),
        'message': 'File cache refreshed',
    })


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """Run the Flask development server."""
    print("=" * 70)
    print("CodeGrep - Starting Flask Server")
    print("=" * 70)
    print()
    print(f"Script directory:  {SCRIPT_DIR}")
    print(f"Project root:      {PROJECT_ROOT}")
    print(f"Config:            {CONFIG_PATH}")
    print()
    print("Scanning for code files...")

    code_files = code_scanner.get_code_files()
    file_stats = code_scanner.get_file_stats()

    print(f"Found {len(code_files)} code file(s)")
    for ext, count in sorted(file_stats.items()):
        print(f"  {ext}: {count}")
    print()
    print("Server starting at: http://localhost:5001")
    print("Opening browser...")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    # Auto-open browser after 1.5 seconds (gives Flask time to start)
    def open_browser():
        webbrowser.open('http://localhost:5001')
    
    Timer(1.5, open_browser).start()

    app.run(host='0.0.0.0', port=5001, debug=True)


if __name__ == "__main__":
    main()
