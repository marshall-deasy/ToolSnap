"""Tool detail panel — displays full information for a single tool."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QLineEdit, QComboBox, QMessageBox,
    QSpinBox,
)
from PySide6.QtCore import Qt, Signal

from core.models import Tool, Component
from core.enums import ToolCategory, ComponentRole, CATEGORY_ATTRIBUTES, pretty_category, pretty_attribute
from core import repo
from ui.widgets import PhotoViewer, TagDisplay, AttributeGrid


class ToolDetailPanel(QWidget):
    """Full detail view for a selected tool."""

    tool_selected = Signal(str)  # emitted when user clicks a linked tool
    add_to_bom = Signal(str, int)  # (tool_id, quantity) — emitted by Add to BOM button

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_tool: Tool | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setSpacing(12)

        # Header
        self._name_label = QLabel()
        self._name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._meta_label = QLabel()
        self._meta_label.setStyleSheet("color: #666;")
        self._content_layout.addWidget(self._name_label)
        self._content_layout.addWidget(self._meta_label)

        # Add to BOM row
        bom_row = QHBoxLayout()
        self._bom_qty_spin = QSpinBox()
        self._bom_qty_spin.setRange(1, 999)
        self._bom_qty_spin.setValue(1)
        self._bom_qty_spin.setPrefix("Qty: ")
        self._bom_qty_spin.setFixedWidth(90)
        self._bom_btn = QPushButton("+ Add to BOM")
        self._bom_btn.setStyleSheet(
            "QPushButton { background: #27ae60; color: white; font-weight: bold;"
            " padding: 4px 14px; border-radius: 3px; }"
            "QPushButton:hover { background: #219a52; }"
        )
        self._bom_btn.clicked.connect(self._on_add_to_bom)
        self._bom_btn.setEnabled(False)
        bom_row.addWidget(self._bom_qty_spin)
        bom_row.addWidget(self._bom_btn)
        bom_row.addStretch()
        self._content_layout.addLayout(bom_row)

        # Photos
        self._photos = PhotoViewer()
        self._content_layout.addWidget(self._photos)

        # Attributes
        self._attrs_group = QGroupBox("Attributes")
        attrs_layout = QVBoxLayout(self._attrs_group)
        self._attr_grid = AttributeGrid()
        attrs_layout.addWidget(self._attr_grid)
        self._content_layout.addWidget(self._attrs_group)

        # Tags
        self._tags = TagDisplay()
        self._content_layout.addWidget(self._tags)

        # Notes
        self._notes_label = QLabel()
        self._notes_label.setWordWrap(True)
        self._notes_label.setStyleSheet("color: #444; font-style: italic;")
        self._content_layout.addWidget(self._notes_label)

        # Children (components of this assembly)
        self._children_group = QGroupBox("Components")
        children_layout = QVBoxLayout(self._children_group)
        self._children_table = QTableWidget()
        self._children_table.setColumnCount(5)
        self._children_table.setHorizontalHeaderLabels(["Role", "Name", "Category", "Catalog #", "Qty"])
        self._children_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._children_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._children_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._children_table.doubleClicked.connect(self._on_child_double_click)
        children_layout.addWidget(self._children_table)
        self._content_layout.addWidget(self._children_group)

        # Parents (assemblies that contain this tool)
        self._parents_group = QGroupBox("Used In Assemblies")
        parents_layout = QVBoxLayout(self._parents_group)
        self._parents_table = QTableWidget()
        self._parents_table.setColumnCount(4)
        self._parents_table.setHorizontalHeaderLabels(["Name", "Category", "Role", "Catalog #"])
        self._parents_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._parents_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._parents_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._parents_table.doubleClicked.connect(self._on_parent_double_click)
        parents_layout.addWidget(self._parents_table)
        self._content_layout.addWidget(self._parents_group)

        self._content_layout.addStretch()
        scroll.setWidget(self._content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def show_tool(self, tool_id: str) -> None:
        """Load and display a tool by ID."""
        tool = repo.get_tool(tool_id)
        if not tool:
            return
        self._current_tool = tool

        # Header
        self._name_label.setText(tool.name)
        self._bom_btn.setEnabled(True)
        self._bom_qty_spin.setValue(1)
        meta_parts = [pretty_category(tool.category)]
        if tool.manufacturer:
            meta_parts.append(tool.manufacturer)
        if tool.catalog_number:
            meta_parts.append(tool.catalog_number)
        if tool.unit_system:
            meta_parts.append(tool.unit_system.value)
        self._meta_label.setText("  •  ".join(meta_parts))

        # Photos
        self._photos.set_photos(tool.photos)

        # Attributes
        expected = CATEGORY_ATTRIBUTES.get(tool.category, [])
        self._attr_grid.set_attributes(tool.attributes, expected)
        self._attrs_group.setVisible(bool(tool.attributes))

        # Tags
        self._tags.set_tags(tool.tags)
        self._tags.setVisible(bool(tool.tags))

        # Notes
        self._notes_label.setText(tool.notes or "")
        self._notes_label.setVisible(bool(tool.notes))

        # Children
        children = repo.get_children(tool.tool_id)
        self._children_table.setRowCount(len(children))
        for i, (comp, child) in enumerate(children):
            role_val = comp.role.value if hasattr(comp.role, "value") else comp.role
            self._children_table.setItem(i, 0, QTableWidgetItem(role_val))
            self._children_table.setItem(i, 1, QTableWidgetItem(child.name))
            self._children_table.setItem(i, 2, QTableWidgetItem(pretty_category(child.category)))
            self._children_table.setItem(i, 3, QTableWidgetItem(child.catalog_number or ""))
            self._children_table.setItem(i, 4, QTableWidgetItem(str(comp.quantity)))
        self._children_group.setVisible(len(children) > 0)
        self._child_ids = [child.tool_id for _, child in children]

        # Parents
        parents = repo.get_parents(tool.tool_id)
        self._parents_table.setRowCount(len(parents))
        for i, (comp, parent) in enumerate(parents):
            self._parents_table.setItem(i, 0, QTableWidgetItem(parent.name))
            self._parents_table.setItem(i, 1, QTableWidgetItem(pretty_category(parent.category)))
            role_val = comp.role.value if hasattr(comp.role, "value") else comp.role
            self._parents_table.setItem(i, 2, QTableWidgetItem(role_val))
            self._parents_table.setItem(i, 3, QTableWidgetItem(parent.catalog_number or ""))
        self._parents_group.setVisible(len(parents) > 0)
        self._parent_ids = [parent.tool_id for _, parent in parents]

    def _on_child_double_click(self, index) -> None:
        row = index.row()
        if 0 <= row < len(self._child_ids):
            self.tool_selected.emit(self._child_ids[row])

    def _on_parent_double_click(self, index) -> None:
        row = index.row()
        if 0 <= row < len(self._parent_ids):
            self.tool_selected.emit(self._parent_ids[row])

    def _on_add_to_bom(self) -> None:
        if self._current_tool:
            self.add_to_bom.emit(
                self._current_tool.tool_id,
                self._bom_qty_spin.value(),
            )
