# CodeGrep

Fast code search tool with Flask web interface. Auto-discovers code files from project root and provides instant search with VS Code integration.

## Features

- **Auto-discovery** - Walks up 2 levels to find project root, scans for all `.py` files
- **Fast search** - Plain text or regex search across entire codebase
- **Context display** - Shows lines before/after each match
- **VS Code integration** - Click result → opens VS Code at exact line
- **Dark theme** - Clean interface matching your style
- **Zero config** - Drop it anywhere, it figures out the rest

## Perfect For

**When Claude asks:** *"Can you show me the `calculate_stops` function?"*

**Without CodeGrep:**
1. Try to remember which file
2. Open file in VS Code
3. Scroll to find it
4. Copy and paste

**With CodeGrep:**
1. Search: `"def calculate_stops"`
2. Click result → VS Code opens at line 287
3. Copy and paste

**Saves ~30 seconds per search + mental energy**

## Installation

**Requirements:**
- Python 3.9+
- Flask (`pip install flask`)

**Deploy:**
1. Extract to `C:\auto_trading\bots\trailboss\tools\CodeGrep\`
2. Install Flask: `pip install flask`
3. Done!

## Project Structure

By default, CodeGrep assumes it lives 2 levels below project root:

```
trailboss/                    ← Project root (scans from here)
  bots/
    marshybot/
    trailboss/
  shared/
  tools/
    CodeGrep/                 ← Lives here
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

Opens browser at `http://localhost:5001`

### Search Interface

**Search box:**
- Enter query (plain text or regex)
- Press Enter or click Search

**Options:**
- **Regex** - Treat query as regex pattern
- **Case Sensitive** - Exact case matching
- **Whole Word** - Match complete words only

**Results:**
- Shows file path and line number
- Context lines before/after match
- Matching line highlighted
- Click "Open in VS Code" → jumps to exact line

### Search Examples

**Find function definition:**
```
def calculate_position_size
```

**Find all imports:**
```
import schwab_api
```

**Find TODO comments (regex):**
```
TODO|FIXME
```
*(Enable Regex checkbox)*

**Find config references:**
```
API_KEY
```

**Find error handling:**
```
except.*Exception
```
*(Enable Regex checkbox)*

**Find all class definitions:**
```
^class \w+
```
*(Enable Regex checkbox)*

## VS Code Integration

**How it works:**
- Clicking "Open in VS Code" uses `vscode://file/` URL scheme
- Opens file at exact line number
- Works if VS Code is installed and set as default handler

**Manual alternative:**
- Copy file path and line number from result
- Open in VS Code manually: `Ctrl+P` → paste path → `:line`

## Configuration

Edit `config.json` to customize:

```json
{
  "levels_up_to_root": 2,           // Walk up 2 levels to find root
  "file_patterns": ["*.py"],         // File patterns to search
  "exclude_dirs": [...],             // Skip these directories
  "exclude_files": ["*.pyc"],        // Skip these files
  "context_lines": 2,                // Lines before/after match
  "max_results": 500,                // Maximum results to return
  "editor_command": "code"           // Editor command (VS Code)
}
```

### Configuration Options

**levels_up_to_root**
- Number of directory levels to traverse up
- Default: 2
- Adjust if deployed at different depth

**file_patterns**
- File patterns to search
- Default: `["*.py"]`
- Can add: `["*.py", "*.js", "*.txt"]`

**exclude_dirs**
- Directories to skip during scan
- Default: `__pycache__`, `.git`, `venv`, etc.

**exclude_files**
- File patterns to exclude
- Default: `["*.pyc", "*.pyo", "*.pyd"]`

**context_lines**
- Lines to show before/after match
- Default: 2
- More context = bigger results

**max_results**
- Maximum search results to return
- Default: 500
- Prevents huge result sets

**editor_command**
- Command to open editor
- Default: `"code"` (VS Code)
- Could be `"notepad++"`, `"sublime"`, etc.

## File Structure

```
CodeGrep/
├── core/
│   ├── __init__.py          # Package init
│   ├── config.py            # Configuration management (~110 lines)
│   ├── path_resolver.py     # Project root detection (~50 lines)
│   └── code_scanner.py      # File discovery and search (~200 lines)
├── templates/
│   ├── base.html            # Layout template
│   └── index.html           # Search interface
├── static/
│   ├── css/
│   │   └── style.css        # Dark theme styling
│   └── js/
│       └── search.js        # Client-side functionality
├── app.py                   # Flask application (~160 lines)
├── run.bat                  # Launcher script
├── config.json              # Configuration
└── README.md                # This file
```

## API Endpoints

### POST /api/search
Search code files

**Request body:**
```json
{
  "query": "def calculate",
  "regex": false,
  "case_sensitive": false,
  "whole_word": false
}
```

