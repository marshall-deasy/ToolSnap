"""
dialogs.py - UI dialogs for DropRouterHud.

ZipTreeDialog:   Preview zip contents as tree with ✓/⚠️ indicators.
                Shows project root folder: ProjectName (ROOT)
                Light theme optimized for careful examination of file paths.
                Green accents for branding consistency.
                
UnmatchedFilePopup:  Handle single files with no routing match.
                Dark HUD theme for quick glanceable decision.

Both use PySide6. Different themes for different use cases:
- Tree dialog = careful examination (light, high contrast)
- Quick popups = glanceable decisions (dark HUD theme)
"""

import json
from pathlib import Path
from typing import Callable, List, Optional, Set, Tuple

# PySide6 imports
from PySide6.QtWidgets import (
    QApplication, QDialog, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor


# ============================================================================
# ZIP TREE PREVIEW
# ============================================================================

class ZipTreeDialog(QDialog):
    """
    Modal tree showing zip internal structure with destination preview.
    Shows project root as: ProjectName (ROOT)
    ✓ = known destination, ⚠️ = flagged (unknown path)
    Returns True (extract) or False (skip) via .show_dialog().
    
    Tree is ALWAYS fully expanded - just scroll with mouse wheel to see all files.
    Light, high-contrast theme optimized for examination and readability.
    Green accents maintain branding consistency with HUD.
    """

    def __init__(
        self,
        zip_path: Path,
        contents: List[str],
        wrapper: Optional[str],
        project_name: str,
        project_root: Path,
        dest_resolver: Callable,
    ):
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        super().__init__()
        
        self.zip_path = zip_path
        self.contents = contents
        self.wrapper = wrapper
        self.project_name = project_name
        self.project_root = project_root
        self.dest_resolver = dest_resolver
        self.accepted = False
        
        self._build()

    def _build(self):
        """Build the dialog UI."""
        # Window setup
        self.setWindowTitle(f"📦 {self.zip_path.name} — {self.project_name} DropRouter")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # Calculate height based on content
        height = min(max(400, len(self.contents) * 22 + 200), 900)
        self.setGeometry(50, 30, 750, height)
        
        # Light, high-contrast theme optimized for reading/examination
        self.setStyleSheet("""
            QDialog {
                background-color: #F5F5F5;
            }
            QLabel {
                color: #202020;
                background: transparent;
            }
            QTreeWidget {
                background-color: #FFFFFF;
                color: #202020;
                border: 1px solid #C0C0C0;
                border-radius: 2px;
                font-size: 10pt;
            }
            QTreeWidget::item {
                padding: 4px;
                border-bottom: 1px solid #F0F0F0;
            }
            QTreeWidget::item:hover {
                background-color: #E8F5E9;
            }
            QTreeWidget::item:selected {
                background-color: #C8E6C9;
            }
            QHeaderView::section {
                background-color: #E0E0E0;
                color: #202020;
                padding: 6px;
                border: none;
                border-right: 1px solid #C0C0C0;
                font-weight: bold;
            }
            QPushButton {
                background-color: #FFFFFF;
                color: #00AA00;
                border: 2px solid #00CC66;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E8F5E9;
                border-color: #00AA00;
            }
            QPushButton:pressed {
                background-color: #C8E6C9;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header
        header = QLabel(f"📦 {self.zip_path.name}")
        header.setFont(QFont("Segoe UI", 13, QFont.Bold))
        header.setStyleSheet("color: #00AA00;")  # Green accent for branding
        layout.addWidget(header)
        
        # Summary
        flagged_count = sum(
            1 for e in self.contents
            if self.dest_resolver(e, self.wrapper)[1]
        )
        summary = f"{len(self.contents)} files"
        if flagged_count:
            summary += f"  ({flagged_count} flagged → Downloads)"
        
        summary_label = QLabel(summary)
        summary_label.setFont(QFont("Segoe UI", 10))
        summary_label.setStyleSheet("color: #606060;")
        layout.addWidget(summary_label)
        
        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File", "Destination"])
        self.tree.setColumnWidth(0, 360)
        self.tree.setColumnWidth(1, 350)
        self.tree.setFont(QFont("Consolas", 10))
        self.tree.setSelectionMode(QTreeWidget.NoSelection)
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree)
        
        self._populate()
        
        # Ensure all items are expanded for easy scrolling
        self.tree.expandAll()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        skip_btn = QPushButton("Skip")
        skip_btn.clicked.connect(self._skip)
        skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #606060;
                border: 2px solid #A0A0A0;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
                border-color: #808080;
            }
        """)
        btn_layout.addWidget(skip_btn)
        
        process_btn = QPushButton("✓ Process")
        process_btn.clicked.connect(self._accept)
        btn_layout.addWidget(process_btn)
        
        layout.addLayout(btn_layout)
        
        # Keyboard shortcuts
        process_btn.setShortcut(Qt.Key_Return)
        skip_btn.setShortcut(Qt.Key_Escape)

    def _populate(self):
        """Build tree with project root folder shown."""
        entries = sorted(e.replace("\\", "/") for e in self.contents)
        
        # Create root node for project
        root_item = QTreeWidgetItem([f"📂 {self.project_name} (ROOT)", ""])
        root_item.setFont(0, QFont("Segoe UI", 10, QFont.Bold))
        root_item.setForeground(0, QColor("#00AA00"))  # Darker green for light bg
        root_item.setExpanded(True)
        self.tree.addTopLevelItem(root_item)
        
        def strip(p):
            """Remove wrapper from path if present."""
            if self.wrapper and p.startswith(self.wrapper + "/"):
                return p[len(self.wrapper) + 1:]
            return p
        
        folder_items = {}
        
        for entry in entries:
            display = strip(entry)
            parts = display.split("/")
            filename = parts[-1]
            folder_parts = parts[:-1]
            
            # Build folder hierarchy under root
            parent_item = root_item
            for i, folder in enumerate(folder_parts):
                folder_key = "/".join(folder_parts[: i + 1])
                if folder_key not in folder_items:
                    folder_item = QTreeWidgetItem([f"📁 {folder}", ""])
                    folder_item.setForeground(0, QColor("#505050"))  # Dark gray for folders
                    folder_item.setExpanded(True)
                    parent_item.addChild(folder_item)
                    folder_items[folder_key] = folder_item
                parent_item = folder_items[folder_key]
            
            # Determine destination and flagged status
            dest, flagged = self.dest_resolver(entry, self.wrapper)
            
            if flagged:
                icon = "⚠️"
                dest_display = "Downloads (flagged)"
                color = "#CC6600"  # Dark orange for warnings on light bg
            else:
                icon = "✓"
                if dest == "ROOT":
                    dest_display = f"{self.project_root.name}/"
                else:
                    dest_display = dest
                color = "#008800"  # Dark green for success on light bg
            
            # Insert file with icon
            file_item = QTreeWidgetItem([f"  {icon} {filename}", dest_display])
            file_item.setForeground(0, QColor(color))
            file_item.setForeground(1, QColor("#505050"))  # Dark gray for destinations
            parent_item.addChild(file_item)

    def _accept(self):
        """User clicked Process."""
        self.accepted = True
        self.accept()

    def _skip(self):
        """User clicked Skip."""
        self.accepted = False
        self.reject()

    def show_dialog(self) -> bool:
        """
        Show dialog and return user choice.
        Returns: True if accepted, False if skipped
        """
        self.exec()
        return self.accepted


# ============================================================================
# UNMATCHED FILE POPUP
# ============================================================================

class UnmatchedFilePopup(QDialog):
    """
    Small popup for files with no routing match.
    Options: Ignore Once / Always Ignore
    
    PySide6-based with green theme (#00FF66) and semi-transparent backgrounds.
    """

    def __init__(
        self,
        filepath: Path,
        ignore_list: Set[str],
        save_ignore_fn: Callable,
    ):
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        super().__init__()
        
        self.filepath = Path(filepath)
        self.ignore_list = ignore_list
        self.save_ignore_fn = save_ignore_fn
        
        self._build()
    
    def _build(self):
        """Build the dialog UI."""
        # Window setup
        self.setWindowTitle("Unmatched File")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setFixedSize(420, 140)
        self.move(50, 50)
        
        # Dark background with slight transparency
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(30, 30, 30, 0.98);
            }
            QLabel {
                color: #00FF66;
                background: transparent;
            }
            QPushButton {
                background-color: rgba(0, 255, 102, 0.2);
                color: #00FF66;
                border: 1px solid #00FF66;
                border-radius: 3px;
                padding: 6px 16px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 102, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(0, 255, 102, 0.4);
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header label
        header = QLabel("No route for:")
        header.setFont(QFont("Segoe UI", 11, QFont.Bold))
        layout.addWidget(header)
        
        # Filename label
        filename_label = QLabel(self.filepath.name)
        filename_label.setFont(QFont("Consolas", 11))
        filename_label.setStyleSheet("color: #00FF66; font-weight: bold;")
        layout.addWidget(filename_label)
        
        layout.addSpacing(12)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        ignore_once_btn = QPushButton("Ignore Once")
        ignore_once_btn.clicked.connect(self._once)
        btn_layout.addWidget(ignore_once_btn)
        
        always_ignore_btn = QPushButton("Always Ignore")
        always_ignore_btn.clicked.connect(self._always)
        btn_layout.addWidget(always_ignore_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self._once)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 100, 100, 0.3);
                color: #C0C0C0;
                border: 1px solid #606060;
            }
            QPushButton:hover {
                background-color: rgba(120, 120, 120, 0.4);
            }
        """)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        # Keyboard shortcut
        close_btn.setShortcut(Qt.Key_Escape)

    def _once(self):
        """Close without saving to ignore list."""
        self.reject()

    def _always(self):
        """Add to ignore list and close."""
        self.ignore_list.add(self.filepath.name)
        self.save_ignore_fn(self.ignore_list)
        print(f"  🚫 Always ignoring: {self.filepath.name}")
        self.accept()

    def show_dialog(self):
        """Show dialog (modal)."""
        self.exec()
