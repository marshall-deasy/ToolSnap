"""Inventory panel — stock management, reorder reports, BOM export."""

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QDialogButtonBox, QFileDialog, QTabWidget, QAbstractItemView,
    QGroupBox,
)
from PySide6.QtCore import Qt

from core import repo
from core.models import Tool, InventoryRecord
from core.enums import pretty_category
from core.inventory import build_reorder_report, export_reorder_csv, export_bom_csv
from core.database import transaction
from utils.time_helpers import now_iso


class InventoryPanel(QWidget):
    """Inventory management with stock editing, low-stock alerts, and reports."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        tabs = QTabWidget()

        # Tab 1: Stock management
        self._stock_tab = StockTab()
        tabs.addTab(self._stock_tab, "Stock Levels")

        # Tab 2: Low stock / reorder
        self._reorder_tab = ReorderTab()
        tabs.addTab(self._reorder_tab, "Reorder Report")

        # Tab 3: BOM export
        self._bom_tab = BomTab()
        tabs.addTab(self._bom_tab, "BOM Export")

        tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(tabs)

    def _on_tab_changed(self, index: int) -> None:
        if index == 0:
            self._stock_tab.refresh()
        elif index == 1:
            self._reorder_tab.refresh()
        elif index == 2:
            self._bom_tab.refresh()


class StockTab(QWidget):
    """Browse all tools and edit their inventory data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools: list[Tool] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Table of tools with inventory data
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Name", "Category", "Catalog #", "Location",
            "On Hand", "Reorder Pt", "Vendor", "Unit Cost",
        ])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, stretch=1)

        btn_row = QHBoxLayout()
        edit_btn = QPushButton("Edit Inventory")
        edit_btn.clicked.connect(self._on_edit)
        btn_row.addWidget(edit_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def refresh(self) -> None:
        self._tools = repo.get_all_tools()
        self._table.setRowCount(len(self._tools))
        for i, tool in enumerate(self._tools):
            inv = repo.get_inventory(tool.tool_id)
            self._table.setItem(i, 0, QTableWidgetItem(tool.name))
            self._table.setItem(i, 1, QTableWidgetItem(pretty_category(tool.category)))
            self._table.setItem(i, 2, QTableWidgetItem(tool.catalog_number or ""))
            self._table.setItem(i, 3, QTableWidgetItem(inv.location or "" if inv else ""))

            on_hand_item = QTableWidgetItem(str(inv.quantity_on_hand) if inv else "—")
            if inv and inv.reorder_point > 0 and inv.quantity_on_hand <= inv.reorder_point:
                on_hand_item.setForeground(Qt.red)
            self._table.setItem(i, 4, on_hand_item)

            self._table.setItem(i, 5, QTableWidgetItem(str(inv.reorder_point) if inv else "—"))
            self._table.setItem(i, 6, QTableWidgetItem(inv.preferred_vendor or "" if inv else ""))
            cost_str = f"${inv.unit_cost:.2f}" if inv and inv.unit_cost else ""
            self._table.setItem(i, 7, QTableWidgetItem(cost_str))

    def _on_edit(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Select Tool", "Select a tool to edit its inventory.")
            return
        row = rows[0].row()
        tool = self._tools[row]
        existing = repo.get_inventory(tool.tool_id)

        dialog = InventoryEditDialog(tool, existing, self)
        if dialog.exec() == QDialog.Accepted:
            record = dialog.get_record()
            with transaction():
                repo.upsert_inventory(record)
            self.refresh()


class ReorderTab(QWidget):
    """Low-stock alert and reorder report."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._summary_label = QLabel()
        self._summary_label.setStyleSheet("font-size: 13px; padding: 4px 0;")
        layout.addWidget(self._summary_label)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Tool Name", "Catalog #", "Vendor", "Vendor P/N",
            "On Hand", "Order Qty", "Unit Cost", "Line Total",
        ])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, stretch=1)

        btn_row = QHBoxLayout()
        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self._on_export)
        btn_row.addWidget(export_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def refresh(self) -> None:
        report = build_reorder_report()
        all_lines = []
        for vendor, lines in sorted(report.lines_by_vendor.items()):
            all_lines.extend(lines)

        self._summary_label.setText(
            f"{report.line_count} items below reorder point across "
            f"{report.vendor_count} vendor(s)  —  Est. total: ${report.total_cost:,.2f}"
        )

        self._table.setRowCount(len(all_lines))
        for i, line in enumerate(all_lines):
            self._table.setItem(i, 0, QTableWidgetItem(line.tool_name))
            self._table.setItem(i, 1, QTableWidgetItem(line.catalog_number))
            self._table.setItem(i, 2, QTableWidgetItem(line.vendor))
            self._table.setItem(i, 3, QTableWidgetItem(line.vendor_part_number))
            self._table.setItem(i, 4, QTableWidgetItem(str(line.on_hand)))
            self._table.setItem(i, 5, QTableWidgetItem(str(line.reorder_qty)))
            cost_str = f"${line.unit_cost:.2f}" if line.unit_cost else ""
            self._table.setItem(i, 6, QTableWidgetItem(cost_str))
            total_str = f"${line.line_total:.2f}" if line.line_total else ""
            self._table.setItem(i, 7, QTableWidgetItem(total_str))

        self._report = report

    def _on_export(self) -> None:
        if not hasattr(self, "_report"):
            self.refresh()
        path, _ = QFileDialog.getSaveFileName(self, "Export Reorder Report", "reorder_report.csv", "CSV (*.csv)")
        if path:
            export_reorder_csv(self._report, Path(path))
            QMessageBox.information(self, "Exported", f"Report saved to {path}")


class BomTab(QWidget):
    """Select an assembly and export its BOM."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._assemblies: list[Tool] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("Assembly:"))
        self._combo = QComboBox()
        self._combo.setMinimumWidth(350)
        sel_row.addWidget(self._combo, stretch=1)
        export_btn = QPushButton("Export BOM CSV")
        export_btn.clicked.connect(self._on_export)
        sel_row.addWidget(export_btn)
        layout.addLayout(sel_row)

        layout.addStretch()

    def refresh(self) -> None:
        self._combo.clear()
        self._assemblies = [t for t in repo.get_all_tools() if t.tool_type == "assembly"]
        for tool in self._assemblies:
            self._combo.addItem(
                f"{tool.name}  [{pretty_category(tool.category)}]",
                tool.tool_id,
            )

    def _on_export(self) -> None:
        tool_id = self._combo.currentData()
        if not tool_id:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export BOM", "bom_export.csv", "CSV (*.csv)")
        if path:
            export_bom_csv(tool_id, Path(path))
            QMessageBox.information(self, "Exported", f"BOM saved to {path}")


class InventoryEditDialog(QDialog):
    """Dialog to create/edit an inventory record for a tool."""

    def __init__(self, tool: Tool, existing: InventoryRecord | None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Inventory — {tool.name}")
        self.setMinimumWidth(400)
        self._tool_id = tool.tool_id

        form = QFormLayout(self)

        self._location = QLineEdit(existing.location or "" if existing else "")
        self._location.setPlaceholderText("e.g. CAB-03:DWR-07")
        form.addRow("Location:", self._location)

        self._on_hand = QSpinBox()
        self._on_hand.setRange(0, 99999)
        self._on_hand.setValue(existing.quantity_on_hand if existing else 0)
        form.addRow("Qty On Hand:", self._on_hand)

        self._reorder_pt = QSpinBox()
        self._reorder_pt.setRange(0, 99999)
        self._reorder_pt.setValue(existing.reorder_point if existing else 0)
        form.addRow("Reorder Point:", self._reorder_pt)

        self._reorder_qty = QSpinBox()
        self._reorder_qty.setRange(0, 99999)
        self._reorder_qty.setValue(existing.reorder_qty if existing else 0)
        form.addRow("Reorder Qty:", self._reorder_qty)

        self._vendor = QLineEdit(existing.preferred_vendor or "" if existing else "")
        form.addRow("Preferred Vendor:", self._vendor)

        self._vendor_pn = QLineEdit(existing.vendor_part_number or "" if existing else "")
        form.addRow("Vendor Part #:", self._vendor_pn)

        self._cost = QDoubleSpinBox()
        self._cost.setRange(0, 999999.99)
        self._cost.setDecimals(2)
        self._cost.setPrefix("$")
        self._cost.setValue(existing.unit_cost or 0 if existing else 0)
        form.addRow("Unit Cost:", self._cost)

        self._notes = QLineEdit(existing.notes or "" if existing else "")
        form.addRow("Notes:", self._notes)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def get_record(self) -> InventoryRecord:
        return InventoryRecord(
            tool_id=self._tool_id,
            location=self._location.text().strip() or None,
            quantity_on_hand=self._on_hand.value(),
            reorder_point=self._reorder_pt.value(),
            reorder_qty=self._reorder_qty.value(),
            preferred_vendor=self._vendor.text().strip() or None,
            vendor_part_number=self._vendor_pn.text().strip() or None,
            unit_cost=self._cost.value() or None,
            last_counted_at=now_iso(),
            notes=self._notes.text().strip() or None,
        )
