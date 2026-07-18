"""BOM panel — build a parts list, copy to clipboard, export PDF."""

import os
import subprocess
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QAbstractItemView,
    QPushButton, QSpinBox, QMessageBox, QFileDialog, QGroupBox,
    QApplication,
)
from PySide6.QtCore import Qt

from core import repo
from core.models import Tool
from core.enums import ToolCategory, pretty_category
from core.bom import build_bom, bom_to_text, BomLine
from ui.widgets import SearchBar


class BomPanel(QWidget):
    """BOM builder tab — pick tools, set quantities, export."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_tools: list[Tool] = []
        self._filtered_tools: list[Tool] = []
        # Selections: list of (tool_id, qty) currently in the BOM
        self._bom_items: list[tuple[str, int]] = []
        self._bom_lines: list[BomLine] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Horizontal)

        # ── Left: Tool picker ──────────────────────────────────────
        picker = QWidget()
        picker_layout = QVBoxLayout(picker)
        picker_layout.setContentsMargins(0, 0, 0, 0)

        picker_label = QLabel("Available Tools")
        picker_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        picker_layout.addWidget(picker_label)

        categories = [cat.value for cat in ToolCategory]
        self._search_bar = SearchBar(categories)
        self._search_bar.search_triggered.connect(self._on_search)
        picker_layout.addWidget(self._search_bar)

        self._picker_table = QTableWidget()
        self._picker_table.setColumnCount(4)
        self._picker_table.setHorizontalHeaderLabels(["Name", "Category", "Mfg", "Catalog #"])
        header = self._picker_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        header.resizeSection(0, 160)
        header.resizeSection(1, 110)
        header.resizeSection(2, 100)
        self._picker_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._picker_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._picker_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._picker_table.setAlternatingRowColors(True)
        picker_layout.addWidget(self._picker_table, stretch=1)

        add_row = QHBoxLayout()
        self._add_qty_spin = QSpinBox()
        self._add_qty_spin.setRange(1, 999)
        self._add_qty_spin.setValue(1)
        self._add_qty_spin.setPrefix("Qty: ")
        self._add_qty_spin.setFixedWidth(90)

        add_btn = QPushButton("Add to BOM →")
        add_btn.clicked.connect(self._add_selected)
        self._picker_table.doubleClicked.connect(self._add_selected)

        add_row.addWidget(self._add_qty_spin)
        add_row.addWidget(add_btn, stretch=1)
        picker_layout.addLayout(add_row)

        splitter.addWidget(picker)

        # ── Right: BOM table + actions ─────────────────────────────
        bom_side = QWidget()
        bom_layout = QVBoxLayout(bom_side)
        bom_layout.setContentsMargins(0, 0, 0, 0)

        bom_label = QLabel("Bill of Materials")
        bom_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        bom_layout.addWidget(bom_label)

        self._bom_table = QTableWidget()
        self._bom_table.setColumnCount(6)
        self._bom_table.setHorizontalHeaderLabels([
            "Qty", "Name", "Category", "Manufacturer", "Catalog #", "Notes",
        ])
        bom_header = self._bom_table.horizontalHeader()
        bom_header.setSectionResizeMode(QHeaderView.Interactive)
        bom_header.setStretchLastSection(True)
        bom_header.resizeSection(0, 45)
        bom_header.resizeSection(1, 160)
        bom_header.resizeSection(2, 110)
        bom_header.resizeSection(3, 110)
        bom_header.resizeSection(4, 100)
        self._bom_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._bom_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._bom_table.setAlternatingRowColors(True)
        bom_layout.addWidget(self._bom_table, stretch=1)

        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet("color: #555; padding: 4px 0;")
        bom_layout.addWidget(self._summary_label)

        # Action buttons
        btn_row = QHBoxLayout()

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected)
        btn_row.addWidget(remove_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_bom)
        btn_row.addWidget(clear_btn)

        btn_row.addStretch()

        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.setStyleSheet("font-weight: bold;")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_row.addWidget(copy_btn)

        pdf_btn = QPushButton("📄 Export PDF")
        pdf_btn.setStyleSheet("font-weight: bold;")
        pdf_btn.clicked.connect(self._export_pdf)
        btn_row.addWidget(pdf_btn)

        bom_layout.addLayout(btn_row)

        splitter.addWidget(bom_side)
        splitter.setSizes([450, 600])

        layout.addWidget(splitter, stretch=1)

        # Initial load
        self._refresh_picker()

    # ── Picker ─────────────────────────────────────────────────────

    def _refresh_picker(self) -> None:
        self._all_tools = repo.get_all_tools()
        self._filtered_tools = list(self._all_tools)
        self._populate_picker()

    def _on_search(self, query: str, category: str) -> None:
        cat_enum = ToolCategory(category) if category else None
        self._filtered_tools = repo.search_tools(query=query, category=cat_enum)
        self._populate_picker()

    def _populate_picker(self) -> None:
        self._picker_table.setRowCount(len(self._filtered_tools))
        for i, tool in enumerate(self._filtered_tools):
            self._picker_table.setItem(i, 0, QTableWidgetItem(tool.name))
            self._picker_table.setItem(i, 1, QTableWidgetItem(pretty_category(tool.category)))
            self._picker_table.setItem(i, 2, QTableWidgetItem(tool.manufacturer or ""))
            self._picker_table.setItem(i, 3, QTableWidgetItem(tool.catalog_number or ""))

    # ── Add / Remove ───────────────────────────────────────────────

    def _add_selected(self) -> None:
        rows = set(idx.row() for idx in self._picker_table.selectionModel().selectedRows())
        if not rows:
            return
        qty = self._add_qty_spin.value()
        for row in rows:
            if 0 <= row < len(self._filtered_tools):
                tool = self._filtered_tools[row]
                # Check if already in BOM — add to existing quantity
                found = False
                for i, (tid, existing_qty) in enumerate(self._bom_items):
                    if tid == tool.tool_id:
                        self._bom_items[i] = (tid, existing_qty + qty)
                        found = True
                        break
                if not found:
                    self._bom_items.append((tool.tool_id, qty))
        self._rebuild_bom()

    def _remove_selected(self) -> None:
        rows = sorted(
            set(idx.row() for idx in self._bom_table.selectionModel().selectedRows()),
            reverse=True,
        )
        if not rows:
            return
        # Map BOM table rows back to bom_items via tool_id
        line_ids = [self._bom_lines[r].tool_id for r in rows if r < len(self._bom_lines)]
        # Remove from source selections any item whose exploded output matches
        # For simplicity, remove bom_items that produced these lines
        # Since explosions can create new lines, we remove by matching tool_id in bom_items
        self._bom_items = [
            (tid, q) for tid, q in self._bom_items if tid not in line_ids
        ]
        self._rebuild_bom()

    def _clear_bom(self) -> None:
        self._bom_items.clear()
        self._rebuild_bom()

    # ── BOM rebuild ────────────────────────────────────────────────

    def _rebuild_bom(self) -> None:
        self._bom_lines = build_bom(self._bom_items)
        self._populate_bom_table()

    def _populate_bom_table(self) -> None:
        lines = self._bom_lines
        self._bom_table.setRowCount(len(lines))
        for i, ln in enumerate(lines):
            qty_item = QTableWidgetItem(str(ln.quantity))
            qty_item.setTextAlignment(Qt.AlignCenter)
            self._bom_table.setItem(i, 0, qty_item)
            self._bom_table.setItem(i, 1, QTableWidgetItem(ln.name))
            self._bom_table.setItem(i, 2, QTableWidgetItem(ln.category))
            self._bom_table.setItem(i, 3, QTableWidgetItem(ln.manufacturer))
            self._bom_table.setItem(i, 4, QTableWidgetItem(ln.catalog_number))
            self._bom_table.setItem(i, 5, QTableWidgetItem(ln.notes))

        total = sum(ln.quantity for ln in lines)
        self._summary_label.setText(
            f"{len(lines)} line items  •  {total} total pieces"
            if lines else "No items in BOM"
        )

    # ── Export actions ─────────────────────────────────────────────

    def _copy_to_clipboard(self) -> None:
        if not self._bom_lines:
            QMessageBox.information(self, "Empty BOM", "Add tools to the BOM first.")
            return
        text = bom_to_text(self._bom_lines)
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Copied", "BOM copied to clipboard — paste into email.")

    def _export_pdf(self) -> None:
        if not self._bom_lines:
            QMessageBox.information(self, "Empty BOM", "Add tools to the BOM first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save BOM PDF", str(Path.home() / "Downloads" / "toolsnap_bom.pdf"),
            "PDF Files (*.pdf)",
        )
        if not path:
            return

        try:
            from utils.bom_export import export_pdf
            export_pdf(self._bom_lines, path)
            reply = QMessageBox.question(
                self, "PDF Saved",
                f"BOM saved to:\n{path}\n\nOpen it now?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                os.startfile(path)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to generate PDF:\n{e}")

    # ── Public refresh ─────────────────────────────────────────────

    def refresh(self) -> None:
        self._refresh_picker()

    def add_tool(self, tool_id: str, quantity: int = 1) -> None:
        """Add a tool to the BOM from an external signal (e.g. detail panel)."""
        for i, (tid, existing_qty) in enumerate(self._bom_items):
            if tid == tool_id:
                self._bom_items[i] = (tid, existing_qty + quantity)
                self._rebuild_bom()
                return
        self._bom_items.append((tool_id, quantity))
        self._rebuild_bom()
