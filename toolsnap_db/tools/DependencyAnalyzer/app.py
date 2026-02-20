"""
DependencyAnalyzer Flask application.

Analyzes Python project folders to find active vs. orphaned files.
"""

import os
import sys
import shutil
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from core import Config, PathResolver, EntryFinder, ImportTracer, Categorizer

# ---------------------------------------------------------------------------
# Self-awareness - where am I?
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

# ---------------------------------------------------------------------------
# Initialize app and core components
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dependency-analyzer-secret-key'

# Load configuration
config = Config(CONFIG_PATH)

# Detect project root
path_resolver = PathResolver(SCRIPT_DIR, config.levels_up_to_root)
PROJECT_ROOT = path_resolver.get_project_root()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Show folder selection interface."""
    # Find bot folders in project
    bots_dir = os.path.join(PROJECT_ROOT, 'bots')
    available_folders = []

    if os.path.isdir(bots_dir):
        for item in os.listdir(bots_dir):
            item_path = os.path.join(bots_dir, item)
            if os.path.isdir(item_path):
                available_folders.append({
                    'name': item,
                    'path': item_path,
                })

    return render_template(
        'index.html',
        project_root=PROJECT_ROOT,
        available_folders=available_folders,
    )


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """
    API endpoint to analyze a folder.

    JSON body:
        target_folder: Path to folder to analyze

    Returns:
        JSON with analysis results
    """
    data = request.get_json()
    target_folder = data.get('target_folder', '').strip()

    if not target_folder or not os.path.isdir(target_folder):
        return jsonify({'error': 'Invalid folder path'}), 400

    try:
        # Find entry points
        entry_finder = EntryFinder(target_folder)
        entry_points = entry_finder.find_entry_points()

        if not entry_points:
            return jsonify({'error': 'No entry points found (.bat files or main.py)'}), 400

        # Trace imports from entry points
        import_tracer = ImportTracer(target_folder, config.exclude_from_analysis)
        active_files = import_tracer.trace_from_entry_points(entry_points)

        # Categorize all files
        categorizer = Categorizer(
            target_folder,
            active_files,
            config.file_categories,
            config.exclude_from_analysis,
        )
        categorized = categorizer.categorize_all_files()

        # Convert to JSON-serializable format
        result = {
            'target_folder': target_folder,
            'entry_points': [path_resolver.get_relative_path(ep, target_folder) for ep in entry_points],
            'categories': {},
        }

        for category, files in categorized.items():
            result['categories'][category] = [f.to_dict() for f in files]

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/execute_cleanup', methods=['POST'])
def api_execute_cleanup():
    """
    API endpoint to execute cleanup operations.

    JSON body:
        target_folder: Path to folder to clean
        actions: Dictionary mapping category to action (archive, move, delete)

    Returns:
        JSON with execution results
    """
    data = request.get_json()
    target_folder = data.get('target_folder', '').strip()
    actions = data.get('actions', {})

    if not target_folder or not os.path.isdir(target_folder):
        return jsonify({'error': 'Invalid folder path'}), 400

    try:
        results = {
            'archived': [],
            'moved': [],
            'deleted': [],
            'errors': [],
        }

        # Create timestamped archive folder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_root = os.path.join(target_folder, config.archive_folder)
        archive_folder = os.path.join(archive_root, f'orphaned_{timestamp}')

        # Create destination folders as needed
        scripts_folder = os.path.join(target_folder, config.scripts_folder)
        output_folder = os.path.join(target_folder, config.output_folder)

        # Process each action
        for category, files in actions.items():
            if category == 'orphaned':
                # Archive orphaned files
                if not os.path.exists(archive_folder):
                    os.makedirs(archive_folder)

                for filepath in files:
                    try:
                        filename = os.path.basename(filepath)
                        dest = os.path.join(archive_folder, filename)
                        shutil.move(filepath, dest)
                        results['archived'].append(filepath)
                    except Exception as e:
                        results['errors'].append(f"{filepath}: {str(e)}")

            elif category == 'scripts':
                # Move scripts to scripts folder
                if not os.path.exists(scripts_folder):
                    os.makedirs(scripts_folder)

                for filepath in files:
                    try:
                        filename = os.path.basename(filepath)
                        dest = os.path.join(scripts_folder, filename)
                        shutil.move(filepath, dest)
                        results['moved'].append(filepath)
                    except Exception as e:
                        results['errors'].append(f"{filepath}: {str(e)}")

            elif category == 'outputs':
                # Move outputs to output folder
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)

                for filepath in files:
                    try:
                        filename = os.path.basename(filepath)
                        dest = os.path.join(output_folder, filename)
                        shutil.move(filepath, dest)
                        results['moved'].append(filepath)
                    except Exception as e:
                        results['errors'].append(f"{filepath}: {str(e)}")

            elif category in ['temp', 'shortcuts', 'duplicates']:
                # Delete temp/shortcut/duplicate files
                for filepath in files:
                    try:
                        os.remove(filepath)
                        results['deleted'].append(filepath)
                    except Exception as e:
                        results['errors'].append(f"{filepath}: {str(e)}")

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """Run the Flask development server."""
    print("=" * 70)
    print("DependencyAnalyzer - Starting Flask Server")
    print("=" * 70)
    print()
    print(f"Script directory:  {SCRIPT_DIR}")
    print(f"Project root:      {PROJECT_ROOT}")
    print(f"Config:            {CONFIG_PATH}")
    print()
    print("Server starting at: http://localhost:5002")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    app.run(host='0.0.0.0', port=5002, debug=True)


if __name__ == "__main__":
    main()
