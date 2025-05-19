# main.py
import sys
from PyQt6.QtWidgets import QApplication
# from app.main_window_qt import AppMainWindowQt # We'll create this new file
# For now, let's assume AppMainWindowQt will be in main_window.py
from app.main_window_qt import AppMainWindowQt # Or whatever you rename your Qt main window class to

if __name__ == "__main__":
    # QApplication instance is required for any Qt GUI application
    app = QApplication(sys.argv)

    # Create and show your main window
    main_window_qt = AppMainWindowQt()
    main_window_qt.show()

    # Start the Qt event loop
    sys.exit(app.exec())