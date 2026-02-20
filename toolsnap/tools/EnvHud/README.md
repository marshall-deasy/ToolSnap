# EnvHud - Environment Launcher

Minimal floating HUD showing "ENV ▼". Right-click to launch terminals with different conda environments.

## Quick Start

1. **Double-click START.bat**
   - ENV ▼ appears on screen
   - No terminal window stays open
   - Clean, silent launch

2. **Right-click ENV ▼**
   - Select environment + path
   - New terminal opens ready to work

3. **Done?**
   - Right-click → Quit

## File Structure

```
EnvHud/
├── START.bat           Launch script (double-click this)
├── envhud.py           Main application
├── config.json         Configuration
├── core/
│   ├── __init__.py
│   ├── config.py       Config management
│   └── env_manager.py  Environment operations
└── README.md           This file
```

## Configuration

Edit `config.json` to add your own environment paths.

## How It Works

- START.bat launches pythonw.exe in background
- Batch script exits immediately (no window stays open)
- ENV ▼ floats on screen
- Right-click opens menu with your configured paths
- Selecting a path opens a NEW terminal at that location with environment activated
