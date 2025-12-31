import logging
import sys

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="data/logs/app.log",
)


def main():
    app = QApplication(sys.argv)
    # app.setStyle("Fusion") # Good baseline for custom styling
    app.setStyle("Windows")

    from database.connection import db_manager
    from config import DATABASE_CONFIGS
    db_manager.connect(DATABASE_CONFIGS['sqlite'])

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
