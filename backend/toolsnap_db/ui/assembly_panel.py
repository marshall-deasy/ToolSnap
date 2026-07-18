"""Assembly panel — view and edit assembly component relationships."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QSpinBox, QDialogButtonBox,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal

from core import repo
from core.models import Tool, Component
from core.enums import ToolCategory, ComponentRole, INDEXABLE_BODY_CATEGORIES, pretty_category
from core.database import transaction


class AssemblyPanel(QWidget):
    """Panel for viewing and editing assembly component relationships."""

    tool_navigate = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._assemblies: list[Tool] = []
        self._current_assembly: Tool | None = None
        self._children: list[tuple[Component, Tool]] = []
        self._build_ui()
        self.refresh_assembly_list()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Assembly selector
        top = QHBoxLayout()
        top.addWidget(QLabel("Assembly:"))
        self._assembly_combo = QComboBox()
        self._assembly_combo.setMinimumWidth(350)
        self._assembly_combo.currentIndexChanged.connect(self._on_assembly_selected)
        top.addWidget(self._assembly_combo, stretch=1)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_assembly_list)
        top.addWidget(refresh_btn)
        layout.addLayout(top)

        # Assembly info
        self._info_label = QLabel()
        self._info_label.setStyleSheet("color: #555; padding: 4px 0;")
        layout.addWidget(self._info_label)

        # Components table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Role", "Name", "Category", "Catalog #", "Qty", "Notes",
        ])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, stretch=1)

        # Buttons
        btn_row = QHBoxLayout()
        self._add_btn = QPushButton("Add Component")
        self._add_btn.clicked.connect(self._on_add_component)
        self._remove_btn = QPushButton("Remove Selected")
        self._remove_btn.clicked.connect(self._on_remove_component)
        btn_row.addWidget(self._add_btn)
        btn_row.addWidget(self._remove_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def refresh_assembly_list(self) -> None:
        """Reload the list of assemblies from the database."""
        self._assembly_combo.blockSignals(True)
        current_id = None
        if self._current_assembly:
            current_id = self._current_assembly.tool_id

        self._assembly_combo.clear()
        self._assemblies = [t for t in repo.get_all_tools() if t.tool_type == "assembly"]
        for tool in self._assemblies:
            label = f"{tool.name}  [{pretty_category(tool.category)}]"
            self._assembly_combo.addItem(label, tool.tool_id)

        # Restore selection
        if current_id:
            for i, t in enumerate(self._assemblies):
                if t.tool_id == current_id:
                    self._assembly_combo.setCurrentIndex(i)
                    break

        self._assembly_combo.blockSignals(False)
        if self._assemblies:
            self._on_assembly_selected(self._assembly_combo.currentIndex())

    def _on_assembly_selected(self, index: int) -> None:
        if index < 0 or index >= len(self._assemblies):
            return
        self._current_assembly = self._assemblies[index]
        self._load_components()

    def _load_components(self) -> None:
        if not self._current_assembly:
            return

        tool = self._current_assembly
        info = f"{tool.manufacturer or '—'}  •  {tool.catalog_number or '—'}  •  {tool.unit_system.value if tool.unit_system else '—'}"
        self._info_label.setText(info)

        self._children = repo.get_children(tool.tool_id)
        self._table.setRowCount(len(self._children))
        for i, (comp, child) in enumerate(self._children):
            role_val = comp.role.value if hasattr(comp.role, "value") else str(comp.role)
            self._table.setItem(i, 0, QTableWidgetItem(role_val))
            self._table.setItem(i, 1, QTableWidgetItem(child.name))
            self._table.setItem(i, 2, QTableWidgetItem(pretty_category(child.category)))
            self._table.setItem(i, 3, QTableWidgetItem(child.catalog_number or ""))
            self._table.setItem(i, 4, QTableWidgetItem(str(comp.quantity)))
            self._table.setItem(i, 5, QTableWidgetItem(comp.notes or ""))

    def _on_add_component(self) -> None:
        if not self._current_assembly:
            return

        dialog = AddComponentDialog(self._current_assembly.tool_id, self)
        if dialog.exec() == QDialog.Accepted:
            comp = dialog.get_component()
            if comp:
                with transaction():
                    repo.upsert_component(comp)
                self._load_components()

    def _on_remove_component(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        if row < 0 or row >= len(self._children):
            return

        comp, child = self._children[row]
        reply = QMessageBox.question(
            self, "Remove Component",
            f"Remove {child.name} ({comp.role.value if hasattr(comp.role, 'value') else comp.role}) from this assembly?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            role_val = comp.role.value if hasattr(comp.role, "value") else str(comp.role)
            with transaction():
                repo.delete_component(comp.parent_tool_id, comp.child_tool_id, role_val)
            self._load_components()


class AddComponentDialog(QDialog):
    """Dialog to add a component link to an assembly."""

    def __init__(self, parent_tool_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Component")
        self.setMinimumWidth(400)
        self._parent_tool_id = parent_tool_id
        self._all_tools = repo.get_all_tools()

        form = QFormLayout(self)

        self._tool_combo = QComboBox()
        for tool in self._all_tools:
            self._tool_combo.addItem(
                f"{tool.name}  [{pretty_category(tool.category)}]",
                tool.tool_id,
            )
        form.addRow("Tool:", self._tool_combo)

        self._role_combo = QComboBox()
        for role in ComponentRole:
            self._role_combo.addItem(role.value, role.value)
        form.addRow("Role:", self._role_combo)

        self._qty_spin = QSpinBox()
        self._qty_spin.setRange(1, 999)
        self._qty_spin.setValue(1)
        form.addRow("Quantity:", self._qty_spin)

        self._notes_input = QLineEdit()
        form.addRow("Notes:", self._notes_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def get_component(self) -> Component | None:
        child_id = self._tool_combo.currentData()
        if not child_id or child_id == self._parent_tool_id:
            return None
        return Component(
            parent_tool_id=self._parent_tool_id,
            child_tool_id=child_id,
            role=ComponentRole(self._role_combo.currentData()),
            quantity=self._qty_spin.value(),
            notes=self._notes_input.text().strip() or None,
        )
