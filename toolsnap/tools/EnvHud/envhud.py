"""
EnvHud - Environment launcher HUD.

Single-line text display: "ENV ▼"
No background, no border - just floating text.
Right-click to launch terminals with different conda environments.
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication, QWidget, QLabel, QMenu, QMessageBox
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QFont, QCursor, QColor

from core import Config, EnvManager


class EnvHud(QWidget):
    """
    Environment launcher HUD: ENV ▼
    Right-click for menu to launch terminals with conda environments.
    """
    
    # Layout constants
    MARGIN_TOP = 5
    MARGIN_RIGHT = 300  # Last character 300px from right edge
    
    def __init__(
        self,
        config: Optional[dict] = None
    ):
        super().__init__()
        
        self._switching = False
        
        # Config
        if config is None:
            config = {}
        hud_cfg = config.get("hud", {})
        self.font_size = 14  # Fixed at 14
        self.color = QColor("#f85149")  # Always red
        
        # Environment manager
        self.env_manager = EnvManager()
        
        self._setup_window()
        self._setup_ui()
        
    def _setup_window(self):
        """Configure window as transparent overlay."""
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Calculate position
        self.adjustSize()
        
    def _setup_ui(self):
        """Build the single-line text label."""
        # Single label with text
        self.label = QLabel(self._format_text(), self)
        self.label.setFont(QFont("Consolas", self.font_size, QFont.Bold))
        
        # Brighter red with semi-transparent dark background for readability
        self.label.setStyleSheet(
            "color: #FF4444; "
            "background-color: rgba(0, 0, 0, 0.2); "
            "padding: 2px 6px; "
            "border-radius: 3px;"
        )
        self.label.adjustSize()
        
        # Position window
        self._reposition()
        
    def _format_text(self) -> str:
        """Format the display text."""
        return "ENV ▼"
    
    def _reposition(self):
        """Position widget: 5px from top, last character 300px from right edge."""
        self.label.adjustSize()
        label_width = self.label.width()
        label_height = self.label.height()
        
        # Get screen dimensions
        screen = QApplication.primaryScreen().geometry()
        
        # Calculate position: 5px from top, 300px from right
        x = screen.width() - self.MARGIN_RIGHT - label_width
        y = self.MARGIN_TOP
        
        # Set widget geometry to exactly fit the label
        self.setGeometry(x, y, label_width, label_height)
        self.label.move(0, 0)
    
    def mousePressEvent(self, event):
        """Handle right-click for context menu."""
        if event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
        event.accept()
        
    def _show_context_menu(self, pos: QPoint):
        """Show nested menu with environments and paths."""
        menu = QMenu(self)
        
        # Load environment paths from config
        import json
        import os
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        env_paths = {}
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                env_paths = config_data.get("environments", {})
        except Exception:
            pass
        
        # Build nested menu
        if env_paths:
            # Trading submenu
            if "trading" in env_paths and env_paths["trading"].get("paths"):
                trading_menu = menu.addMenu("Trading")
                for name, path in env_paths["trading"]["paths"].items():
                    action = trading_menu.addAction(f"→ {name}")
                    action.triggered.connect(lambda checked=False, e="trading", p=path: self._launch_at_path(e, p))
            
            # Chatbots submenu
            if "chatbots" in env_paths and env_paths["chatbots"].get("paths"):
                chatbots_menu = menu.addMenu("Chatbots")
                for name, path in env_paths["chatbots"]["paths"].items():
                    action = chatbots_menu.addAction(f"→ {name}")
                    action.triggered.connect(lambda checked=False, e="chatbots", p=path: self._launch_at_path(e, p))
            
            # Base submenu
            if "base" in env_paths and env_paths["base"].get("paths"):
                base_menu = menu.addMenu("Base")
                for name, path in env_paths["base"]["paths"].items():
                    action = base_menu.addAction(f"→ {name}")
                    action.triggered.connect(lambda checked=False, e="base", p=path: self._launch_at_path(e, p))
        else:
            # Fallback to simple environment list if no paths configured
            envs = self.env_manager.list_environments()
            for env in envs:
                action = menu.addAction(f"Launch: {env}")
                action.triggered.connect(lambda checked=False, e=env: self._switch_env(e))
        
        menu.addSeparator()
        
        # Kill all Python processes
        kill_action = menu.addAction("🔴 Kill All Python")
        kill_action.triggered.connect(self._kill_all_python)
        
        menu.addSeparator()
        
        # Quit
        quit_action = menu.addAction("✕ Quit")
        quit_action.triggered.connect(self._quit)
        
        menu.exec(pos)
    
    def _launch_at_path(self, env_name: str, path: str):
        """Launch terminal at specific path with environment."""
        # Prevent duplicate calls
        if self._switching:
            return
        
        self._switching = True
        
        try:
            # Build the command for CMD to run
            cmd_commands = f'cd /d {path} && conda activate {env_name}'
            
            # Use PowerShell to start CMD (visible, ready to use)
            ps_cmd = f'Start-Process cmd -ArgumentList "/k","{cmd_commands}"'
            
            subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            print(f"Launched: {env_name} @ {path}")
        except Exception as e:
            print(f"Error launching terminal: {e}")
        finally:
            # Reset flag after delay
            QTimer.singleShot(2000, lambda: setattr(self, '_switching', False))
    
    def _kill_all_python(self):
        """Kill all Python processes."""
        try:
            # Kill all python.exe processes
            subprocess.run(
                ["taskkill", "/F", "/IM", "python.exe"],
                capture_output=True
            )
            # Kill all pythonw.exe processes
            subprocess.run(
                ["taskkill", "/F", "/IM", "pythonw.exe"],
                capture_output=True
            )
            print("Killed all Python processes")
        except Exception as e:
            print(f"Error killing Python processes: {e}")
    
    def _switch_env(self, env_name: str):
        """Switch to a different environment."""
        # Prevent duplicate calls
        if self._switching:
            return
        
        self._switching = True
        
        try:
            success = self.env_manager.switch_environment(env_name)
            if success:
                print(f"Opened new terminal with: {env_name}")
            else:
                print(f"Failed to switch to: {env_name}")
        finally:
            # Reset flag after delay
            QTimer.singleShot(2000, lambda: setattr(self, '_switching', False))
    
    def _quit(self):
        """Quit without confirmation."""
        QApplication.quit()


def main():
    """Main entry point."""
    # Self-awareness - where am I?
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    
    # Load configuration
    import json
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except Exception:
            pass
    
    # Create application
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create and show HUD
    hud = EnvHud(config=config)
    hud.show()
    
    print("=" * 60)
    print("EnvHud - Environment Launcher")
    print("=" * 60)
    print("Display: ENV ▼")
    print("Right-click to launch terminal with conda environment")
    print("=" * 60)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
