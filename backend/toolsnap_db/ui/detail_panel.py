"""
Detail panel — shows all fields for the selected tool.

Displays: name, category, manufacturer, catalog#, description,
all attributes, photos (from session folder), and component links.
"""

import json
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QGridLayout,
    QSizePolicy, QHBoxLayout,
)

from config.settings import DETAIL_PANEL_WIDTH
from core.database import Database

# Friendly labels for attribute keys
_ATTR_LABELS = {
    "cutting_diameter": "Cutting Diameter",
    "shank_diameter": "Shank Diameter",
    "flutes": "Flutes",
    "flute_length": "Flute Length",
    "helix_angle": "Helix Angle",
    "coating": "Coating",
    "material": "Material",
    "overall_length": "Overall Length",
    "coolant_through": "Coolant Through",
    "point_angle": "Point Angle",
    "thread_pitch": "Thread Pitch",
    "thread_form": "Thread Form",
    "shank_type": "Shank Type",
    "pocket_size": "Pocket Size",
    "projection": "Projection",
    "shank_size": "Shank Size",
    "hand": "Hand",
    "thread_type": "Thread Type",
    "groove_width": "Groove Width",
    "max_depth": "Max Depth",
    "iso_designation": "ISO Designation",
    "insert_shape": "Insert Shape",
    "insert_size": "Insert Size",
    "thickness": "Thickness",
    "nose_radius": "Nose Radius",
    "grade": "Grade",
    "workpiece_material": "Workpiece Material",
    "chipbreaker": "Chipbreaker",
    "rake": "Rake",
    "size": "Size",
    "drive_type": "Drive Type",
    "torque_spec": "Torque Spec",
    "shim_type": "Shim Type",
    "clamp_type": "Clamp Type",
    "wedge_type": "Wedge Type",
    "bore_size": "Bore Size",
    "gauge_length": "Gauge Length",
    "collet_system": "Collet System",
    "thread_size": "Thread Size",
    "description_custom": "Description",
}

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


