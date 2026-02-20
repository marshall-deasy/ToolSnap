# DependencyAnalyzer

Automatically analyze Python projects to find active vs. orphaned files based on import dependencies. Clean up messy bot folders systematically.

## The Problem It Solves

**You have:** A bot folder littered with duplicates, old scripts, temp files, and orphaned code.

```
marshybot2/
├── strategy_brain (1).py        ← Duplicate
├── strategy_brain (2).py        ← Duplicate  
├── main_window_FIXED.py         ← Old version
├── current.json                 ← Should be in config/
├── init_core.py                 ← What is this?
├── RUN_BOT.bat                  ← Should be in scripts/
├── STRUCTURE_2026.txt           ← Should be in output/
└── ... 100+ other files
```

**You need:** To know what's actually used vs. what can be archived.

**DependencyAnalyzer:**
1. Finds your entry point (e.g., `marshybot2.bat` → `main.py`)
2. Traces all imports recursively
3. Categorizes everything
4. Web interface to review and execute cleanup
5. Never deletes - always archives safely

## Usage

```bash
python app.py
```

Opens browser at `http://localhost:5002`

Select folder → Review results → Execute cleanup

See full documentation in tool for details.