**Response:**
```json
{
  "results": [
    {
      "file_path": "C:\\...\\trailboss.py",
      "relative_path": "bots\\trailboss\\trailboss.py",
      "line_number": 287,
      "line_text": "    def calculate_stops(self, entry_price, side):",
      "context_before": ["", "    # Stop loss calculation"],
      "context_after": ["        atr = self.get_atr()", ""]
    }
  ],
  "query": "def calculate",
  "count": 15,
  "truncated": false
}
```

### GET /api/files
Get list of all discovered code files

**Response:**
```json
{
  "files": ["bots/trailboss/trailboss.py", ...],
  "total": 42,
  "stats": {".py": 42}
}
```

### GET /api/refresh
Refresh file cache (rescan project)

**Response:**
```json
{
  "total_files": 42,
  "message": "File cache refreshed"
}
```

## Design Principles

Following Marshall's engineering rules:

- **Single source of truth** - Each piece of logic exists in exactly one place
- **Separation of concerns** - Core logic, Flask routes, templates, static files all separated
- **Config externalized** - All settings in `config.json`, zero hardcoded values
- **Complete working code** - No stubs, all imports resolve
- **Modular** - Each file <400 lines, clear responsibility

## Use Cases

### Debugging with Claude
```
Claude: "Show me your calculate_position_size function"
You: [search "def calculate_position_size"]
     → Click result → VS Code opens
     → Copy function
     → Paste to Claude
```

### Finding imports
```
You: Where am I using schwab_api?
     [search "import schwab_api"]
     → See all 5 files that import it
```

### Finding TODOs
```
You: What tasks are pending?
     [search "TODO|FIXME" with Regex]
     → See all TODO comments across project
```

### Finding config usage
```
You: Where is API_KEY used?
     [search "API_KEY"]
     → See all references
```

### Understanding code flow
```
You: How does order placement work?
     [search "place_order"]
     → Find definition
     → Find all calls
     → Trace through code
```

## Troubleshooting

**No files found:**
- Check `config.json` → `levels_up_to_root` is correct
- Verify `.py` files exist in scanned directories
- Check console output showing project root

**Search not working:**
- Verify query syntax (especially for regex)
- Try plain text search first
- Check regex syntax if using regex mode

**VS Code not opening:**
- Ensure VS Code is installed
- Verify it's the default handler for `vscode://` URLs
- Manually copy file:line and open in VS Code

**Port 5001 already in use:**
- Stop other Flask apps
- Or edit `app.py` and change port: `app.run(port=5002)`

**Slow search:**
- Reduce file count (add more excludes)
- Use more specific queries
- Consider file pattern restrictions

## Performance

**Typical performance:**
- Small project (<50 files): <100ms
- Medium project (50-200 files): <500ms
- Large project (200+ files): <2s

**Optimization tips:**
- File cache speeds up repeated searches
- Exclude unnecessary directories
- Use specific queries (avoid `.*` style searches)

## Tips & Tricks

**Keyboard shortcuts:**
- Enter in search box → Execute search
- Focus search box on page load

**Search patterns:**
- Function defs: `def function_name`
- Class defs: `class ClassName`
- Imports: `import module_name`
- Comments: `# keyword` or `TODO|FIXME`
- Variables: `variable_name =`

**Regex examples:**
- Start of line: `^pattern`
- End of line: `pattern$`
- Word boundary: `\bword\b`
- Any character: `.`
- One or more: `+`
- Zero or more: `*`
- Alternation: `pattern1|pattern2`

**Common workflows:**

**Quick reference check:**
1. See unfamiliar function call
2. Search for definition
3. Read implementation
4. Return to original work

**Refactoring:**
1. Search for all uses of function
2. Review each usage
3. Update as needed
4. Verify with another search

**Code review:**
1. Search for specific patterns
2. Review implementations
3. Check consistency across files

## Integration with Other Tools

**Works great with:**
- **MapStructure** - See project layout, then search code
- **LogViewer** - Debug runtime, search for error patterns in code
- **VS Code** - Search finds it, VS Code edits it

**Workflow example:**
1. **LogViewer** shows error: `KeyError: 'position_size'`
2. **CodeGrep** finds where `position_size` is used
3. **VS Code** opens to fix the bug
4. **MapStructure** confirms file location in project

## Future Enhancements

Potential features for future versions:

- Search history (recent queries)
- Saved searches (common patterns)
- File type filtering (search only in specific dirs)
- Export results to file
- Multi-project support
- Syntax highlighting in results
- Replace functionality (find & replace)
- Git integration (search only tracked files)

## License

Use freely. No attribution required.

## Support

Check `app.py` console output for debugging info.

File issues or questions in project documentation.
