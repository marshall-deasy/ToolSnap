"""Import panel — configure import directory, scan, and show results."""

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QTextEdit, QGroupBox, QMessageBox,
)
from PySide6.QtCore import Qt, Signal

from config import get as cfg_get, set_value as cfg_set, save as cfg_save
from config.settings import DEFAULT_IMPORT_DIR
from core.importer import scan_and_import, ScanResult


class ImportPanel(QWidget):
    """Panel for configuring and triggering manifest imports."""

    import_completed = Signal()  # emitted after successful import so other panels can refresh

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Directory config
        dir_group = QGroupBox("Import Directory")
        dir_layout = QVBoxLayout(dir_group)

        dir_row = QHBoxLayout()
        self._dir_input = QLineEdit(cfg_get("import_directory", "") or str(DEFAULT_IMPORT_DIR))
        self._dir_input.setPlaceholderText("Path to phone sync folder...")
        dir_row.addWidget(self._dir_input, stretch=1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse)
        dir_row.addWidget(browse_btn)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._on_save_dir)
        dir_row.addWidget(save_btn)
        dir_layout.addLayout(dir_row)

        self._dir_status = QLabel()
        self._dir_status.setStyleSheet("color: #666;")
        dir_layout.addWidget(self._dir_status)

        layout.addWidget(dir_group)

        # Scan controls
        scan_row = QHBoxLayout()
        self._scan_btn = QPushButton("Scan & Import")
        self._scan_btn.setStyleSheet("font-weight: bold; padding: 8px 24px;")
        self._scan_btn.clicked.connect(self._on_scan)
        scan_row.addWidget(self._scan_btn)
        scan_row.addStretch()
        layout.addLayout(scan_row)

        # Log output
        log_group = QGroupBox("Import Log")
        log_layout = QVBoxLayout(log_group)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        log_layout.addWidget(self._log)
        layout.addWidget(log_group, stretch=1)

        self._update_dir_status()

    def _on_browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Import Directory")
        if path:
            self._dir_input.setText(path)

    def _on_save_dir(self) -> None:
        path = self._dir_input.text().strip()
        cfg_set("import_directory", path)
        cfg_save()
        self._update_dir_status()
        self._log_msg(f"Import directory saved: {path}")

    def _update_dir_status(self) -> None:
        path = self._dir_input.text().strip()
        if not path:
            self._dir_status.setText("No import directory configured.")
            self._dir_status.setStyleSheet("color: #c00;")
            return
        p = Path(path)
        if p.is_dir():
            count = sum(1 for d in p.iterdir() if d.is_dir())
            self._dir_status.setText(f"✓ Directory exists — {count} subdirectories found")
            self._dir_status.setStyleSheet("color: #080;")
        else:
            self._dir_status.setText("✗ Directory does not exist")
            self._dir_status.setStyleSheet("color: #c00;")

    def _on_scan(self) -> None:
        path = self._dir_input.text().strip()
        if not path:
            QMessageBox.warning(self, "No Directory", "Set an import directory first.")
            return

        p = Path(path)
        if not p.is_dir():
            QMessageBox.warning(self, "Invalid Directory", f"Directory does not exist:\n{path}")
            return

        self._log_msg(f"Scanning {path}...")
        self._scan_btn.setEnabled(False)

        try:
            result = scan_and_import(p)
            self._show_results(result)
            self.import_completed.emit()
        except Exception as e:
            self._log_msg(f"ERROR: {e}")
        finally:
            self._scan_btn.setEnabled(True)

    def _show_results(self, result: ScanResult) -> None:
        self._log_msg(f"Scanned {result.directories_scanned} directories, found {result.manifests_found} manifests")

        for imp in result.imports:
            if imp.skipped:
                self._log_msg(f"  SKIP  {imp.directory} (already imported, unchanged)")
            elif imp.error:
                self._log_msg(f"  ERROR {imp.directory}: {imp.error}")
            else:
                self._log_msg(
                    f"  OK    {imp.directory} (V{imp.version}) — "
                    f"+{imp.tools_added} new, {imp.tools_updated} updated, "
                    f"{imp.tools_deduplicated} deduped, {imp.components_added} components, "
                    f"{imp.compatibility_derived} compat links"
                )

        self._log_msg(
            f"Totals: {result.total_tools_added} tools added, "
            f"{result.total_tools_updated} updated, {result.total_errors} errors"
        )
        self._log_msg("—" * 60)

    def _log_msg(self, msg: str) -> None:
        self._log.append(msg)
