"""Compatibility panel — view and manage insert/body compatibility links."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox, QRadioButton, QButtonGroup,
    QAbstractItemView,
)
from PySide6.QtCore import Qt

from core import repo
from core.models import Tool, CompatibilityLink
from core.enums import ToolCategory, INDEXABLE_BODY_CATEGORIES, pretty_category
from core.database import transaction


class CompatibilityPanel(QWidget):
    """Panel showing insert/body compatibility relationships."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = "body"  # "body" = select body, show inserts; "insert" = opposite
        self._tools: list[Tool] = []
        self._results: list[tuple[CompatibilityLink, Tool]] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Mode toggle
        mode_row = QHBoxLayout()
        self._mode_group = QButtonGroup(self)
        self._body_radio = QRadioButton("Select Body → Show Compatible Inserts")
        self._body_radio.setChecked(True)
        self._insert_radio = QRadioButton("Select Insert → Show Compatible Bodies")
        self._mode_group.addButton(self._body_radio)
        self._mode_group.addButton(self._insert_radio)
        self._body_radio.toggled.connect(self._on_mode_changed)
        mode_row.addWidget(self._body_radio)
        mode_row.addWidget(self._insert_radio)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        # Tool selector
        sel_row = QHBoxLayout()
        self._selector_label = QLabel("Body:")
        sel_row.addWidget(self._selector_label)
        self._tool_combo = QComboBox()
        self._tool_combo.setMinimumWidth(350)
        self._tool_combo.currentIndexChanged.connect(self._on_tool_selected)
        sel_row.addWidget(self._tool_combo, stretch=1)
        layout.addLayout(sel_row)

        # Results table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Name", "Category", "Manufacturer", "Catalog #", "Fit Notes"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, stretch=1)

        # Buttons
        btn_row = QHBoxLayout()
        self._add_btn = QPushButton("Add Compatibility Link")
        self._add_btn.clicked.connect(self._on_add_link)
        self._remove_btn = QPushButton("Remove Selected")
        self._remove_btn.clicked.connect(self._on_remove_link)
        btn_row.addWidget(self._add_btn)
        btn_row.addWidget(self._remove_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def refresh(self) -> None:
        """Reload tool lists based on current mode."""
        self._tool_combo.blockSignals(True)
        self._tool_combo.clear()

        if self._mode == "body":
            self._selector_label.setText("Body:")
            body_cats = {cat.value for cat in INDEXABLE_BODY_CATEGORIES}
            self._tools = [t for t in repo.get_all_tools() if t.category.value in body_cats]
        else:
            self._selector_label.setText("Insert:")
            self._tools = [t for t in repo.get_all_tools() if t.category == ToolCategory.INSERT]

        for tool in self._tools:
            self._tool_combo.addItem(
                f"{tool.name}  [{pretty_category(tool.category)}]",
                tool.tool_id,
            )

        self._tool_combo.blockSignals(False)
        if self._tools:
            self._on_tool_selected(0)
        else:
            self._table.setRowCount(0)

    def _on_mode_changed(self, checked: bool) -> None:
        if not checked:
            return
        self._mode = "body" if self._body_radio.isChecked() else "insert"
        self.refresh()

    def _on_tool_selected(self, index: int) -> None:
        if index < 0 or index >= len(self._tools):
            return
        tool = self._tools[index]

        if self._mode == "body":
            self._results = repo.get_compatible_inserts(tool.tool_id)
        else:
            self._results = repo.get_compatible_bodies(tool.tool_id)

        self._table.setRowCount(len(self._results))
        for i, (link, related) in enumerate(self._results):
            self._table.setItem(i, 0, QTableWidgetItem(related.name))
            self._table.setItem(i, 1, QTableWidgetItem(pretty_category(related.category)))
            self._table.setItem(i, 2, QTableWidgetItem(related.manufacturer or ""))
            self._table.setItem(i, 3, QTableWidgetItem(related.catalog_number or ""))
            self._table.setItem(i, 4, QTableWidgetItem(link.fit_notes or ""))

    def _on_add_link(self) -> None:
        idx = self._tool_combo.currentIndex()
        if idx < 0 or idx >= len(self._tools):
            return

        selected_tool = self._tools[idx]

        if self._mode == "body":
            # Pick an insert to link
            inserts = [t for t in repo.get_all_tools() if t.category == ToolCategory.INSERT]
            dialog = PickToolDialog("Select Insert", inserts, self)
            if dialog.exec() == QDialog.Accepted:
                picked_id = dialog.get_selected_id()
                if picked_id:
                    link = CompatibilityLink(body_tool_id=selected_tool.tool_id, insert_tool_id=picked_id)
                    with transaction():
                        repo.upsert_compatibility(link)
                    self._on_tool_selected(idx)
        else:
            # Pick a body to link
            body_cats = {cat.value for cat in INDEXABLE_BODY_CATEGORIES}
            bodies = [t for t in repo.get_all_tools() if t.category.value in body_cats]
            dialog = PickToolDialog("Select Body", bodies, self)
            if dialog.exec() == QDialog.Accepted:
                picked_id = dialog.get_selected_id()
                if picked_id:
                    link = CompatibilityLink(body_tool_id=picked_id, insert_tool_id=selected_tool.tool_id)
                    with transaction():
                        repo.upsert_compatibility(link)
                    self._on_tool_selected(idx)

    def _on_remove_link(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        if row < 0 or row >= len(self._results):
            return

        link, related = self._results[row]
        reply = QMessageBox.question(
            self, "Remove Compatibility",
            f"Remove compatibility link with {related.name}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            with transaction():
                repo.delete_compatibility(link.body_tool_id, link.insert_tool_id)
            self._on_tool_selected(self._tool_combo.currentIndex())


class PickToolDialog(QDialog):
    """Simple dialog to pick a tool from a list."""

    def __init__(self, title: str, tools: list[Tool], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self._tools = tools

        layout = QFormLayout(self)
        self._combo = QComboBox()
        for tool in tools:
            self._combo.addItem(
                f"{tool.name}  [{tool.manufacturer or '—'}  {tool.catalog_number or '—'}]",
                tool.tool_id,
            )
        layout.addRow("Tool:", self._combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_selected_id(self) -> str | None:
        return self._combo.currentData()
