"""
FolderSync - Folder Comparison and Synchronization Tool
Main entry point.
"""

import sys
from PySide6.QtWidgets import QApplication
from gui import FolderSyncWindow


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Consistent cross-platform look
    
    window = FolderSyncWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
