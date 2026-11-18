"""Point d'entrée de GESCO."""
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from gesco.database import initialize_database
from gesco.window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("GESCO")
    try:
        initialize_database()
        window = MainWindow()
        window.show()
        return app.exec()
    except Exception as exc:
        QMessageBox.critical(None, "Erreur de démarrage", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
