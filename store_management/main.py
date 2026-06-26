import sys
import os
from pathlib import Path

# Make sure the store_management package is importable
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from config import APP_NAME, APP_VERSION
from app.database.schema import init_schema
from app.views.login_dialog import LoginDialog
from app.views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    import platform
    font_family = "Segoe UI" if platform.system() == "Windows" else (
        "SF Pro Display" if platform.system() == "Darwin" else "Ubuntu"
    )
    font = QFont(font_family, 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    # Init DB
    try:
        init_schema()
    except Exception as e:
        QMessageBox.critical(None, "Erreur base de données", str(e))
        sys.exit(1)

    # Login
    login = LoginDialog()
    if login.exec() != LoginDialog.Accepted:
        sys.exit(0)

    # Main window
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
