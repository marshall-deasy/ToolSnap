"""
FolderSync Configuration
UI constants, colors, and application settings.
"""

# ============================================================================
# COLORS (Dark Theme)
# ============================================================================

COLORS = {
    # Backgrounds
    'bg_dark': '#0d1117',       # Main window background
    'bg_panel': '#161b22',      # Panel/cell background
    'bg_input': '#21262d',      # Input fields
    'bg_hover': '#1c2128',      # Hover state
    'border': '#30363d',        # Borders, dividers
    
    # Text
    'text': '#c9d1d9',          # Primary text
    'text_dim': '#8b949e',      # Secondary text
    
    # Status
    'green': '#3fb950',         # Newest
    'orange': '#f0883e',        # Older
    'red': '#f85149',           # Missing
    'blue': '#58a6ff',          # Same age
    'cyan': '#39c5cf',          # Accent
    
    # Buttons
    'slate_blue': '#6272a4',    # Neutral actions
    'muted_red': '#b05050',     # Delete actions
}


# ============================================================================
# STATUS INDICATORS
# ============================================================================

STATUS = {
    'newest': {'symbol': '✓', 'color': COLORS['green'], 'label': 'newest'},
    'older': {'symbol': '⚠', 'color': COLORS['orange'], 'label': 'older'},
    'missing': {'symbol': '❌', 'color': COLORS['red'], 'label': 'missing'},
    'same': {'symbol': '═', 'color': COLORS['blue'], 'label': 'same'},
}


# ============================================================================
# UI DIMENSIONS
# ============================================================================

# Window
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 800  # Reduced for half-screen support
WINDOW_MIN_HEIGHT = 600

# Grid
GRID_ROW_HEIGHT = 70
GRID_TOOL_COLUMN_WIDTH = 300
GRID_LOCATION_COLUMN_WIDTH = 200

# Fonts
FONT_FAMILY = 'Segoe UI'
FONT_FAMILY_MONO = 'Consolas'
FONT_SIZE_TITLE = 20
FONT_SIZE_NORMAL = 13
FONT_SIZE_SMALL = 11
FONT_SIZE_MONO = 14  # Increased from 12 for better readability in grid


# ============================================================================
# FILE OPERATIONS
# ============================================================================

# Timestamp format for renamed folders
TIMESTAMP_FORMAT = '%Y%m%d_%H%M%S'

# Suffix for old folders
OLD_FOLDER_SUFFIX = '.OLD_{timestamp}'