class DetailPanel(QWidget):
    """Right-side panel showing selected tool details."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self.setFixedWidth(DETAIL_PANEL_WIDTH)
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.NoFrame)

        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(12)
        self._layout.setAlignment(Qt.AlignTop)

        self._scroll.setWidget(self._content)
        outer.addWidget(self._scroll)

        # Placeholder
        self._placeholder = QLabel("Select a tool to view details")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet("color: #666; font-size: 14px;")
        self._layout.addWidget(self._placeholder)

    def show_tool(self, tool_id: str):
        """Load and display a tool by ID."""
        tool = self._db.get_tool(tool_id)
        if not tool:
            return

        self._clear()

        # --- Header: name ---
        name_label = QLabel(tool.get("name", "Unnamed"))
        name_label.setWordWrap(True)
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        name_label.setFont(name_font)
        self._layout.addWidget(name_label)

        # --- Category + type badge ---
        category = tool.get("category", "OTHER")
        cat_display = _CATEGORY_DISPLAY.get(category, category)
        tool_type = tool.get("type", "standalone")
        badge_text = f"{cat_display}  •  {tool_type}"
        badge = QLabel(badge_text)
        badge.setStyleSheet(
            "color: #aaa; font-size: 11px; padding: 2px 0;"
        )
        self._layout.addWidget(badge)

        self._add_separator()

        # --- Core fields ---
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        grid.setSpacing(4)
        row = 0

        core_fields = [
            ("Manufacturer", tool.get("manufacturer")),
            ("Catalog #", tool.get("catalogNumber")),
            ("Description", tool.get("description")),
            ("Unit System", tool.get("unitSystem")),
            ("Status", tool.get("status")),
        ]
        for label, value in core_fields:
            if value:
                row = self._add_field_row(grid, row, label, value)

        if row > 0:
            self._layout.addLayout(grid)
            self._add_separator()

        # --- Category-specific attributes ---
        attrs = tool.get("attributes", {})
        if attrs:
            attrs_label = QLabel("Attributes")
            attrs_font = QFont()
            attrs_font.setPointSize(11)
            attrs_font.setBold(True)
            attrs_label.setFont(attrs_font)
            attrs_label.setStyleSheet("color: #ccc;")
            self._layout.addWidget(attrs_label)

            attr_grid = QGridLayout()
            attr_grid.setColumnStretch(1, 1)
            attr_grid.setSpacing(4)
            arow = 0
            for key, val in attrs.items():
                display_key = _ATTR_LABELS.get(key, key.replace("_", " ").title())
                arow = self._add_field_row(attr_grid, arow, display_key, val)
            self._layout.addLayout(attr_grid)
            self._add_separator()

        # --- Tags ---
        tags = tool.get("tags", [])
        if tags:
            tags_label = QLabel("Tags")
            tags_font = QFont()
            tags_font.setBold(True)
            tags_label.setFont(tags_font)
            tags_label.setStyleSheet("color: #ccc; font-size: 11px;")
            self._layout.addWidget(tags_label)

            tag_row = QHBoxLayout()
            for tag in tags:
                chip = QLabel(tag)
                chip.setStyleSheet("""
                    background: #2a3a4a; color: #aad4ff;
                    padding: 2px 8px; border-radius: 4px; font-size: 11px;
                """)
                tag_row.addWidget(chip)
            tag_row.addStretch()
            self._layout.addLayout(tag_row)
            self._add_separator()

        # --- Photos ---
        photos = tool.get("photos", [])
        session_dir = tool.get("sessionDir")
        if photos and session_dir:
            photos_label = QLabel("Photos")
            photos_font = QFont()
            photos_font.setBold(True)
            photos_label.setFont(photos_font)
            photos_label.setStyleSheet("color: #ccc; font-size: 11px;")
            self._layout.addWidget(photos_label)

            for photo_name in photos:
                photo_path = Path(session_dir) / photo_name
                if photo_path.exists():
                    pixmap = QPixmap(str(photo_path))
                    if not pixmap.isNull():
                        scaled = pixmap.scaledToWidth(
                            DETAIL_PANEL_WIDTH - 40,
                            Qt.SmoothTransformation
                        )
                        img_label = QLabel()
                        img_label.setPixmap(scaled)
                        img_label.setStyleSheet(
                            "border: 1px solid #333; border-radius: 4px;"
                        )
                        self._layout.addWidget(img_label)
                else:
                    missing = QLabel(f"📷 {photo_name} (not found)")
                    missing.setStyleSheet("color: #886; font-size: 11px;")
                    self._layout.addWidget(missing)

            self._add_separator()

        # --- Component links ---
        children = self._db.get_children(tool_id)
        if children:
            comp_label = QLabel("Components")
            comp_font = QFont()
            comp_font.setBold(True)
            comp_label.setFont(comp_font)
            comp_label.setStyleSheet("color: #ccc; font-size: 11px;")
            self._layout.addWidget(comp_label)

            for child in children:
                role = child.get("role", "")
                name = child.get("childName", "")
                cat = _CATEGORY_DISPLAY.get(
                    child.get("childCategory", ""), ""
                )
                qty = child.get("quantity", 1)
                text = f"{role}: {name}"
                if qty > 1:
                    text += f" (×{qty})"
                cl = QLabel(text)
                cl.setWordWrap(True)
                cl.setStyleSheet("color: #aaa; font-size: 11px; padding: 1px 0;")
                self._layout.addWidget(cl)

        parents = self._db.get_parents(tool_id)
        if parents:
            parent_label = QLabel("Used In")
            parent_font = QFont()
            parent_font.setBold(True)
            parent_label.setFont(parent_font)
            parent_label.setStyleSheet("color: #ccc; font-size: 11px;")
            self._layout.addWidget(parent_label)

            for p in parents:
                text = f"{p.get('parentName', '')} ({p.get('role', '')})"
                pl = QLabel(text)
                pl.setWordWrap(True)
                pl.setStyleSheet("color: #aaa; font-size: 11px; padding: 1px 0;")
                self._layout.addWidget(pl)

        # --- Notes ---
        notes = tool.get("notes")
        if notes:
            self._add_separator()
            notes_label = QLabel("Notes")
            notes_font = QFont()
            notes_font.setBold(True)
            notes_label.setFont(notes_font)
            notes_label.setStyleSheet("color: #ccc; font-size: 11px;")
            self._layout.addWidget(notes_label)
            notes_text = QLabel(notes)
            notes_text.setWordWrap(True)
            notes_text.setStyleSheet("color: #aaa; font-size: 12px;")
            self._layout.addWidget(notes_text)

        # Bottom spacer
        self._layout.addStretch()

    def clear(self):
        """Reset to placeholder state."""
        self._clear()
        self._placeholder = QLabel("Select a tool to view details")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet("color: #666; font-size: 14px;")
        self._layout.addWidget(self._placeholder)

    def _clear(self):
        """Remove all widgets from the content layout."""
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            sub = item.layout()
            if sub:
                self._clear_layout(sub)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            sub = item.layout()
            if sub:
                self._clear_layout(sub)

    def _add_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #333;")
        self._layout.addWidget(sep)

    @staticmethod
    def _add_field_row(
        grid: QGridLayout, row: int, label: str, value: str
    ) -> int:
        lbl = QLabel(f"{label}:")
        lbl.setStyleSheet("color: #888; font-size: 12px;")
        lbl.setAlignment(Qt.AlignRight | Qt.AlignTop)

        val = QLabel(str(value))
        val.setWordWrap(True)
        val.setStyleSheet("color: #ddd; font-size: 12px;")
        val.setTextInteractionFlags(Qt.TextSelectableByMouse)

        grid.addWidget(lbl, row, 0)
        grid.addWidget(val, row, 1)
        return row + 1
