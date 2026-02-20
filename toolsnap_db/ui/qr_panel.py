"""QR label panel — generate and preview location QR codes."""

from pathlib import Path
from io import BytesIO

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSpinBox, QFileDialog, QMessageBox, QGroupBox, QCheckBox,
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt

from core.qr import generate_qr_image, save_qr_image
from config import get as cfg_get


class QrPanel(QWidget):
    """Panel for generating QR code location labels."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Input group
        input_group = QGroupBox("Label Settings")
        input_layout = QVBoxLayout(input_group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Location ID:"))
        self._location_input = QLineEdit()
        self._location_input.setPlaceholderText("e.g. CAB-03:DWR-07")
        self._location_input.returnPressed.connect(self._on_generate)
        row1.addWidget(self._location_input, stretch=1)
        input_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Label Size (mm):"))
        self._size_spin = QSpinBox()
        self._size_spin.setRange(15, 100)
        self._size_spin.setValue(cfg_get("qr_label_size_mm", 30))
        row2.addWidget(self._size_spin)
        row2.addSpacing(20)
        self._text_check = QCheckBox("Include text below QR")
        self._text_check.setChecked(True)
        row2.addWidget(self._text_check)
        row2.addStretch()
        input_layout.addLayout(row2)

        layout.addWidget(input_group)

        # Buttons
        btn_row = QHBoxLayout()
        gen_btn = QPushButton("Generate Preview")
        gen_btn.clicked.connect(self._on_generate)
        save_btn = QPushButton("Save as PNG")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(gen_btn)
        btn_row.addWidget(save_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Preview
        self._preview_label = QLabel("Enter a location ID and click Generate")
        self._preview_label.setAlignment(Qt.AlignCenter)
        self._preview_label.setMinimumHeight(300)
        self._preview_label.setStyleSheet("border: 1px solid #ccc; background: white;")
        layout.addWidget(self._preview_label, stretch=1)

        # Info
        prefix = cfg_get("qr_label_prefix", "TS")
        info = QLabel(f"QR codes encode: {prefix}:<location_id>")
        info.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info)

    def _on_generate(self) -> None:
        location = self._location_input.text().strip()
        if not location:
            return

        try:
            pil_img = generate_qr_image(
                location,
                size_mm=self._size_spin.value(),
                include_text=self._text_check.isChecked(),
            )
            # Convert PIL Image to QPixmap
            buf = BytesIO()
            pil_img.save(buf, "PNG")
            buf.seek(0)
            qimg = QImage()
            qimg.loadFromData(buf.read())
            pixmap = QPixmap.fromImage(qimg)

            # Scale to fit preview area
            scaled = pixmap.scaled(
                self._preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self._preview_label.setPixmap(scaled)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate QR code: {e}")

    def _on_save(self) -> None:
        location = self._location_input.text().strip()
        if not location:
            QMessageBox.information(self, "No Location", "Enter a location ID first.")
            return

        safe_name = location.replace(":", "-").replace("/", "-").replace("\\", "-")
        default_name = f"QR_{safe_name}.png"
        path, _ = QFileDialog.getSaveFileName(self, "Save QR Label", default_name, "PNG (*.png)")
        if path:
            try:
                save_qr_image(
                    location,
                    Path(path),
                    size_mm=self._size_spin.value(),
                    include_text=self._text_check.isChecked(),
                )
                QMessageBox.information(self, "Saved", f"QR label saved to {path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save: {e}")
