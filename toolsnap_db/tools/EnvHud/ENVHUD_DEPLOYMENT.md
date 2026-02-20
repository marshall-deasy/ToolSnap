# EnvHud - Deployment Summary

## What You're Getting

**Minimal conda environment HUD** - always-on-top display showing current environment. Stacks with DropRouterHud in top-right corner. Right-click to switch environments.

## Visual Layout

```
Top-right corner:

┌──────────────────────────────┐
│ DropRouterHud                │
│ Watching: Downloads          │
│ Last: CG_latest.zip → tools  │
└──────────────────────────────┘
┌──────────────────────────────┐
│ ENV: trading 🔴              │  ← EnvHud (new!)
└──────────────────────────────┘
```

**Two separate apps, positioned together.**

## Installation

### 1. Install PySide6
```bash
pip install PySide6
```

### 2. Deploy Files
Extract `EH_latest.zip` to: `C:\auto_trading\bots\trailboss\tools\EnvHud\`

Your structure:
```
trailboss/
  tools/
    EnvHud/
      envhud.py
      START.bat
      core/
      ...
```

### 3. Run It
```bash
# Option 1: Double-click
START.bat

# Option 2: Background (no console)
pythonw envhud.py
```

**HUD appears in top-right corner, below DropRouterHud.**

## What It Does

### Display Current Environment

**Shows:**
- 🔴 `ENV: trading` - Red (active dev work)
- ⚫ `ENV: base` - Gray (system default)
- 🟢 `ENV: chatbots` - Green (AI work)

**Updates:**
- Checks every 5 seconds
- Shows current `CONDA_DEFAULT_ENV`
- Minimal, clean display

### Switch Environments

**Right-click the HUD:**
```
EnvHud
├─ ✓ trading (current)
├─ ⚫ Switch to: base
├─ 🟢 Switch to: chatbots
├─────────────────
├─ 🔄 Refresh
├─────────────────
└─ ✕ Exit
```

**Click an environment:**
- Opens new terminal
- That terminal has selected env activated
- Command: `conda activate <env>`

**Important:** Switching opens a **new** terminal with the environment. Your existing terminals stay in their current environment. Use the new terminal for work.

## Configuration

Edit `config.json`:

```json
{
  "position": {
    "x_offset": -350,
    "y": 170,          // Below DropRouterHud
    "width": 330,
    "height": 50
  },
  "colors": {
    "trading": "#f85149",
    "base": "#8b949e",
    "chatbots": "#3fb950"
  },
  "refresh_interval_ms": 5000,
  "window_opacity": 0.95
}
```

**Adjust `y` value** to change vertical position (stack distance from DropRouterHud).

## Use Cases

### Morning Startup

**Before:**
```bash
conda env list                # Which env am I in?
conda activate trading        # Switch manually
# Forget which terminal has what...
```

**With EnvHud:**
1. Glance at top-right
2. See: `ENV: base ⚫`
3. Right-click → Switch to: trading
4. New terminal opens ready to go
5. Visual confirmation at all times

### Context Switching

**Workflow:**
```
Working on trading bots (trading env)
  ↓
Need to test chatbot (chatbots env)
  ↓
Right-click EnvHud → Switch to: chatbots
  ↓
New terminal opens with chatbots active
  ↓
Do chatbot work
  ↓
Close that terminal when done
  ↓
