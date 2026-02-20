# LogViewer - Deployment Summary

## What You're Getting

**Complete Flask-based log viewer** that auto-discovers and displays log files from your project with live tail, search, filtering, and favorites.

## File Structure

```
LogViewer/
├── core/                          [Business Logic]
│   ├── __init__.py               Package initialization
│   ├── config.py                 Configuration management (~120 lines)
│   ├── path_resolver.py          Project root detection (~50 lines)
│   └── log_scanner.py            Log file discovery (~180 lines)
├── templates/                     [UI Templates]
│   ├── base.html                 Layout shell with dark theme
│   ├── index.html                Log file browser
│   └── viewer.html               Log viewer interface
├── static/                        [Client-side Assets]
│   ├── css/
│   │   └── style.css             Dark theme (your color palette)
│   └── js/
│       └── viewer.js             Live tail, search, filtering
├── app.py                        Flask application (~330 lines)
├── run.bat                       Double-click launcher
├── config.json                   Configuration settings
└── README.md                     Complete documentation
```

## Key Features

### 1. Auto-Discovery (PRIMARY FEATURE)
- **Walks up 2 levels** from script location to find project root
- **Recursively scans** for all `.log` files
- **Zero configuration** - just drop it in `tools/LogViewer/` and run

### 2. Live Tail
- Auto-refreshes every 2 seconds (configurable)
- Adjustable tail lines (50/100/200/500/1000)
- Manual refresh button
- Auto-scroll to bottom

### 3. Search & Filter
- **Full-text search** with plain text or regex
- **Case-sensitive** option
- **Filter by level** (ERROR/WARNING/INFO/DEBUG)
- Shows line numbers for matches

### 4. Favorites
- Star frequently-viewed logs
- Quick access from main page
- Persisted in config.json

### 5. Dark Theme
- Uses your STYLE_REFERENCE color palette
- Clean, flat hierarchy
- Easy on the eyes for long sessions

## Installation

### 1. Install Flask
```bash
pip install flask
```

### 2. Deploy Files
Extract `LV_latest.zip` to: `C:\auto_trading\bots\trailboss\tools\LogViewer\`

Your structure should be:
```
trailboss/
  tools/
    LogViewer/
      app.py
      run.bat
      core/
      templates/
      static/
      ...
```

### 3. Run It
```bash
# Option 1: Double-click
run.bat

# Option 2: Command line
cd C:\auto_trading\bots\trailboss\tools\LogViewer
python app.py
```

Opens browser at `http://localhost:5000`

## What It Does

### Startup Sequence
1. **Detects location** → `tools/LogViewer/`
2. **Walks up 2 levels** → finds `trailboss/`
3. **Scans recursively** → finds all `.log` files
4. **Groups by directory** → organizes display
5. **Starts Flask server** → `http://localhost:5000`

### Discovered Logs
Will find logs in:
- `trailboss/logs/`
- `trailboss/bots/marshybot/logs/`
- `trailboss/bots/trailboss/logs/`
- Any other subdirectory (excluding `__pycache__`, `.git`, etc.)

### Main Page
- Lists all log files grouped by directory
- Shows file size and last modified time
- Favorites section at top
- Click any log to view

### Log Viewer
- **Controls:**
  - ← Back (return to list)
  - 🔍 Search (toggle search panel)
  - ⭐/☆ Favorite (toggle favorite)
  - ⬇ Download (download log file)
  - 🔄 Refresh (manual reload)
  - Auto checkbox (toggle auto-refresh)

- **Filters:**
  - Level filter (All/ERROR/WARNING/INFO/DEBUG)
  - Lines selector (50/100/200/500/1000)

- **Content:**
  - Color-coded by level (ERROR=red, WARNING=orange, INFO=blue)
  - Monospace font (Consolas)
  - Auto-scrolls to bottom
  - Preserves formatting

## Configuration

Edit `config.json` to customize:

```json
{
  "levels_up_to_root": 2,           // Walk up 2 levels to find root
  "log_patterns": ["*.log"],         // File patterns to match
  "exclude_dirs": [...],             // Skip these directories
  "tail_lines": 100,                 // Default tail lines
  "refresh_interval_ms": 2000,       // Auto-refresh interval (ms)
  "max_file_size_mb": 100,           // Max file size to view
  "favorites": []                     // Auto-managed by UI
}
```

## Engineering Rules Compliance

✅ **Single source of truth** - Each piece of logic in one place
✅ **No copy-paste** - Shared logic in core modules
✅ **Complete working code** - No stubs, all imports resolve
✅ **Modular** - Each file <400 lines, clear responsibility
✅ **GUI/logic separated** - Templates have no business logic
✅ **Config externalized** - All settings in config.json

## File Breakdown

