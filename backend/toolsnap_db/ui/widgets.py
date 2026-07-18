"""Shared UI widgets used across multiple panels."""

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QScrollArea,
    QFrame, QSizePolicy, QLineEdit, QComboBox, QPushButton,
    QDialog, QApplication,
)
from PySide6.QtGui import QPixmap, QImage, QCursor
from PySide6.QtCore import Qt, Signal


class _ClickableThumb(QLabel):
    """A thumbnail label that opens a larger popup on click."""

    def __init__(self, pixmap: QPixmap, full_path: str, parent=None):
        super().__init__(parent)
        self._full_pixmap = pixmap
        self._full_path = full_path
        thumb = pixmap.scaledToHeight(100, Qt.SmoothTransformation)
        self.setPixmap(thumb)
        self.setToolTip(Path(full_path).name)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(
            "border: 1px solid #ccc; border-radius: 4px; padding: 2px;"
            "background: #fafafa;"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._show_popup()

    def _show_popup(self):
        dlg = QDialog(self.window())
        dlg.setWindowTitle(Path(self._full_path).name)
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowMaximizeButtonHint)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel()
        lbl.setAlignment(Qt.AlignCenter)

        # Scale to fit screen, max 90% of screen size
        screen = QApplication.primaryScreen().availableGeometry()
        max_w = int(screen.width() * 0.9)
        max_h = int(screen.height() * 0.9)
        scaled = self._full_pixmap.scaled(
            max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        lbl.setPixmap(scaled)

        scroll = QScrollArea()
        scroll.setWidget(lbl)
        scroll.setWidgetResizable(False)
        scroll.setAlignment(Qt.AlignCenter)
        scroll.setFrameShape(QFrame.NoFrame)
        layout.addWidget(scroll)

        # Size dialog to image (capped at screen size)
        dlg.resize(
            min(scaled.width() + 20, max_w),
            min(scaled.height() + 20, max_h),
        )
        dlg.exec()


class PhotoViewer(QWidget):
    """Horizontally scrollable strip of tool photo thumbnails.
    Click any thumbnail to see the full-size image in a popup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(8)

        self._container = QWidget()
        self._container.setLayout(self._layout)

        scroll = QScrollArea()
        scroll.setWidget(self._container)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFixedHeight(120)
        scroll.setFrameShape(QFrame.NoFrame)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def set_photos(self, photo_paths: list[str]) -> None:
        """Display photos from the given file paths."""
        # Clear existing
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for path_str in photo_paths:
            p = Path(path_str)
            if not p.is_file():
                lbl = QLabel(f"[missing: {p.name}]")
                lbl.setStyleSheet("color: #888; font-style: italic;")
                self._layout.addWidget(lbl)
                continue

            pixmap = QPixmap(str(p))
            if pixmap.isNull():
                lbl = QLabel(f"[unreadable: {p.name}]")
                lbl.setStyleSheet("color: #888; font-style: italic;")
                self._layout.addWidget(lbl)
                continue

            thumb = _ClickableThumb(pixmap, str(p))
            self._layout.addWidget(thumb)

        self._layout.addStretch()


class TagDisplay(QWidget):
    """Horizontal flow of tag badges."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)

    def set_tags(self, tags: list[str]) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for tag in tags:
            lbl = QLabel(tag)
            lbl.setStyleSheet(
                "background-color: #e0e7ff; color: #3730a3; padding: 2px 8px; "
                "border-radius: 3px; font-size: 11px;"
            )
            self._layout.addWidget(lbl)

        self._layout.addStretch()


class SearchBar(QWidget):
    """Search input with category dropdown and search button."""

    search_triggered = Signal(str, str)  # (query_text, category_or_empty)

    def __init__(self, categories: list[str] | None = None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search tools...")
        self._search_input.returnPressed.connect(self._on_search)

        self._category_combo = QComboBox()
        self._category_combo.addItem("All Categories", "")
        if categories:
            for cat in categories:
                self._category_combo.addItem(cat.replace("_", " ").title(), cat)
        self._category_combo.setMinimumWidth(180)
        self._category_combo.currentIndexChanged.connect(self._on_search)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._on_search)

        layout.addWidget(self._search_input, stretch=1)
        layout.addWidget(self._category_combo)
        layout.addWidget(search_btn)

    def _on_search(self) -> None:
        query = self._search_input.text().strip()
        category = self._category_combo.currentData() or ""
        self.search_triggered.emit(query, category)

    def set_categories(self, categories: list[str]) -> None:
        """Update the category dropdown."""
        current = self._category_combo.currentData()
        self._category_combo.clear()
        self._category_combo.addItem("All Categories", "")
        for cat in categories:
            self._category_combo.addItem(cat.replace("_", " ").title(), cat)
        # Restore selection if still valid
        idx = self._category_combo.findData(current)
        if idx >= 0:
            self._category_combo.setCurrentIndex(idx)


class AttributeGrid(QWidget):
    """Two-column key/value display for tool attributes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)

    def set_attributes(self, attributes: dict[str, str], expected_keys: list[str] | None = None) -> None:
        """Display attributes. If expected_keys provided, show in that order."""
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        keys = expected_keys if expected_keys else sorted(attributes.keys())

        for key in keys:
            value = attributes.get(key)
            if value is None or value == "":
                continue
            row = QHBoxLayout()
            row.setSpacing(8)

            key_label = QLabel(key.replace("_", " ").title() + ":")
            key_label.setStyleSheet("font-weight: bold; color: #555; min-width: 140px;")
            key_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

            val_label = QLabel(str(value))
            val_label.setWordWrap(True)

            row.addWidget(key_label)
            row.addWidget(val_label, stretch=1)

            container = QWidget()
            container.setLayout(row)
            self._layout.addWidget(container)

        # Show any extra attributes not in expected_keys
        if expected_keys:
            extras = {k: v for k, v in attributes.items()
                      if k not in expected_keys and v is not None and v != ""}
            for key, value in sorted(extras.items()):
                row = QHBoxLayout()
                row.setSpacing(8)
                key_label = QLabel(key.replace("_", " ").title() + ":")
                key_label.setStyleSheet("font-weight: bold; color: #888; min-width: 140px;")
                key_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
                val_label = QLabel(str(value))
                val_label.setWordWrap(True)
                row.addWidget(key_label)
                row.addWidget(val_label, stretch=1)
                container = QWidget()
                container.setLayout(row)
                self._layout.addWidget(container)
