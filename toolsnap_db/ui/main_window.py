"""
Main application window.

Layout:
    [Toolbar: Import button | DB info]
    [Tools Table (left)  |  Detail Panel (right)]
    [Status bar]
"""

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction
from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QToolBar, QStatusBar, QFileDialog,
    QMessageBox, QLabel, QWidget, QVBoxLayout,
)

from config.settings import (
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, DEFAULT_IMPORT_DIR,
)
from core.database import Database
from core.importer import run_import
from ui.tools_table import ToolsTable
from ui.detail_panel import DetailPanel


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self._db = db
        self._import_dir = DEFAULT_IMPORT_DIR

        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self._apply_theme()
        self._setup_ui()
        self._refresh_table()

    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #1a1a1a;
            }
            QToolBar {
                background: #242424;
                border-bottom: 1px solid #333;
                padding: 4px 8px;
                spacing: 8px;
            }
            QToolBar QLabel {
                color: #888;
                font-size: 12px;
            }
            QPushButton, QToolButton {
                background: #2a3a4a;
                color: #ccd;
                border: 1px solid #3a4a5a;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 12px;
            }
            QPushButton:hover, QToolButton:hover {
                background: #3a4a5a;
            }
            QPushButton:pressed, QToolButton:pressed {
                background: #1a2a3a;
            }
            QTableWidget {
                background: #1e1e1e;
                alternate-background-color: #222;
                color: #ccc;
                border: none;
                gridline-color: #333;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 4px 8px;
            }
            QTableWidget::item:selected {
                background: #2a4a6a;
                color: #eee;
            }
            QHeaderView::section {
                background: #252525;
                color: #999;
                border: none;
                border-bottom: 1px solid #333;
                border-right: 1px solid #2a2a2a;
                padding: 6px 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QLineEdit {
                background: #252525;
                color: #ccc;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #4a6a8a;
            }
            QComboBox {
                background: #252525;
                color: #ccc;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: #252525;
                color: #ccc;
                selection-background-color: #3a4a5a;
            }
            QScrollArea {
                background: #1e1e1e;
                border-left: 1px solid #333;
            }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 10px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: #3a3a3a;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QStatusBar {
                background: #242424;
                color: #888;
                border-top: 1px solid #333;
                font-size: 11px;
            }
            QSplitter::handle {
                background: #333;
                width: 1px;
            }
            QMessageBox {
                background: #1e1e1e;
                color: #ccc;
            }
        """)

    def _setup_ui(self):
        # --- Toolbar ---
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        import_action = QAction("Import Sessions", self)
        import_action.triggered.connect(self._on_import)
        toolbar.addAction(import_action)

        set_dir_action = QAction("Set Import Folder", self)
        set_dir_action.triggered.connect(self._on_set_import_dir)
        toolbar.addAction(set_dir_action)

        toolbar.addSeparator()

        self._dir_label = QLabel(f"Import: {self._import_dir}")
        toolbar.addWidget(self._dir_label)

        spacer = QWidget()
        spacer.setSizePolicy(
            spacer.sizePolicy().horizontalPolicy(),
            spacer.sizePolicy().verticalPolicy()
        )
        from PySide6.QtWidgets import QSizePolicy
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        self._db_label = QLabel("")
        toolbar.addWidget(self._db_label)

        # --- Central: splitter with table + detail ---
        splitter = QSplitter(Qt.Horizontal)

        self._tools_table = ToolsTable()
        self._tools_table.tool_selected.connect(self._on_tool_selected)
        splitter.addWidget(self._tools_table)

        self._detail_panel = DetailPanel(self._db)
        splitter.addWidget(self._detail_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        self.setCentralWidget(splitter)

        # --- Status bar ---
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready")

    def _refresh_table(self):
        """Reload all tools from DB into the table."""
        tools = self._db.get_all_tools()
        self._tools_table.load_tools(tools)
        count = self._db.tool_count()
        cats = self._db.category_counts()
        cat_summary = ", ".join(
            f"{v} {k.lower().replace('_', ' ')}"
            for k, v in sorted(cats.items(), key=lambda x: -x[1])[:4]
        )
        self._db_label.setText(
            f"{count} tools" + (f"  ({cat_summary})" if cat_summary else "")
        )

    def _on_tool_selected(self, tool_id: str):
        self._detail_panel.show_tool(tool_id)

    def _on_import(self):
        """Run the import pipeline against the configured directory."""
        if not self._import_dir.is_dir():
            QMessageBox.warning(
                self, "Import",
                f"Import directory does not exist:\n{self._import_dir}\n\n"
                "Use 'Set Import Folder' to choose a valid directory."
            )
            return

        self._status.showMessage("Importing...")
        result = run_import(self._import_dir, self._db)
        self._refresh_table()

        if result.errors:
            error_text = "\n".join(result.errors[:10])
            QMessageBox.warning(
                self, "Import Errors",
                f"{result.summary}\n\nErrors:\n{error_text}"
            )
        else:
            self._status.showMessage(result.summary.replace("\n", "  |  "))

    def _on_set_import_dir(self):
        """Let user pick the import directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Import Folder",
            str(self._import_dir),
        )
        if dir_path:
            self._import_dir = Path(dir_path)
            self._dir_label.setText(f"Import: {self._import_dir}")
            self._status.showMessage(f"Import directory set to {dir_path}")