### app.py (~330 lines)
**Routes:**
- `GET /` - Main page (log file browser)
- `GET /view/<path>` - Log viewer interface
- `GET /api/tail/<path>` - Tail endpoint (returns JSON)
- `GET /api/search/<path>` - Search endpoint (returns JSON)
- `POST /api/favorite/<path>` - Toggle favorite
- `GET /api/download/<path>` - Download log file

**Helper functions:**
- `_tail_file()` - Read last N lines efficiently
- `_tail_large_file()` - Handle large files (read from end)
- `_search_file()` - Search with regex or plain text

### core/config.py (~120 lines)
- Loads config.json with defaults
- Property-based access to settings
- Manages favorites (add/remove/save)

### core/path_resolver.py (~50 lines)
- Walks up N levels to find project root
- Converts absolute paths to relative paths

### core/log_scanner.py (~180 lines)
**Classes:**
- `LogFile` - Represents a log file with metadata (size, modified time)
- `LogScanner` - Discovers log files recursively

**Features:**
- Pattern matching (*.log)
- Directory exclusion
- Size filtering
- Grouping by directory

### static/css/style.css
- Your dark theme colors
- Responsive layout
- Button styles
- Log line color coding
- Scrollbar customization

### static/js/viewer.js (~200 lines)
- Live tail with auto-refresh
- Search with regex support
- Level filtering
- Favorite toggling
- Status messages

## Usage Examples

### Quick Check
```bash
# Start server
python app.py

# Open http://localhost:5000
# See all discovered logs
# Click any log to view
```

### Debugging
```bash
# 1. Open problematic log
# 2. Filter by "ERROR"
# 3. Search for specific error text
# 4. Download filtered results
```

### Monitoring
```bash
# 1. Open active log (e.g., trailboss.log)
# 2. Enable auto-refresh
# 3. Watch live updates
# 4. Favorite for quick access
```

### Comparing
```bash
# 1. Open first log in tab 1
# 2. Open second log in tab 2
# 3. Search same term in both
# 4. Compare side-by-side
```

## API Examples

### Tail last 200 lines
```bash
GET /api/tail/logs/trailboss.log?lines=200

Response:
{
  "lines": ["line1", "line2", ...],
  "path": "logs/trailboss.log"
}
```

### Search for ERROR
```bash
GET /api/search/logs/trailboss.log?q=ERROR&regex=0&case=0

Response:
{
  "matches": [
    {"line_number": 42, "text": "ERROR: Something broke"},
    ...
  ],
  "query": "ERROR",
  "count": 15
}
```

### Toggle favorite
```bash
POST /api/favorite/logs/trailboss.log

Response:
{
  "path": "logs/trailboss.log",
  "is_favorite": true
}
```

## Troubleshooting

### No logs showing
- Check console output showing project root
- Verify `levels_up_to_root` in config.json
- Ensure .log files exist in scanned directories

### Can't connect to server
- Install Flask: `pip install flask`
- Check port 5000 not in use
- Try `python app.py` directly to see errors

### Auto-refresh not working
- Check browser console for errors
- Verify JavaScript loaded (view page source)
- Try manual refresh button

### Search not working
- Check search query is correct
- Try case-insensitive search
- Verify file not too large

## Manual Steps

1. **Install Flask** (if not already installed)
   ```bash
   pip install flask
   ```

2. **Extract zip** to `C:\auto_trading\bots\trailboss\tools\LogViewer\`

3. **Run** `python app.py` or double-click `run.bat`

4. **Open browser** to `http://localhost:5000`

5. **Verify** logs are discovered correctly

6. **Test features:**
   - View a log
   - Search for text
   - Filter by level
   - Toggle favorite
   - Download log

## Integration with Your Workflow

### folder_watcher
- Zip prefix: `LV_` (LogViewer)
- Will auto-deploy to correct location

### Access from anywhere
```bash
# From any terminal in trailboss project
cd tools\LogViewer
python app.py
```

### Bookmark for quick access
- Add `http://localhost:5000` to browser bookmarks
- Always available when server running

### Run in background
```bash
# Start server in background (Windows)
start /B python app.py

# Or use Windows Task Scheduler for auto-start
```

## Next Steps

1. **Deploy** files to `tools/LogViewer/`
2. **Install** Flask if needed
3. **Run** `python app.py`
4. **Verify** logs are discovered
5. **Test** features (tail, search, filter, favorite)
6. **Customize** config.json if needed
7. **Add to workflow** - bookmark, shortcuts, etc.

## Tips

- **Large logs**: Reduce tail lines to 50 or 100 for performance
- **Slow search**: Use more specific queries or regex patterns
- **Many logs**: Use favorites to focus on important ones
- **Keep it running**: Server can stay running in background
- **Multiple instances**: Each project can have its own LogViewer

## Support

All code is self-contained and documented. Check:
1. Console output when running `app.py`
2. Browser console (F12) for JavaScript errors
3. README.md for detailed documentation
4. Comments in source files
