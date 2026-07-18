"""ToolSnap PC Database — entry point."""

import sys
from pathlib import Path

# Add project root to path so imports resolve
_root = Path(__file__).parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from PySide6.QtWidgets import QApplication

from config import load as load_config, get_db_path
from core.database import init as init_db, close as close_db
from ui.app import MainWindow


def main() -> None:
    load_config()
    init_db(get_db_path())

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    exit_code = app.exec()
    close_db()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
