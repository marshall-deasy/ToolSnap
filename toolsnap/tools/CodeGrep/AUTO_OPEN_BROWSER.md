# CodeGrep - Auto-Open Browser

## What Changed

CodeGrep now automatically opens a browser tab when the server starts.

## How It Works

When you run `python app.py`:

1. Flask server starts on `http://localhost:5001`
2. After 1.5 seconds (ensures server is ready)
3. Browser automatically opens to CodeGrep interface
4. No need to manually copy/paste the URL

## Technical Details

**Implementation:**
```python
import webbrowser
from threading import Timer

# In main():
Timer(1.5, lambda: webbrowser.open('http://localhost:5001')).start()
app.run(...)
```

**Delay explained:**
- Flask needs ~1 second to initialize
- 1.5 second delay ensures server is accepting connections
- Browser opens to ready interface (no connection errors)

## Browser Selection

`webbrowser.open()` uses your **default browser** automatically.

To force Chrome specifically (optional):
```python
# Windows
chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'
webbrowser.get(chrome_path).open('http://localhost:5001')

# Or simpler - just set Chrome as default browser
```

Current implementation uses default browser (simpler, more reliable).

## Disabling Auto-Open

If you don't want auto-open, comment out these lines in `app.py`:

```python
# def open_browser():
#     webbrowser.open('http://localhost:5001')
# 
# Timer(1.5, open_browser).start()
```

## Console Output

```
======================================================================
CodeGrep - Starting Flask Server
======================================================================

Script directory:  C:\path\to\CodeGrep
Project root:      C:\path\to\project
Config:            C:\path\to\CodeGrep\config.json

Scanning for code files...
Found 247 code file(s)
  .bat: 5
  .json: 12
  .py: 230

Server starting at: http://localhost:5001
Opening browser...
Press Ctrl+C to stop
======================================================================

 * Running on http://0.0.0.0:5001
 * Debug mode: on
```

Browser tab opens automatically at this point.

## Benefits

✅ **Faster workflow** - No manual URL copying
✅ **Better UX** - Immediate access to interface
✅ **Consistent** - Same experience every launch
✅ **Simple** - Uses Python's built-in webbrowser module

## Compatibility

Works on:
- ✅ Windows (all browsers)
- ✅ macOS (all browsers)
- ✅ Linux (all browsers)

Uses system's default browser handler.
