# LogViewer

Flask-based web interface for viewing and searching log files. Auto-discovers logs from project root and provides live tail, search, filtering, and favorites.

## Features

- **Auto-discovery** - Walks up 2 levels to find project root, scans for all `.log` files
- **Live tail** - Auto-refreshes at configurable intervals
- **Search** - Full-text search with regex support
- **Filter** - Filter by log level (ERROR, WARNING, INFO, DEBUG)
- **Favorites** - Star frequently-viewed logs for quick access
- **Dark theme** - Clean, easy-on-the-eyes interface
- **Zero config** - Drop it anywhere, it figures out the rest

## Installation

**Requirements:**
- Python 3.9+
- Flask (`pip install flask`)

**Deploy:**
1. Extract to `C:\auto_trading\bots\trailboss\tools\LogViewer\`
2. Install Flask: `pip install flask`
3. Done!

## Project Structure

By default, LogViewer assumes it lives 2 levels below project root:

```
trailboss/                    ← Project root (scans from here)
  logs/                       ← Finds .log files
  bots/
    marshybot/logs/           ← And here
    trailboss/logs/           ← And here
  tools/
    LogViewer/                ← Lives here
      app.py                  ← Main Flask app
      run.bat                 ← Double-click launcher
```

## Usage

### Quick Start
```bash
# Option 1: Double-click
run.bat

# Option 2: Command line
python app.py
```

Opens browser at `http://localhost:5000`

### Interface

**Main page:**
- Lists all discovered log files grouped by directory
- Shows file size and last modified time
- Click any log to open viewer

**Log viewer:**
- Live tail (auto-refreshes every 2 seconds by default)
- Search with plain text or regex
- Filter by log level (ERROR/WARNING/INFO/DEBUG)
- Adjust tail lines (50/100/200/500/1000)
- Favorite logs for quick access
- Download log files

### Features in Detail

#### Live Tail
- Automatically refreshes log content
- Toggle with "Auto" checkbox
- Manual refresh with 🔄 button
- Configurable interval in `config.json`

#### Search
1. Click "🔍 Search" button
2. Enter search query
3. Optional: Enable regex or case-sensitive
4. Click "Search"
5. Results show matching lines with line numbers

#### Filtering
- Use "Filter" dropdown to show only specific log levels
- Filters current view without reloading file
- Combines with tail lines setting

#### Favorites
- Click "☆ Favorite" to star a log
- Favorited logs appear in special section on main page
- Persisted in `config.json`

## Configuration

Edit `config.json` to customize:

```json
{
  "levels_up_to_root": 2,           // How many levels to walk up
  "log_patterns": ["*.log"],         // File patterns to match
  "exclude_dirs": [...],             // Directories to skip
  "tail_lines": 100,                 // Default tail lines
  "refresh_interval_ms": 2000,       // Auto-refresh interval
  "max_file_size_mb": 100,           // Max file size to view
  "favorites": []                     // Favorited log paths
}
```

### Configuration Options

**levels_up_to_root**
- Number of directory levels to traverse up to find project root
- Default: 2 (for `tools/LogViewer/` → `trailboss/`)
- Adjust if deployed at different depth

**log_patterns**
- List of filename patterns to match
- Supports wildcards (e.g., `["*.log", "*.txt"]`)
- Default: `["*.log"]`

**exclude_dirs**
- Directory names to skip during scanning
- Default: `__pycache__`, `.git`, `venv`, etc.

**tail_lines**
- Default number of lines to show in tail
- Can be overridden in viewer interface
- Default: 100

**refresh_interval_ms**
- Auto-refresh interval in milliseconds
- Default: 2000 (2 seconds)

**max_file_size_mb**
- Maximum file size in MB to allow viewing
- Large files are excluded from discovery
- Default: 100 MB

**favorites**
- Automatically managed by favorite toggle
- Stores relative paths from project root
- Don't edit manually

## File Structure

```
LogViewer/
├── core/
│   ├── __init__.py          # Package init
│   ├── config.py            # Configuration management (~120 lines)
│   ├── path_resolver.py     # Project root detection (~50 lines)
│   └── log_scanner.py       # Log file discovery (~180 lines)
├── templates/
│   ├── base.html            # Layout template
│   ├── index.html           # Log file browser
│   └── viewer.html          # Log viewer interface
├── static/
│   ├── css/
│   │   └── style.css        # Dark theme styling
│   └── js/
│       └── viewer.js        # Client-side functionality
├── app.py                   # Flask application (~320 lines)
├── run.bat                  # Launcher script
├── config.json              # Configuration
└── README.md                # This file
```

