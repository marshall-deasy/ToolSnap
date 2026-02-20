"""
FolderSync GUI
Qt-based user interface for folder comparison and synchronization.
"""

import sys
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QMenu, QListWidget, QGroupBox,
    QSizePolicy, QAbstractItemView, QApplication, QDialog, QLineEdit
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QBrush, QCursor, QScreen

from config import (
    COLORS, STATUS, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH,
    WINDOW_MIN_HEIGHT, GRID_ROW_HEIGHT, GRID_TOOL_COLUMN_WIDTH,
    GRID_LOCATION_COLUMN_WIDTH, FONT_FAMILY, FONT_FAMILY_MONO,
    FONT_SIZE_TITLE, FONT_SIZE_NORMAL, FONT_SIZE_SMALL, FONT_SIZE_MONO
)
from models import ScanResult, ToolFolder
from scanner import scan_multiple_locations, validate_folder_path, find_old_folders
from sync_engine import SyncEngine
from dialogs import FolderSearchDialog


class FolderListWidget(QListWidget):
    """Custom list widget with drag & drop support for folders."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = None  # Will be set by parent
    
    def dragEnterEvent(self, event):
        """Accept drag events with URLs (file paths)."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Accept drag move events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle dropped folder paths."""
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        
        # Get dropped paths
        urls = event.mimeData().urls()
        for url in urls:
            path = Path(url.toLocalFile())
            
            # Only accept directories
            if path.is_dir() and self.main_window:
                self.main_window._add_folder_path(path)
        
        event.acceptProposedAction()


class FolderSyncWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FolderSync - Folder Comparison Tool")
        
        # State
        self.folder_paths: list[Path] = []
        self.scan_result: Optional[ScanResult] = None
        self.show_conflicts_only = False
        self.last_folder_path: Optional[Path] = None  # Track last selected folder
        
        # Setup UI
        self._setup_ui()
        self._apply_styles()
        
        # Window size and position
        self._position_window()
    
    def _position_window(self):
        """Position window at top-left, half screen width."""
        # Get screen geometry
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        # Calculate half-screen width
        half_width = screen_geometry.width() // 2
        full_height = screen_geometry.height()
        
        # Position at top-left
        self.setGeometry(
            screen_geometry.left(),
            screen_geometry.top(),
            half_width,
            full_height
        )
        
        # Set minimum size
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
    
    def _get_column_label(self, path: Path) -> str:
        """
        Get a readable column label from a path.
        Returns the two parent directory names above the selected folder.
        
        Example:
            C:\\auto_trading\\bots\\marshybot2\\tools -> bots/marshybot2
        """
        try:
            # Get path parts
            parts = path.parts
            
            # Need at least 2 parent directories
            if len(parts) < 2:
                return path.name
            
            # Get the two directories above the selected folder
            parent1 = parts[-2]  # e.g., "marshybot2"
            parent2 = parts[-3]  # e.g., "bots"
            
            return f"{parent2}/{parent1}"
        except (IndexError, AttributeError):
            # Fallback to folder name
            return path.name
    
    def _setup_ui(self):
        """Build the user interface."""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)
        
        # Header
        main_layout.addLayout(self._create_header())
        
        # Folder selection
        folder_group = self._create_folder_selection()
        folder_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        main_layout.addWidget(folder_group)
        
        # Comparison grid
        grid_group = self._create_comparison_grid()
        grid_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        main_layout.addWidget(grid_group)
        
        # Status bar
        main_layout.addLayout(self._create_status_bar())
    
    def _create_header(self) -> QHBoxLayout:
        """Create header with title."""
        header = QHBoxLayout()
        
        title = QLabel("FolderSync")
        title.setStyleSheet(f"""
            font-size: {FONT_SIZE_TITLE}px;
            font-weight: bold;
            color: {COLORS['cyan']};
            font-family: '{FONT_FAMILY}';
        """)
        header.addWidget(title)
        
        header.addStretch()
        
        return header
    
    def _create_folder_selection(self) -> QGroupBox:
        """Create folder selection section."""
        group = QGroupBox("FOLDERS TO COMPARE")
        group.setMinimumHeight(180)
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 12, 8, 11)
        layout.setSpacing(8)
        
        # Folder list
        self.folder_list = FolderListWidget()
        self.folder_list.main_window = self  # Connect to parent
        self.folder_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.folder_list.setAcceptDrops(True)
        self.folder_list.setDragDropMode(QAbstractItemView.DropOnly)
        layout.addWidget(self.folder_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self.add_folder_btn = QPushButton("+ Add Folder")
        self.add_folder_btn.clicked.connect(self._on_add_folder)
        btn_layout.addWidget(self.add_folder_btn)
        
        self.find_tools_btn = QPushButton("🔍 Find 'tools'")
        self.find_tools_btn.clicked.connect(self._on_find_tools)
        btn_layout.addWidget(self.find_tools_btn)
        
        self.find_other_btn = QPushButton("🔍 Find Other...")
        self.find_other_btn.clicked.connect(self._on_find_custom)
        btn_layout.addWidget(self.find_other_btn)
        
        self.remove_folder_btn = QPushButton("Remove Selected")
        self.remove_folder_btn.clicked.connect(self._on_remove_folder)
        self.remove_folder_btn.setEnabled(False)
        btn_layout.addWidget(self.remove_folder_btn)
        
        self.clear_folders_btn = QPushButton("Clear All")
        self.clear_folders_btn.clicked.connect(self._on_clear_folders)
        self.clear_folders_btn.setEnabled(False)
        btn_layout.addWidget(self.clear_folders_btn)
        
        self.cleanup_old_btn = QPushButton("Clean Up .OLD Folders")
        self.cleanup_old_btn.clicked.connect(self._on_cleanup_old_folders)
        self.cleanup_old_btn.setEnabled(False)
        btn_layout.addWidget(self.cleanup_old_btn)
        
        btn_layout.addStretch()
        
        self.compare_btn = QPushButton("COMPARE")
        self.compare_btn.clicked.connect(self._on_compare)
        self.compare_btn.setEnabled(False)
        btn_layout.addWidget(self.compare_btn)
        
        layout.addLayout(btn_layout)
        
        # Connect list selection
        self.folder_list.itemSelectionChanged.connect(self._on_folder_selection_changed)
        
        return group
    
    def _create_comparison_grid(self) -> QGroupBox:
        """Create comparison grid section."""
        group = QGroupBox("COMPARISON")
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 12, 8, 11)
        layout.setSpacing(8)
        
        # Controls
        controls = QHBoxLayout()
        
        self.conflicts_checkbox = QPushButton("☐ Show Only Conflicts")
        self.conflicts_checkbox.setCheckable(True)
        self.conflicts_checkbox.clicked.connect(self._on_toggle_conflicts_filter)
        controls.addWidget(self.conflicts_checkbox)
        
        controls.addStretch()
        
        self.conflict_label = QLabel("No comparison data")
        controls.addWidget(self.conflict_label)
        
        layout.addLayout(controls)
        
        # Grid table
        self.grid_table = QTableWidget()
        self.grid_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid_table.customContextMenuRequested.connect(self._on_context_menu)
        self.grid_table.verticalHeader().setVisible(False)
        self.grid_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.grid_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.grid_table)
        
        return group
    
    def _create_status_bar(self) -> QHBoxLayout:
        """Create status bar."""
        status = QHBoxLayout()
        
        self.status_label = QLabel("Ready")
        status.addWidget(self.status_label)
        
        status.addStretch()
        
        return status
    
    def _apply_styles(self):
        """Apply stylesheet to the window."""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text']};
            }}
            QGroupBox {{
                background-color: {COLORS['bg_panel']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
                font-family: '{FONT_FAMILY}';
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_dim']};
                font-size: {FONT_SIZE_SMALL}px;
                font-weight: bold;
            }}
            QListWidget {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 3px;
                padding: 4px;
                color: {COLORS['text']};
                font-size: {FONT_SIZE_NORMAL}px;
                font-family: '{FONT_FAMILY_MONO}';
            }}
            QListWidget::item {{
                padding: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['blue']};
                color: white;
            }}
            QPushButton {{
                background-color: {COLORS['slate_blue']};
                color: white;
                font-weight: bold;
                font-size: {FONT_SIZE_NORMAL}px;
                padding: 6px 14px;
                border: none;
                border-radius: 3px;
                font-family: '{FONT_FAMILY}';
            }}
            QPushButton:hover {{
                background-color: #50608a;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_dim']};
            }}
            QPushButton#compare_btn {{
                background-color: {COLORS['green']};
                color: #1a1a1a;
                font-size: 15px;
                padding: 8px 20px;
            }}
            QPushButton#compare_btn:hover {{
                background-color: #32944a;
            }}
            QPushButton#cleanup_btn {{
                background-color: {COLORS['orange']};
                color: #1a1a1a;
            }}
            QPushButton#cleanup_btn:hover {{
                background-color: #c06f32;
            }}
            QHeaderView {{
                background-color: {COLORS['bg_panel']};
            }}
            QTableWidget {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                gridline-color: {COLORS['border']};
                color: {COLORS['text']};
                font-size: {FONT_SIZE_NORMAL}px;
            }}
            QTableWidget::item {{
                padding: 4px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_dim']};
                padding: 6px;
                border: 1px solid {COLORS['border']};
                font-weight: bold;
                font-size: 16px;
                font-family: '{FONT_FAMILY}';
            }}
            QLabel {{
                color: {COLORS['text']};
                font-size: {FONT_SIZE_NORMAL}px;
                font-family: '{FONT_FAMILY}';
            }}
        """)
        
        # Set object names for specific styling
        self.compare_btn.setObjectName("compare_btn")
        self.cleanup_old_btn.setObjectName("cleanup_btn")
    
    def _style_message_box(self, msg_box: QMessageBox):
        """Apply dark text styling to message box for readability."""
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: white;
            }}
            QMessageBox QLabel {{
                color: #2d2d2d;
                font-size: {FONT_SIZE_NORMAL}px;
            }}
            QPushButton {{
                background-color: {COLORS['slate_blue']};
                color: white;
                font-weight: bold;
                font-size: {FONT_SIZE_NORMAL}px;
                padding: 6px 20px;
                border: none;
                border-radius: 3px;
                min-width: 60px;
            }}
            QPushButton:hover {{
                background-color: #50608a;
            }}
        """)
    
    def _add_folder_path(self, folder_path: Path) -> bool:
        """
        Add a folder path to the comparison list.
        Can be called from button click or drag & drop.
        
        Args:
            folder_path: Path to folder to add
            
        Returns:
            True if added successfully, False otherwise
        """
        # Validate
        is_valid, error_msg = validate_folder_path(folder_path)
        if not is_valid:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Invalid Folder")
            msg.setText(error_msg)
            self._style_message_box(msg)
            msg.exec()
            return False
        
        # Check for duplicates
        if folder_path in self.folder_paths:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Duplicate Folder")
            msg.setText("This folder is already in the list.")
            self._style_message_box(msg)
            msg.exec()
            return False
        
        # Add to list
        self.folder_paths.append(folder_path)
        self.folder_list.addItem(str(folder_path))
        
        # Remember this location for next time
        self.last_folder_path = folder_path
        
        # Update buttons
        self._update_folder_buttons()
        return True
    
    def _on_add_folder(self):
        """Handle add folder button."""
        # Determine starting directory
        if self.last_folder_path:
            # Start one level up from last selected folder
            start_dir = str(self.last_folder_path.parent)
        else:
            # First time, start at home
            start_dir = str(Path.home())
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Tools Folder",
            start_dir
        )
        
        if folder:
            self._add_folder_path(Path(folder))
    
    def _on_find_tools(self):
        """Handle Find 'tools' button - search for folders named 'tools'."""
        self._search_and_add_folders('tools')
    
    def _on_find_custom(self):
        """Handle Find Other button - search for folders with custom name and path."""
        from PySide6.QtWidgets import QLineEdit
        
        # Create custom dialog for path + name
        dialog = QDialog(self)
        dialog.setWindowTitle("Find Folders")
        dialog.setMinimumWidth(600)
        
        layout = QVBoxLayout(dialog)
        
        # Instructions
        instructions = QLabel("Choose where to search and what folder name to find:")
        layout.addWidget(instructions)
        
        # Search path selection
        path_layout = QHBoxLayout()
        path_label = QLabel("Search in:")
        path_layout.addWidget(path_label)
        
        path_input = QLineEdit("C:/")
        path_layout.addWidget(path_input)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(
            lambda: self._browse_search_path(path_input)
        )
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        # Folder name input
        name_layout = QHBoxLayout()
        name_label = QLabel("Folder name:")
        name_layout.addWidget(name_label)
        
        name_input = QLineEdit("tools")
        name_layout.addWidget(name_input)
        
        layout.addLayout(name_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        ok_btn = QPushButton("Search")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # Apply styling
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text']};
            }}
            QLabel {{
                color: {COLORS['text']};
                font-size: {FONT_SIZE_NORMAL}px;
                padding: 4px;
            }}
            QLineEdit {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 3px;
                padding: 6px;
                font-size: {FONT_SIZE_NORMAL}px;
                font-family: '{FONT_FAMILY_MONO}';
            }}
            QPushButton {{
                background-color: {COLORS['slate_blue']};
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                font-size: {FONT_SIZE_NORMAL}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['cyan']};
            }}
            QPushButton:default {{
                background-color: {COLORS['cyan']};
            }}
        """)
        
        # Show dialog
        if dialog.exec() == QDialog.Accepted:
            search_path = path_input.text().strip()
            folder_name = name_input.text().strip()
            
            if folder_name and search_path:
                self._search_and_add_folders(folder_name, Path(search_path))
    
    def _browse_search_path(self, path_input: 'QLineEdit'):
        """Browse for search starting path."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Search Starting Path",
            path_input.text()
        )
        
        if folder:
            path_input.setText(folder)
    
    def _search_and_add_folders(self, folder_name: str, search_root: Path = Path('C:/')):
        """
        Search for folders with given name and add selected ones.
        
        Args:
            folder_name: Name of folders to search for
            search_root: Root path to start searching from (default C:/)
        """
        # Show search dialog
        dialog = FolderSearchDialog(folder_name, search_root, self)
        
        if dialog.exec() == QDialog.Accepted:
            # Add selected folders
            selected = dialog.get_selected_folders()
            
            for folder_path in selected:
                self._add_folder_path(folder_path)
            
            if selected:
                self.status_label.setText(f"Added {len(selected)} folder(s)")
    
    def _on_remove_folder(self):
        """Handle remove folder button."""
        current_row = self.folder_list.currentRow()
        if current_row >= 0:
            self.folder_list.takeItem(current_row)
            self.folder_paths.pop(current_row)
            self._update_folder_buttons()
    
    def _on_clear_folders(self):
        """Handle clear all folders button."""
        self.folder_list.clear()
        self.folder_paths.clear()
        self._update_folder_buttons()
        self.scan_result = None
        self.grid_table.setRowCount(0)
        self.grid_table.setColumnCount(0)
        self.conflict_label.setText("No comparison data")
    
    def _on_folder_selection_changed(self):
        """Handle folder list selection change."""
        has_selection = self.folder_list.currentRow() >= 0
        self.remove_folder_btn.setEnabled(has_selection)
    
    def _update_folder_buttons(self):
        """Update folder button states."""
        has_folders = len(self.folder_paths) > 0
        self.clear_folders_btn.setEnabled(has_folders)
        self.cleanup_old_btn.setEnabled(has_folders)
        self.compare_btn.setEnabled(len(self.folder_paths) >= 2)
        self.remove_folder_btn.setEnabled(self.folder_list.currentRow() >= 0)
    
    def _on_compare(self):
        """Handle compare button."""
        if len(self.folder_paths) < 2:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Not Enough Folders")
            msg.setText("Please add at least 2 folders to compare.")
            self._style_message_box(msg)
            msg.exec()
            return
        
        try:
            # Show scanning message
            self.status_label.setText("Scanning folders...")
            QApplication.processEvents()
            
            # Scan folders
            self.scan_result = scan_multiple_locations(self.folder_paths)
            
            # Build grid
            self._build_comparison_grid()
            
            # Update status
            conflict_count = self.scan_result.get_conflict_count()
            total_tools = len(self.scan_result.tools)
            self.conflict_label.setText(f"Conflicts: {conflict_count} / {total_tools} tools")
            self.status_label.setText(f"Compared {len(self.folder_paths)} locations")
            
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Scan Failed")
            msg.setText(f"Failed to scan folders: {e}")
            self._style_message_box(msg)
            msg.exec()
            self.status_label.setText("Scan failed")
    
    def _on_cleanup_old_folders(self):
        """Handle cleanup .OLD folders button."""
        if not self.folder_paths:
            return
        
        # Find all .OLD folders
        self.status_label.setText("Searching for .OLD folders...")
        QApplication.processEvents()
        
        old_folders = find_old_folders(self.folder_paths)
        
        if not old_folders:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("No .OLD Folders Found")
            msg.setText("No .OLD folders found in the selected locations.")
            self._style_message_box(msg)
            msg.exec()
            self.status_label.setText("No .OLD folders found")
            return
        
        # Show confirmation with count
        folder_list = "\n".join(f"• {f.name}" for f in old_folders[:10])
        if len(old_folders) > 10:
            folder_list += f"\n... and {len(old_folders) - 10} more"
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Confirm Delete")
        msg.setText(f"Found {len(old_folders)} .OLD folder(s):\n\n{folder_list}\n\nDelete all .OLD folders?\nThis cannot be undone.")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        self._style_message_box(msg)
        
        if msg.exec() != QMessageBox.Yes:
            self.status_label.setText("Cleanup cancelled")
            return
        
        # Delete folders
        import shutil
        deleted = 0
        failed = 0
        
        for folder in old_folders:
            try:
                self.status_label.setText(f"Deleting {folder.name}...")
                QApplication.processEvents()
                shutil.rmtree(folder)
                deleted += 1
            except Exception as e:
                failed += 1
        
        # Show summary
        if failed > 0:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Cleanup Complete")
            msg.setText(f"Deleted {deleted} folder(s).\nFailed to delete {failed} folder(s).")
            self._style_message_box(msg)
            msg.exec()
        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Cleanup Complete")
            msg.setText(f"Successfully deleted {deleted} .OLD folder(s).")
            self._style_message_box(msg)
            msg.exec()
        
        self.status_label.setText(f"Cleanup complete: {deleted} deleted, {failed} failed")
        
        # Refresh comparison if it exists
        if self.scan_result:
            self._on_compare()
    
    def _build_comparison_grid(self):
        """Build the comparison grid from scan results."""
        if not self.scan_result:
            return
        
        # Get tools to display
        if self.show_conflicts_only:
            tools = self.scan_result.get_tools_with_conflicts()
        else:
            tools = self.scan_result.get_all_tools_sorted()
        
        # Setup table
        self.grid_table.setRowCount(len(tools))
        self.grid_table.setColumnCount(len(self.folder_paths) + 1)
        
        # Set headers with readable names
        headers = ["Tool"] + [self._get_column_label(path) for path in self.folder_paths]
        self.grid_table.setHorizontalHeaderLabels(headers)
        
        # Populate rows
        for row, tool in enumerate(tools):
            self._populate_grid_row(row, tool)
        
        # Set row heights
        for row in range(len(tools)):
            self.grid_table.setRowHeight(row, GRID_ROW_HEIGHT)
        
        # Auto-resize columns to fit content
        self.grid_table.resizeColumnsToContents()
        
        # Add some padding to columns for breathing room
        for col in range(self.grid_table.columnCount()):
            current_width = self.grid_table.columnWidth(col)
            self.grid_table.setColumnWidth(col, current_width + 20)
        
        # Disable stretch on last column to prevent white empty column
        self.grid_table.horizontalHeader().setStretchLastSection(False)
    
    def _populate_grid_row(self, row: int, tool: ToolFolder):
        """Populate a single row in the grid."""
        # Tool name column
        name_item = QTableWidgetItem(tool.name)
        name_item.setFont(QFont(FONT_FAMILY, FONT_SIZE_NORMAL, QFont.Bold))
        name_item.setBackground(QBrush(QColor(COLORS['bg_input'])))  # Dark background
        self.grid_table.setItem(row, 0, name_item)
        
        # Location columns
        for location_idx in range(len(self.folder_paths)):
            status = tool.get_status(location_idx)
            cell_text = self._format_cell_text(tool, location_idx, status)
            
            item = QTableWidgetItem(cell_text)
            item.setFont(QFont(FONT_FAMILY_MONO, FONT_SIZE_MONO))
            
            # Set colors based on status
            status_info = STATUS[status]
            item.setForeground(QBrush(QColor(status_info['color'])))
            item.setBackground(QBrush(QColor(COLORS['bg_input'])))  # Dark background for all cells
            
            # Store metadata
            item.setData(Qt.UserRole, {
                'tool': tool,
                'location_idx': location_idx,
                'status': status
            })
            
            self.grid_table.setItem(row, location_idx + 1, item)
    
    def _format_cell_text(self, tool: ToolFolder, location_idx: int, status: str) -> str:
        """Format text for a grid cell."""
        if status == 'missing':
            return f"{STATUS[status]['symbol']} missing"
        
        folder_info = tool.locations[location_idx]
        symbol = STATUS[status]['symbol']
        date = folder_info.format_date()
        size = folder_info.format_size()
        files = folder_info.file_count
        
        return f"{symbol} {date}\n{size} ({files} files)"
    
    def _on_toggle_conflicts_filter(self):
        """Toggle showing only conflicts."""
        self.show_conflicts_only = self.conflicts_checkbox.isChecked()
        
        # Update button text
        symbol = "☑" if self.show_conflicts_only else "☐"
        self.conflicts_checkbox.setText(f"{symbol} Show Only Conflicts")
        
        # Rebuild grid
        if self.scan_result:
            self._build_comparison_grid()
    
    def _on_context_menu(self, position):
        """Show context menu for grid cell."""
        item = self.grid_table.itemAt(position)
        if not item or item.column() == 0:
            return
        
        metadata = item.data(Qt.UserRole)
        if not metadata:
            return
        
        tool = metadata['tool']
        location_idx = metadata['location_idx']
        status = metadata['status']
        
        menu = self._create_context_menu(tool, location_idx, status)
        if menu:
            menu.exec_(QCursor.pos())
    
    def _create_context_menu(self, tool: ToolFolder, location_idx: int, status: str) -> Optional[QMenu]:
        """Create context menu based on cell status."""
        menu = QMenu(self)
        
        if status == 'newest':
            menu.addAction("🔄 Distribute Newest (Rename Older)", 
                          lambda: self._distribute_newest(tool, location_idx, rename_old=True))
            menu.addAction("🔄 Distribute Newest (Delete Older)", 
                          lambda: self._distribute_newest(tool, location_idx, rename_old=False))
            menu.addSeparator()
        
        elif status == 'older':
            newest_idx = tool.get_newest_location()
            menu.addAction("⬆️ Replace with Newest", 
                          lambda: self._replace_with_newest(tool, location_idx, newest_idx))
            menu.addAction("🏷️ Rename to .OLD", 
                          lambda: self._rename_old(tool, location_idx))
            menu.addSeparator()
        
        elif status == 'missing':
            newest_idx = tool.get_newest_location()
            menu.addAction("⬇️ Copy Newest Here", 
                          lambda: self._copy_to_missing(tool, location_idx, newest_idx))
            menu.addSeparator()
        
        # Common actions for non-missing cells
        if status != 'missing':
            menu.addAction("✏️ Rename Folder",
                          lambda: self._rename_folder(tool, location_idx))
            menu.addAction("📂 Open in Explorer", 
                          lambda: self._open_in_explorer(tool, location_idx))
            menu.addSeparator()
            menu.addAction("🗑️ Delete This Folder", 
                          lambda: self._delete_folder(tool, location_idx))
        else:
            menu.addAction("📂 Open Parent Folder", 
                          lambda: self._open_parent_folder(location_idx))
        
        return menu
    
    def _distribute_newest(self, tool: ToolFolder, source_idx: int, rename_old: bool):
        """Distribute newest version to all locations."""
        # Execute immediately without confirmation
        self._execute_sync_operation(
            lambda engine: engine.distribute_newest(tool, source_idx, self.folder_paths, rename_old),
            f"Distributing {tool.name}..."
        )
    
    def _replace_with_newest(self, tool: ToolFolder, target_idx: int, source_idx: int):
        """Replace a single location with newest version."""
        source_folder = tool.locations[source_idx].path
        target_location = self.folder_paths[target_idx]
        destination = target_location / tool.name
        
        target_label = self._get_column_label(target_location)
        
        self._execute_sync_operation(
            lambda engine: engine.replace_single(source_folder, destination, rename_old=True),
            f"Replacing {tool.name} at {target_label}..."
        )
    
    def _copy_to_missing(self, tool: ToolFolder, target_idx: int, source_idx: int):
        """Copy tool to missing location."""
        source_folder = tool.locations[source_idx].path
        target_location = self.folder_paths[target_idx]
        
        target_label = self._get_column_label(target_location)
        
        self._execute_sync_operation(
            lambda engine: engine.copy_to_missing(source_folder, target_location, tool.name),
            f"Copying {tool.name} to {target_label}..."
        )
    
    def _rename_old(self, tool: ToolFolder, location_idx: int):
        """Rename folder to .OLD."""
        folder = tool.locations[location_idx].path
        
        def operation(engine):
            return engine.renamer.rename_folder_old(folder) is not None
        
        self._execute_sync_operation(operation, f"Renaming {tool.name}...")
    
    def _rename_folder(self, tool: ToolFolder, location_idx: int):
        """Rename a folder interactively."""
        from PySide6.QtWidgets import QInputDialog
        
        folder = tool.locations[location_idx].path
        current_name = folder.name
        
        # Prompt for new name
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Folder",
            f"Enter new name for '{current_name}':",
            text=current_name
        )
        
        if not ok or not new_name or new_name == current_name:
            return
        
        # Validate new name
        if '/' in new_name or '\\' in new_name or ':' in new_name:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Invalid Name")
            msg.setText("Folder name cannot contain: / \\ :")
            self._style_message_box(msg)
            msg.exec()
            return
        
        # Rename
        new_path = folder.parent / new_name
        
        if new_path.exists():
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Name Exists")
            msg.setText(f"A folder named '{new_name}' already exists.")
            self._style_message_box(msg)
            msg.exec()
            return
        
        try:
            self.status_label.setText(f"Renaming {current_name} to {new_name}...")
            QApplication.processEvents()
            
            folder.rename(new_path)
            
            self.status_label.setText(f"Renamed to {new_name}")
            
            # Refresh comparison
            self._on_compare()
            
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Rename Failed")
            msg.setText(f"Failed to rename folder: {e}")
            self._style_message_box(msg)
            msg.exec()
            self.status_label.setText(f"Rename failed: {e}")
    
    def _delete_folder(self, tool: ToolFolder, location_idx: int):
        """Delete a folder immediately without confirmation."""
        folder = tool.locations[location_idx].path
        
        self._execute_sync_operation(
            lambda engine: engine.deleter.delete_folder(folder),
            f"Deleting {tool.name}..."
        )
    
    def _execute_sync_operation(self, operation, progress_message: str):
        """Execute a sync operation with status bar updates."""
        messages = []
        
        def progress_callback(msg: str):
            messages.append(msg)
            self.status_label.setText(msg)
            # Process events so UI updates immediately
            QApplication.processEvents()
        
        try:
            # Show starting message
            self.status_label.setText(progress_message)
            QApplication.processEvents()
            
            # Execute operation
            engine = SyncEngine(progress_callback)
            result = operation(engine)
            errors = engine.get_all_errors()
            
            # Show errors if any
            if errors:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Operation Completed with Errors")
                msg.setText("\n".join(errors))
                self._style_message_box(msg)
                msg.exec()
                self.status_label.setText("Operation completed with errors")
            else:
                self.status_label.setText("Operation completed successfully")
            
            # Auto-refresh the grid
            self._on_compare()
            
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Operation Failed")
            msg.setText(f"An error occurred: {e}")
            self._style_message_box(msg)
            msg.exec()
            self.status_label.setText(f"Operation failed: {e}")
    
    def _open_in_explorer(self, tool: ToolFolder, location_idx: int):
        """Open folder in file explorer."""
        import subprocess
        import platform
        
        folder = tool.locations[location_idx].path
        
        if platform.system() == 'Windows':
            subprocess.run(['explorer', str(folder)])
        elif platform.system() == 'Darwin':
            subprocess.run(['open', str(folder)])
        else:
            subprocess.run(['xdg-open', str(folder)])
    
    def _open_parent_folder(self, location_idx: int):
        """Open parent folder in file explorer."""
        import subprocess
        import platform
        
        folder = self.folder_paths[location_idx]
        
        if platform.system() == 'Windows':
            subprocess.run(['explorer', str(folder)])
        elif platform.system() == 'Darwin':
            subprocess.run(['open', str(folder)])
        else:
            subprocess.run(['xdg-open', str(folder)])
