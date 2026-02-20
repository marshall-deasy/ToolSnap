"""Main application window — tab container for all panels."""

from PySide6.QtWidgets import QMainWindow, QTabWidget
from PySide6.QtCore import Qt

from config import get as cfg_get
from ui.search_panel import SearchPanel
from ui.assembly_panel import AssemblyPanel
from ui.compatibility_panel import CompatibilityPanel
from ui.inventory_panel import InventoryPanel
from ui.import_panel import ImportPanel
from ui.qr_panel import QrPanel
from ui.bom_panel import BomPanel


class MainWindow(QMainWindow):
    """Top-level window with tabbed navigation."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ToolSnap — Tooling Database")
        self.resize(cfg_get("window_width", 1400), cfg_get("window_height", 900))

        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        # Create panels
        self._search = SearchPanel()
        self._assembly = AssemblyPanel()
        self._compatibility = CompatibilityPanel()
        self._inventory = InventoryPanel()
        self._bom = BomPanel()
        self._import = ImportPanel()
        self._qr = QrPanel()

        # Add tabs
        self._tabs.addTab(self._search, "Tools")
        self._tabs.addTab(self._assembly, "Assemblies")
        self._tabs.addTab(self._compatibility, "Compatibility")
        self._tabs.addTab(self._inventory, "Inventory")
        self._tabs.addTab(self._bom, "BOM")
        self._tabs.addTab(self._import, "Import")
        self._tabs.addTab(self._qr, "QR Labels")

        # Wire cross-panel signals
        self._import.import_completed.connect(self._on_import_completed)
        self._tabs.currentChanged.connect(self._on_tab_changed)
        # BOM: wire detail panels → BOM panel
        self._search._detail.add_to_bom.connect(self._on_add_to_bom)

    def _on_import_completed(self) -> None:
        """Refresh relevant panels after an import."""
        self._search.refresh()
        self._assembly.refresh_assembly_list()
        self._compatibility.refresh()

    def _on_tab_changed(self, index: int) -> None:
        """Refresh the active tab when switching to it."""
        widget = self._tabs.widget(index)
        if widget is self._search:
            self._search.refresh()
        elif widget is self._assembly:
            self._assembly.refresh_assembly_list()
        elif widget is self._compatibility:
            self._compatibility.refresh()
        elif widget is self._bom:
            self._bom.refresh()

    def _on_add_to_bom(self, tool_id: str, quantity: int) -> None:
        """Handle add-to-BOM from any detail panel."""
        from core import repo
        tool = repo.get_tool(tool_id)
        name = tool.name if tool else tool_id
        self._bom.add_tool(tool_id, quantity)
        self.statusBar().showMessage(
            f"Added {quantity}× {name} to BOM", 3000
        )
