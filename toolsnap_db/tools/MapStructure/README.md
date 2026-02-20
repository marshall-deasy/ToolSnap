# Map Structure

Portable, self-aware directory structure mapper that auto-detects project root and generates timestamped tree files.

## Features

- **Auto-detects project root** — walks up 2 levels from script location by default
- **Smart defaults** — no args needed, just run it
- **Timestamped output** — saves to project root with `PROJECTNAME_STRUCTURE_20250207_153045.txt`
- **Configurable exclusions** — edit `config.json` to customize what's excluded
- **Context menu integration** — right-click any folder → "Map Structure"
- **Portable** — detects its own location, no hardcoded paths

## Installation

1. **Place the tool** in your project structure (e.g., `trailboss/tools/MapStructure/`)

2. **Run installer** to add context menu:
   ```bash
   python install.py
   ```

3. **Done!** Right-click any folder and select "Map Structure"

## Project Structure

By default, the script assumes it lives 2 levels below project root:

```
trailboss/                    ← Project root (output goes here)
  tools/                      ← 1 level up
    MapStructure/             ← Script location
      map_structure.py        ← Main script
      install.py              ← Registry installer
      config.json             ← Configuration
```

## Usage

### Auto-detect mode (default)
```bash
python map_structure.py
```
Maps the project root (2 levels up) and saves output there.

### Map specific directory
```bash
python map_structure.py C:\some\other\path
```

### Show folder picker
```bash
python map_structure.py --pick
```

### Limit depth
```bash
python map_structure.py --depth 3
```

### Directories only
```bash
python map_structure.py --dirs-only
```

### Double-click
Just double-click `map_structure_launcher.bat` — it figures out the rest.

## Configuration

Edit `config.json` to customize behavior:

```json
{
  "levels_up_to_root": 2,
  "exclude_dirs": [
    "__pycache__",
    ".git",
    "node_modules",
    "venv"
  ],
  "exclude_suffixes": [
    ".egg-info"
  ],
  "structure_file_pattern": "^.+_STRUCTURE(_\\d{8}_\\d{6})?\\.txt$"
}
```

### Configuration options:

- **levels_up_to_root**: How many directory levels to traverse up to find project root
- **exclude_dirs**: Directory names to skip during mapping
- **exclude_suffixes**: File/directory suffixes to exclude
- **structure_file_pattern**: Regex pattern for identifying structure output files (auto-excluded)

## Output Example

```
TRAILBOSS/
├── bots/
│   ├── marshybot/
│   │   ├── config/
│   │   └── main.py
│   └── trailboss/
│       ├── tools/
│       │   └── MapStructure/
│       │       ├── core/
│       │       ├── map_structure.py
│       │       └── config.json
│       └── trailboss.py
├── data/
└── logs/

[ Dirs: 12 | Files: 45 ]
```

Saved to: `C:\auto_trading\bots\trailboss\TRAILBOSS_STRUCTURE_20250207_153045.txt`

## Context Menu Integration

After running `install.py`, you get two context menu options:

1. **Right-click on a folder** → "Map Structure" (maps that folder)
2. **Right-click in empty space** → "Map Structure" (maps current directory)

### Uninstall context menu
```bash
python install.py --uninstall
```

## File Structure

```
MapStructure/
├── core/
│   ├── __init__.py          # Package init
│   ├── config.py            # Configuration management
│   ├── path_resolver.py     # Project root detection
│   └── tree_builder.py      # Tree building logic
├── map_structure.py         # Main entry point
├── install.py               # Registry installer
├── map_structure_launcher.bat  # Double-click wrapper
├── config.json              # User configuration
└── README.md                # This file
```

## Design Principles

- **Single source of truth** — each piece of logic exists in exactly one place
- **Separation of concerns** — config, UI, business logic all separated
- **Zero hardcoded paths** — everything auto-detected
- **Externalized configuration** — customize without editing code
- **Complete working code** — no stubs, no TODOs

## Requirements

- Python 3.9+
- Windows (for context menu integration)
- tkinter (optional, for folder picker GUI)

## License

Use freely. No attribution required.
