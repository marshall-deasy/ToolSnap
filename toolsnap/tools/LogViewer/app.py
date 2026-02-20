"""
LogViewer Flask application.

Auto-discovers log files from project root and provides web interface for viewing.
"""

import os
import sys
from flask import Flask, render_template, jsonify, request, send_file
from core import Config, PathResolver, LogScanner

# ---------------------------------------------------------------------------
# Self-awareness - where am I?
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

# ---------------------------------------------------------------------------
# Initialize app and core components
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = 'logviewer-secret-key'

# Add custom Jinja2 filters
@app.template_filter('basename')
def basename_filter(path):
    """Get basename of a path."""
    return os.path.basename(path)

@app.template_filter('dirname')
def dirname_filter(path):
    """Get dirname of a path."""
    return os.path.dirname(path)

# Load configuration
config = Config(CONFIG_PATH)

# Detect project root
path_resolver = PathResolver(SCRIPT_DIR, config.levels_up_to_root)
PROJECT_ROOT = path_resolver.get_project_root()

# Initialize log scanner
log_scanner = LogScanner(
    PROJECT_ROOT,
    config.log_patterns,
    config.exclude_dirs,
    config.max_file_size_mb,
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Show list of all discovered log files."""
    # Scan for log files
    log_files = log_scanner.scan()
    grouped = log_scanner.group_by_directory(log_files)

    # Sort directories
    sorted_dirs = sorted(grouped.keys())

    return render_template(
        'index.html',
        project_root=PROJECT_ROOT,
        grouped_logs=grouped,
        sorted_dirs=sorted_dirs,
        favorites=config.favorites,
    )


@app.route('/view/<path:log_path>')
def view_log(log_path):
    """
    Show log viewer interface for a specific log file.

    Args:
        log_path: Relative path to log file from project root
    """
    absolute_path = os.path.join(PROJECT_ROOT, log_path)

    # Verify file exists and is readable
    if not os.path.isfile(absolute_path):
        return f"Log file not found: {log_path}", 404

    # Get file metadata
    try:
        stat = os.stat(absolute_path)
        size_mb = stat.st_size / (1024 * 1024)
    except OSError:
        size_mb = 0

    is_favorite = log_path in config.favorites

    return render_template(
        'viewer.html',
        log_path=log_path,
        log_name=os.path.basename(log_path),
        size_mb=size_mb,
        is_favorite=is_favorite,
        refresh_interval=config.refresh_interval_ms,
        tail_lines=config.tail_lines,
    )


@app.route('/api/tail/<path:log_path>')
def api_tail(log_path):
    """
    API endpoint to tail last N lines of a log file.

    Query params:
        lines: Number of lines to return (default: config.tail_lines)

    Returns:
        JSON with lines array
    """
    absolute_path = os.path.join(PROJECT_ROOT, log_path)

    if not os.path.isfile(absolute_path):
        return jsonify({'error': 'File not found'}), 404

    # Get number of lines to tail
    lines = request.args.get('lines', config.tail_lines, type=int)

    try:
        content_lines = _tail_file(absolute_path, lines)
        return jsonify({
            'lines': content_lines,
            'path': log_path,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search/<path:log_path>')
def api_search(log_path):
    """
    API endpoint to search within a log file.

    Query params:
        q: Search query (plain text or regex)
        regex: If 1, treat q as regex pattern
        case: If 1, case-sensitive search

    Returns:
        JSON with matching lines
    """
    absolute_path = os.path.join(PROJECT_ROOT, log_path)

    if not os.path.isfile(absolute_path):
        return jsonify({'error': 'File not found'}), 404

    query = request.args.get('q', '')
    use_regex = request.args.get('regex', '0') == '1'
    case_sensitive = request.args.get('case', '0') == '1'

    if not query:
        return jsonify({'error': 'No search query provided'}), 400

    try:
        matches = _search_file(absolute_path, query, use_regex, case_sensitive)
        return jsonify({
            'matches': matches,
            'query': query,
            'count': len(matches),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/favorite/<path:log_path>', methods=['POST'])
def api_toggle_favorite(log_path):
    """
    Toggle favorite status of a log file.

    Returns:
        JSON with new favorite status
    """
    if log_path in config.favorites:
        config.remove_favorite(log_path)
        is_favorite = False
    else:
        config.add_favorite(log_path)
        is_favorite = True

    return jsonify({
        'path': log_path,
        'is_favorite': is_favorite,
    })


@app.route('/api/download/<path:log_path>')
def api_download(log_path):
    """
    Download a log file.

    Returns:
        File download response
    """
    absolute_path = os.path.join(PROJECT_ROOT, log_path)

    if not os.path.isfile(absolute_path):
        return "File not found", 404

    return send_file(
        absolute_path,
        as_attachment=True,
        download_name=os.path.basename(log_path),
    )


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _tail_file(filepath: str, num_lines: int) -> list:
    """
    Read last N lines from a file efficiently.

    Args:
        filepath: Path to file
        num_lines: Number of lines to read from end

    Returns:
        List of lines (strings)
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            return [line.rstrip('\n\r') for line in lines[-num_lines:]]
    except Exception:
        # Fallback for large files - read from end
        return _tail_large_file(filepath, num_lines)


def _tail_large_file(filepath: str, num_lines: int) -> list:
    """
    Tail large file by reading from end.

    Args:
        filepath: Path to file
        num_lines: Number of lines to read

    Returns:
        List of lines
    """
    buffer_size = 8192
    lines = []

    with open(filepath, 'rb') as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        position = file_size

        while len(lines) < num_lines and position > 0:
            # Move back by buffer_size
            position = max(0, position - buffer_size)
            f.seek(position)
            chunk = f.read(min(buffer_size, file_size - position))

            # Decode and split into lines
            try:
                text = chunk.decode('utf-8', errors='replace')
            except Exception:
                text = str(chunk)

            chunk_lines = text.split('\n')
            lines = chunk_lines + lines

        # Return last N lines
        return [line.rstrip('\r') for line in lines[-num_lines:] if line]


def _search_file(filepath: str, query: str, use_regex: bool, case_sensitive: bool) -> list:
    """
    Search file for matching lines.

    Args:
        filepath: Path to file
        query: Search query
        use_regex: If True, treat query as regex
        case_sensitive: If True, case-sensitive search

    Returns:
        List of dicts with line_number and text
    """
    import re

    matches = []

    # Compile regex if needed
    if use_regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(query, flags)
        except re.error:
            return []
    else:
        query_compare = query if case_sensitive else query.lower()

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for line_num, line in enumerate(f, 1):
                line_stripped = line.rstrip('\n\r')

                # Check if line matches
                if use_regex:
                    if pattern.search(line_stripped):
                        matches.append({
                            'line_number': line_num,
                            'text': line_stripped,
                        })
                else:
                    line_compare = line_stripped if case_sensitive else line_stripped.lower()
                    if query_compare in line_compare:
                        matches.append({
                            'line_number': line_num,
                            'text': line_stripped,
                        })

                # Limit results to prevent huge responses
                if len(matches) >= 1000:
                    break

    except Exception:
        pass

    return matches


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """Run the Flask development server."""
    print("=" * 70)
    print("LogViewer - Starting Flask Server")
    print("=" * 70)
    print()
    print(f"Script directory:  {SCRIPT_DIR}")
    print(f"Project root:      {PROJECT_ROOT}")
    print(f"Config:            {CONFIG_PATH}")
    print()
    print("Scanning for log files...")

    log_files = log_scanner.scan()
    print(f"Found {len(log_files)} log file(s)")
    print()
    print("Server starting at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == "__main__":
    main()