## API Endpoints

### GET /
Main page showing all discovered log files

### GET /view/<path>
Log viewer interface for specific log file

### GET /api/tail/<path>
Tail last N lines of log file

**Query params:**
- `lines` - Number of lines to return (default: config.tail_lines)

**Response:**
```json
{
  "lines": ["line1", "line2", ...],
  "path": "logs/trailboss.log"
}
```

### GET /api/search/<path>
Search within a log file

**Query params:**
- `q` - Search query (required)
- `regex` - If `1`, treat query as regex pattern
- `case` - If `1`, case-sensitive search

**Response:**
```json
{
  "matches": [
    {"line_number": 42, "text": "ERROR: Something broke"},
    ...
  ],
  "query": "ERROR",
  "count": 15
}
```

### POST /api/favorite/<path>
Toggle favorite status of a log file

**Response:**
```json
{
  "path": "logs/trailboss.log",
  "is_favorite": true
}
```

### GET /api/download/<path>
Download a log file

## Design Principles

Following Marshall's engineering rules:

- **Single source of truth** - Each piece of logic exists in exactly one place
- **Separation of concerns** - Core logic, Flask routes, templates, static files all separated
- **Config externalized** - All settings in `config.json`, zero hardcoded values
- **Complete working code** - No stubs, all imports resolve
- **Modular** - Each file <400 lines, clear responsibility

## Troubleshooting

**No logs showing up:**
- Check `config.json` → `levels_up_to_root` is correct
- Verify log files exist in scanned directories
- Check `log_patterns` matches your file names
- Look at console output showing project root

**Page won't load:**
- Install Flask: `pip install flask`
- Check if port 5000 is already in use
- Try different port: edit `app.py` and change `port=5000`

**Auto-refresh not working:**
- Check browser console for JavaScript errors
- Verify `refresh_interval_ms` in `config.json` is valid
- Try manual refresh with 🔄 button

**Search returns no results:**
- Verify search query is correct
- Try case-insensitive search (uncheck "Case sensitive")
- Check if log file is too large (exceeds `max_file_size_mb`)

**Favorites not persisting:**
- Verify `config.json` is writable
- Check file permissions on LogViewer directory

## Color Scheme

Uses Marshall's dark theme from STYLE_REFERENCE:

- Background: `#0d1117` (bg_dark)
- Panels: `#161b22` (bg_panel)
- Inputs: `#21262d` (bg_input)
- Borders: `#30363d`
- Text: `#c9d1d9`
- Dim text: `#8b949e`
- ERROR: `#f85149` (red)
- WARNING: `#f0883e` (orange)
- INFO: `#58a6ff` (blue)
- DEBUG: `#8b949e` (dim)
- Accent: `#39c5cf` (cyan)

## Tips & Tricks

**Keyboard shortcuts:**
- Enter in search box → Execute search
- Click log line → (future: jump to context)

**Performance:**
- Large logs? Reduce tail lines to 50 or 100
- Slow search? Try more specific queries
- Many logs? Use favorites to focus on important ones

**Workflow examples:**

**Debugging a crash:**
1. Open crashed bot's log
2. Filter by "ERROR"
3. Search for specific error message
4. Download filtered results for sharing

**Monitoring live activity:**
1. Open log in viewer
2. Enable auto-refresh
3. Watch updates roll in
4. Favorite for quick access

**Comparing logs:**
1. Open first log in tab 1
2. Open second log in tab 2
3. Search same query in both
4. Compare results side-by-side

## Future Enhancements

Potential features for future versions:

- Multiple log tail (view 2+ logs simultaneously)
- Export filtered/searched results
- Jump to timestamp
- Syntax highlighting for structured logs (JSON)
- Log analytics (error frequency, etc.)
- WebSocket for real-time streaming
- Dark/light theme toggle

## License

Use freely. No attribution required.

## Support

Check `app.py` console output for debugging info.

File issues or questions in project documentation.
