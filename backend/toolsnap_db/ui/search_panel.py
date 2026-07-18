"""Search panel — tool list with search/filter, linked to detail view."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QAbstractItemView,
    QMenu, QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from core import repo
from core.models import Tool
from core.enums import ToolCategory, pretty_category
from core.database import transaction
from ui.widgets import SearchBar
from ui.tool_detail import ToolDetailPanel


class SearchPanel(QWidget):
    """Main search/browse panel — tool list on the left, detail on the right."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools: list[Tool] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Search bar
        categories = [cat.value for cat in ToolCategory]
        self._search_bar = SearchBar(categories)
        self._search_bar.search_triggered.connect(self._on_search)
        layout.addWidget(self._search_bar)

        # Count label
        self._count_label = QLabel()
        self._count_label.setStyleSheet("color: #666; padding: 4px 0;")
        layout.addWidget(self._count_label)

        # Splitter: table left, detail right
        splitter = QSplitter(Qt.Horizontal)

        # Tool table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Name", "Category", "Manufacturer", "Catalog #", "Type"])
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        header.resizeSection(0, 180)   # Name
        header.resizeSection(1, 130)   # Category
        header.resizeSection(2, 120)   # Manufacturer
        header.resizeSection(3, 110)   # Catalog #
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed) if self._table.selectionModel() else None
        self._table.setAlternatingRowColors(True)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        splitter.addWidget(self._table)

        # Detail panel
        self._detail = ToolDetailPanel()
        self._detail.tool_selected.connect(self._navigate_to_tool)
        splitter.addWidget(self._detail)

        splitter.setSizes([500, 600])
        layout.addWidget(splitter, stretch=1)

    def refresh(self) -> None:
        """Reload the tool list from the database."""
        self._on_search("", "")

    def _on_search(self, query: str, category: str) -> None:
        cat_enum = ToolCategory(category) if category else None
        self._tools = repo.search_tools(query=query, category=cat_enum)
        self._populate_table()

    def _populate_table(self) -> None:
        self._table.setRowCount(len(self._tools))
        for i, tool in enumerate(self._tools):
            self._table.setItem(i, 0, QTableWidgetItem(tool.name))
            self._table.setItem(i, 1, QTableWidgetItem(pretty_category(tool.category)))
            self._table.setItem(i, 2, QTableWidgetItem(tool.manufacturer or ""))
            self._table.setItem(i, 3, QTableWidgetItem(tool.catalog_number or ""))
            self._table.setItem(i, 4, QTableWidgetItem(tool.tool_type))

        self._count_label.setText(f"{len(self._tools)} tool{'s' if len(self._tools) != 1 else ''}")

        # Connect selection after populating
        sel_model = self._table.selectionModel()
        if sel_model:
            sel_model.selectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            if 0 <= row < len(self._tools):
                self._detail.show_tool(self._tools[row].tool_id)

    def _navigate_to_tool(self, tool_id: str) -> None:
        """Navigate to a tool by ID (e.g. when clicking a linked tool in detail)."""
        for i, tool in enumerate(self._tools):
            if tool.tool_id == tool_id:
                self._table.selectRow(i)
                return
        # Tool not in current search — do a fresh load
        self._tools = repo.get_all_tools()
        self._populate_table()
        for i, tool in enumerate(self._tools):
            if tool.tool_id == tool_id:
                self._table.selectRow(i)
                return
        # Fallback: just show detail directly
        self._detail.show_tool(tool_id)

    # ── Context menu ───────────────────────────────────────────────

    def _on_context_menu(self, position) -> None:
        index = self._table.indexAt(position)
        if not index.isValid():
            return
        row = index.row()
        if row < 0 or row >= len(self._tools):
            return

        tool = self._tools[row]
        menu = QMenu(self)

        delete_action = QAction(f'Delete "{tool.name}"', self)
        delete_action.triggered.connect(lambda: self._delete_tool(tool))
        menu.addAction(delete_action)

        menu.exec(self._table.viewport().mapToGlobal(position))

    def _delete_tool(self, tool: Tool) -> None:
        reply = QMessageBox.warning(
            self,
            "Delete Tool",
            f'Permanently delete "{tool.name}"?\n\n'
            f"This also removes any component links, compatibility entries, "
            f"and inventory records for this tool.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        with transaction():
            repo.delete_tool(tool.tool_id)
        self.refresh()