Back to trading work in original terminal
```

## File Structure

```
EnvHud/
├── core/
│   ├── __init__.py
│   ├── config.py         # Config management (~100 lines)
│   └── env_manager.py    # Conda operations (~120 lines)
├── envhud.py             # Main PySide6 app (~200 lines)
├── START.bat             # Launcher
├── config.json           # Configuration
└── README.md             # Full docs
```

## Engineering Rules Compliance

✅ **Single source of truth** - Each piece of logic in one place
✅ **No copy-paste** - Shared logic in core modules  
✅ **Complete working code** - No stubs, all imports resolve
✅ **Modular** - Each file <400 lines, clear responsibility
✅ **GUI/logic separated** - PySide6 UI, business logic in core
✅ **Config externalized** - All settings in config.json

## How It Works

### Environment Detection

**Checks:**
1. `CONDA_DEFAULT_ENV` environment variable
2. Falls back to `conda info --envs` output
3. Looks for asterisk indicating active env
4. Defaults to 'base' if can't detect

**Polling:**
- Checks every 5 seconds (configurable)
- Only updates display if environment changed
- Minimal CPU usage

### Environment Switching

**Process:**
1. User right-clicks HUD
2. Menu populated from `conda env list`
3. User selects environment
4. EnvHud runs: `start cmd /k "conda activate <env>"`
5. New CMD window opens with environment activated
6. User works in that new terminal

**Note:** The HUD itself stays in its original environment. Only the new terminal has the selected environment. This is by design - switching is about opening new terminals, not changing existing ones.

### Positioning

**Auto-positions:**
- Right side of screen
- 170 pixels from top (stacks below DropRouterHud)
- Same width as DropRouterHud
- Always-on-top

## Tips

**Launch from desired env:**
```bash
conda activate trading
cd C:\auto_trading\bots\trailboss\tools\EnvHud
pythonw envhud.py
```
HUD will show 'trading' as current.

**Minimize distraction:**
- Set `window_opacity` to 0.8 or lower
- Makes it more transparent
- Still readable but less intrusive

**Custom env colors:**
```json
{
  "colors": {
    "trading": "#f85149",      // Red
    "base": "#8b949e",         // Gray
    "chatbots": "#3fb950",     // Green
    "myenv": "#f0c33e"         // Yellow (custom)
  }
}
```

## Integration with Your Tools

**Complete dev suite:**

1. **DropRouterHud** (`tools/DropRouterHud/`)
   - Watches downloads for zip files
   - Auto-deploys to correct locations
   - Shows deployment status

2. **EnvHud** (`tools/EnvHud/`)
   - Shows current conda environment
   - Quick switching via right-click
   - Visual confirmation

3. **MapStructure** (`tools/MapStructure/`)
   - Generate project structure maps
   - Context menu integration

4. **LogViewer** (`localhost:5000`)
   - View and search log files
   - Live tail, filtering

5. **CodeGrep** (`localhost:5001`)
   - Search code across project
   - VS Code integration

6. **DependencyAnalyzer** (`localhost:5002`)
   - Find orphaned files
   - Clean up projects

**All tools work together:**
- EnvHud shows which env you're in
- DropRouterHud deploys new tools
- Other tools run in whichever env is active
- Visual stack in top-right corner

## Troubleshooting

**HUD doesn't appear:**
- Install PySide6: `pip install PySide6`
- Try: `python envhud.py` (see errors)
- Check Python in PATH

**Shows wrong environment:**
- HUD shows env of terminal it was launched from
- After switching, use the NEW terminal that opens
- Or restart HUD from desired env

**Right-click menu empty:**
- Check conda in PATH: `conda env list`
- If fails, add conda to PATH
- Restart terminal/HUD

**Position overlaps DropRouterHud:**
- Edit `y` in config.json
- Increase value (moves down)
- Restart HUD

## Next Steps

1. **Deploy** to `tools/EnvHud/`
2. **Install** PySide6 if needed
3. **Run** `START.bat`
4. **Test** right-click switching
5. **Adjust** position if needed (edit config.json)
6. **Enjoy** visual environment awareness

## Folder Watcher

- Zip prefix: `EH_` (EnvHud)
- Auto-deploys via DropRouterHud
- Extract and run

## Value Proposition

**Before:**
- Forget which terminal has which environment
- `conda env list` to check
- Switch manually with `conda activate`
- No visual confirmation

**With EnvHud:**
- Glance at top-right → know immediately
- Right-click → new terminal with selected env
- Visual confirmation at all times
- Minimal, clean, always visible

**EnvHud = Environment awareness without thinking about it.**

Deploy it, stack it with DropRouterHud, never wonder again.
