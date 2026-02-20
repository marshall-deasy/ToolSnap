"""
FolderSync Dialogs
Dialog windows for folder operations.
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QScrollArea, QWidget, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from config import COLORS, FONT_FAMILY, FONT_FAMILY_MONO, FONT_SIZE_NORMAL, FONT_SIZE_SMALL
from scanner import search_folders_by_name


class FolderSearchDialog(QDialog):
    """
    Dialog for searching and selecting folders by name.
    Searches common locations on C drive and presents results in a checklist.
    """
    
    def __init__(self, folder_name: str, parent=None):
        """
        Args:
            folder_name: Name of folders to search for (e.g., 'tools')
            parent: Parent widget
        """
        super().__init__(parent)
        self.folder_name = folder_name
        self.selected_folders: list[Path] = []
        
        self.setWindowTitle(f"Search for '{folder_name}' Folders")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        
        # Search for folders
        self._search_and_build_ui()
        
        # Apply styling
        self._apply_styles()
    
    def _search_and_build_ui(self):
        """Search for folders and build the UI."""
        # Show progress message
        layout = QVBoxLayout(self)
        progress_label = QLabel(f"Searching for '{self.folder_name}' folders...")
        progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(progress_label)
        
        # Process events to show the dialog
        self.show()
        QApplication.processEvents()
        
        # Perform search
        found_folders = search_folders_by_name(
            search_root=Path('C:/'),
            folder_name=self.folder_name,
            max_depth=3
        )
        
        # Clear progress message and rebuild UI with results
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self._build_results_ui(found_folders)
    
    def _build_results_ui(self, folders: list[Path]):
        """
        Build UI showing search results.
        
        Args:
            folders: List of found folder paths
        """
        layout = QVBoxLayout(self)
        
        if not folders:
            # No results found
            no_results = QLabel(f"No '{self.folder_name}' folders found in common locations.")
            no_results.setWordWrap(True)
            layout.addWidget(no_results)
            
            # Close button
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.reject)
            btn_layout.addWidget(close_btn)
            layout.addLayout(btn_layout)
            
            return
        
        # Results header
        header = QLabel(f"Found {len(folders)} '{self.folder_name}' folder(s). Select which to add:")
        header.setWordWrap(True)
        layout.addWidget(header)
        
        # Scrollable checkbox list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(4)
        
        self.checkboxes: list[tuple[QCheckBox, Path]] = []
        
        for folder in folders:
            cb = QCheckBox(str(folder))
            cb.setChecked(True)  # Select all by default
            scroll_layout.addWidget(cb)
            self.checkboxes.append((cb, folder))
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all)
        btn_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self._deselect_all)
        btn_layout.addWidget(deselect_all_btn)
        
        btn_layout.addStretch()
        
        add_btn = QPushButton("Add Selected")
        add_btn.clicked.connect(self._on_add_selected)
        add_btn.setDefault(True)
        btn_layout.addWidget(add_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _select_all(self):
        """Select all checkboxes."""
        for cb, _ in self.checkboxes:
            cb.setChecked(True)
    
    def _deselect_all(self):
        """Deselect all checkboxes."""
        for cb, _ in self.checkboxes:
            cb.setChecked(False)
    
    def _on_add_selected(self):
        """Handle Add Selected button."""
        self.selected_folders = [
            folder for cb, folder in self.checkboxes if cb.isChecked()
        ]
        self.accept()
    
    def _apply_styles(self):
        """Apply dark theme styling."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text']};
            }}
            QLabel {{
                color: {COLORS['text']};
                font-size: {FONT_SIZE_NORMAL}px;
                padding: 8px;
            }}
            QCheckBox {{
                color: {COLORS['text']};
                font-family: '{FONT_FAMILY_MONO}';
                font-size: {FONT_SIZE_SMALL}px;
                spacing: 8px;
                padding: 4px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QPushButton {{
                background-color: {COLORS['slate_blue']};
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                font-size: {FONT_SIZE_NORMAL}px;
                font-family: '{FONT_FAMILY}';
            }}
            QPushButton:hover {{
                background-color: {COLORS['cyan']};
            }}
            QPushButton:default {{
                background-color: {COLORS['cyan']};
            }}
            QScrollArea {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 3px;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {COLORS['bg_input']};
            }}
        """)
    
    def get_selected_folders(self) -> list[Path]:
        """
        Get list of selected folders.
        
        Returns:
            List of folder paths user selected
        """
        return self.selected_folders
