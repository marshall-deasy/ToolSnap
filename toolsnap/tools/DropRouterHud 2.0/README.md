# DropRouterHud v2.0 Installation

## Quick Start

**Method 1: Automatic (Recommended)**
1. Drop `TB_droprouterhud_v2.zip` in your Downloads folder
2. TrailBoss router will detect it → show tree dialog
3. Accept → files extract to correct location automatically
4. Restart the router

**Method 2: Manual**
1. Navigate to your project root: `C:\auto_trading\bots\trailboss\`
2. Extract `TB_droprouterhud_v2.zip` here
3. Files will go to `tools\DropRouterHud\` automatically

## Zip Structure

This zip contains full paths from project root:

```
tools/
└── DropRouterHud/
    ├── routing.py          (NEW)
    ├── zip_handler.py      (NEW)
    ├── droprouterhud.py    (UPDATED)
    ├── dialogs.py          (UPDATED)
    ├── hud_overlay.py      (UPDATED)
    └── CHANGELOG_V2.md     (Documentation)
```

When extracted at `C:\auto_trading\bots\trailboss\`, files go directly to the correct location.

## What's New in v2.0

- **Modular architecture** - Clean separation of routing, zip handling, and orchestration
- **Pure PySide6** - No more tkinter dependencies
- **ALL zips show tree** - No auto-extraction, full control
- **Tree fully expanded** - Just scroll, no clicking folders
- **Version in HUD** - Shows "2.0 DL → TrailBoss (0)"
- **Bug fixes** - Re-processing works, no more crashes

## After Installation

Start the router:
```bash
cd C:\auto_trading\bots\trailboss\tools\DropRouterHud
python droprouterhud.py
```

Look for:
- HUD displays: `2.0 DL → TrailBoss (0)`
- Console shows version and status

## Files You're Updating

**New files** (never existed before):
- `routing.py` - Pattern matching logic
- `zip_handler.py` - Zip operations

**Updated files** (replacing old versions):
- `droprouterhud.py` - Main script (refactored)
- `dialogs.py` - Tree dialog improvements
- `hud_overlay.py` - Version display

**Unchanged files** (keep your existing):
- `config.json` - Your routing rules
- `instance_manager.py`
- `requirements.txt`
- `droprouter_ignore.json` (if exists)

## Documentation

Read `CHANGELOG_V2.md` for:
- Complete list of changes
- Troubleshooting guide
- Routing configuration help
- Testing checklist

## Need Help?

**Routing not working?**
→ Check patterns in `config.json`
→ See CHANGELOG_V2.md routing section

**Zip extraction wrong?**
→ Check `known_root_folders` in `config.json`
→ Verify zip internal structure matches project

**HUD not showing version?**
→ Verify all files extracted correctly
→ Restart router completely
