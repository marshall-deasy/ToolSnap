"""
Tools table view — sortable, searchable table of all tools in the database.

Displays: name, category, manufacturer, catalog#, type, status, modified date.
Emits a signal when a row is selected so the detail panel can update.
"""

import json
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QLabel, QHeaderView, QAbstractItemView,
)

# Category display names (matches ToolCategory.kt)
_CATEGORY_DISPLAY = {
    "END_MILL": "End Mill",
    "DRILL": "Drill",
    "TAP": "Tap",
    "REAMER": "Reamer",
    "INDEXABLE_MILL_BODY": "Indexable Mill Body",
    "INDEXABLE_DRILL_BODY": "Indexable Drill Body",
    "BORING_BAR_BODY": "Boring Bar Body",
    "TURNING_HOLDER": "Turning Holder",
    "THREADING_HOLDER": "Threading Holder",
    "GROOVING_HOLDER": "Grooving / Parting Holder",
    "INSERT": "Insert",
    "SCREW": "Insert Screw",
    "SHIM": "Shim / Seat",
    "CLAMP": "Clamp",
    "WEDGE": "Wedge",
    "HOLDER": "Holder / Adapter",
    "COLLET": "Collet",
    "RETENTION_KNOB": "Retention Knob",
    "OTHER": "Other",
}

_COLUMNS = [
    ("Name", 240),
    ("Category", 160),
    ("Manufacturer", 140),
    ("Catalog #", 150),
    ("Type", 80),
    ("Status", 80),
    ("Modified", 140),
]

# Subtle category colors for the category cell background
_CATEGORY_COLORS = {
    "END_MILL": "#1a3a4a",
    "DRILL": "#1a3a4a",
    "TAP": "#1a3a4a",
    "REAMER": "#1a3a4a",
    "INDEXABLE_MILL_BODY": "#3a2a1a",
    "INDEXABLE_DRILL_BODY": "#3a2a1a",
    "BORING_BAR_BODY": "#3a2a1a",
    "TURNING_HOLDER": "#3a2a1a",
    "THREADING_HOLDER": "#3a2a1a",
    "GROOVING_HOLDER": "#3a2a1a",
    "INSERT": "#2a1a3a",
    "SCREW": "#1a2a1a",
    "SHIM": "#1a2a1a",
    "CLAMP": "#1a2a1a",
    "WEDGE": "#1a2a1a",
    "HOLDER": "#1a2a3a",
    "COLLET": "#1a2a3a",
    "RETENTION_KNOB": "#1a2a3a",
}


class ToolsTable(QWidget):
    """Table widget with search bar and category filter."""

    tool_selected = Signal(str)  # emits toolId

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools: list[dict] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # --- Filter bar ---
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search tools...")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._apply_filter)
        filter_bar.addWidget(self._search, stretch=1)

        self._category_filter = QComboBox()
        self._category_filter.setMinimumWidth(180)
        self._category_filter.addItem("All Categories", "")
        for key, display in _CATEGORY_DISPLAY.items():
            self._category_filter.addItem(display, key)
        self._category_filter.currentIndexChanged.connect(self._apply_filter)
        filter_bar.addWidget(self._category_filter)

        self._count_label = QLabel("0 tools")
        self._count_label.setStyleSheet("color: #888; font-size: 12px;")
        filter_bar.addWidget(self._count_label)

        layout.addLayout(filter_bar)

        # --- Table ---
        self._table = QTableWidget()
        self._table.setColumnCount(len(_COLUMNS))
        self._table.setHorizontalHeaderLabels([c[0] for c in _COLUMNS])
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setSortingEnabled(True)
        self._table.setShowGrid(False)

        header = self._table.horizontalHeader()
        for i, (_, width) in enumerate(_COLUMNS):
            header.resizeSection(i, width)
        header.setStretchLastSection(True)

        self._table.currentCellChanged.connect(self._on_selection_changed)

        layout.addWidget(self._table)

    def load_tools(self, tools: list[dict]):
        """Replace the table contents with a new list of tools."""
        self._tools = tools
        self._apply_filter()

    def _apply_filter(self):
        """Filter displayed rows by search text and category."""
        query = self._search.text().strip().lower()
        cat_filter = self._category_filter.currentData()

        filtered = []
        for t in self._tools:
            if cat_filter and t.get("category") != cat_filter:
                continue
            if query:
                searchable = " ".join([
                    t.get("name", ""),
                    t.get("manufacturer", "") or "",
                    t.get("catalogNumber", "") or "",
                    t.get("description", "") or "",
                    json.dumps(t.get("attributes", {})),
                ]).lower()
                if query not in searchable:
                    continue
            filtered.append(t)

        self._populate_table(filtered)
        self._count_label.setText(
            f"{len(filtered)} of {len(self._tools)} tools"
        )

    def _populate_table(self, tools: list[dict]):
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(tools))

        for row, tool in enumerate(tools):
            tool_id = tool.get("toolId", "")
            category = tool.get("category", "OTHER")

            items = [
                self._make_item(tool.get("name", ""), tool_id),
                self._make_item(
                    _CATEGORY_DISPLAY.get(category, category), tool_id
                ),
                self._make_item(tool.get("manufacturer") or "—", tool_id),
                self._make_item(tool.get("catalogNumber") or "—", tool_id),
                self._make_item(tool.get("type", ""), tool_id),
                self._make_item(tool.get("status", ""), tool_id),
                self._make_item(
                    (tool.get("modifiedAt") or "")[:19].replace("T", " "),
                    tool_id
                ),
            ]

            # Tint the category cell
            cat_color = _CATEGORY_COLORS.get(category)
            if cat_color:
                items[1].setBackground(QColor(cat_color))

            for col, item in enumerate(items):
                self._table.setItem(row, col, item)

        self._table.setSortingEnabled(True)

    @staticmethod
    def _make_item(text: str, tool_id: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setData(Qt.UserRole, tool_id)
        return item

    def _on_selection_changed(self, row, col, prev_row, prev_col):
        if row < 0:
            return
        item = self._table.item(row, 0)
        if item:
            tool_id = item.data(Qt.UserRole)
            self.tool_selected.emit(tool_id)
