"""
hud_overlay.py - Minimal floating HUD for DropRouterHud.

Single-line text display: "DL → ProjectName (count)"
Green text with semi-transparent dark background for readability.
Positioned 5px from top-right, stacked with 5px spacing.
"""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication, QWidget, QLabel, QMenu
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QFont, QCursor, QColor


class DropRouterHUD(QWidget):
    """
    Minimal floating HUD showing: DL → ProjectName (count)
    Right-click for menu (info, quit).
    """
    
    # Signals for updates
    update_count = Signal(int)
    
    # Layout constants
    MARGIN_TOP = 5
    MARGIN_RIGHT = 5
    LINE_SPACING = 5
    
    def __init__(
        self, 
        project_name: str,
        watch_folder: str,
        position_index: int = 0,
        config: Optional[dict] = None,
        version: str = "2.0"
    ):
        super().__init__()
        
        self.project_name = project_name
        self.watch_folder = Path(watch_folder).name
        self.position_index = position_index
        self.file_count = 0
        self.version = version
        
        # Config
        if config is None:
            config = {}
        hud_cfg = config.get("hud", {})
        self.font_size = hud_cfg.get("font_size", 14)
        self.color = QColor(hud_cfg.get("color", "#00FF66"))
        
        self._setup_window()
        self._setup_ui()
        
        # Connect signals
        self.update_count.connect(self._on_count_update)
        
    def _setup_window(self):
        """Configure window as transparent overlay."""
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Calculate position - top-right with stacking
        self.adjustSize()  # Initial size
        
    def _setup_ui(self):
        """Build the single-line text label."""
        # Single label with text
        self.label = QLabel(self._format_text(), self)
        self.label.setFont(QFont("Consolas", self.font_size, QFont.Bold))
        
        # Green text with semi-transparent dark background for readability
        self.label.setStyleSheet(
            f"color: {self.color.name()}; "
            "background-color: rgba(0, 0, 0, 0.2); "
            "padding: 2px 6px; "
            "border-radius: 3px;"
        )
        self.label.adjustSize()
        
        # Position window
        self._reposition()
        
    def _format_text(self) -> str:
        """Format the display text."""
        return f"{self.version} {self.watch_folder} → {self.project_name} ({self.file_count})"
    
    def _reposition(self):
        """Position widget in top-right corner with vertical stacking."""
        self.label.adjustSize()
        label_width = self.label.width()
        label_height = self.label.height()
        
        # Get screen dimensions
        screen = QApplication.primaryScreen().geometry()
        
        # Calculate position
        x = screen.width() - label_width - self.MARGIN_RIGHT
        y = self.MARGIN_TOP + (self.position_index * (label_height + self.LINE_SPACING))
        
        # Set widget geometry to exactly fit the label
        self.setGeometry(x, y, label_width, label_height)
        self.label.move(0, 0)
        
    def mousePressEvent(self, event):
        """Handle right-click for context menu."""
        if event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
        event.accept()
        
    def _show_context_menu(self, pos: QPoint):
        """Show minimal context menu."""
        menu = QMenu(self)
        
        # Info
        action_info = menu.addAction("ℹ️ Info")
        action_info.triggered.connect(self._show_info)
        
        menu.addSeparator()
        
        # Quit
        action_quit = menu.addAction("✖ Quit")
        action_quit.triggered.connect(self._quit)
        
        menu.exec(pos)
        
    def _show_info(self):
        """Show info about this router instance."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            f"{self.project_name} DropRouter",
            f"Project: {self.project_name}\n"
            f"Watching: {self.watch_folder}\n"
            f"Files Processed: {self.file_count}\n"
            f"Position: {self.position_index}"
        )
        
    def _quit(self):
        """Confirm and quit."""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Quit DropRouter",
            f"Stop watching {self.project_name}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QApplication.quit()
            
    def _on_count_update(self, count: int):
        """Handle file count update - refresh text."""
        self.file_count = count
        self.label.setText(self._format_text())
        self._reposition()  # Reposition in case text width changed


def create_hud_app(
    project_name: str,
    watch_folder: str, 
    position_index: int = 0,
    config: Optional[dict] = None,
    version: str = "2.0"
) -> tuple[QApplication, DropRouterHUD]:
    """
    Create QApplication and HUD window.
    Returns: (app, hud_window)
    """
    # Check if QApplication already exists
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    hud = DropRouterHUD(project_name, watch_folder, position_index, config, version)
    hud.show()
    
    return app, hud
