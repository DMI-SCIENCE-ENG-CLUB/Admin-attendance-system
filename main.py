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

    from ui.login_window import LoginWindow
    
    login = LoginWindow()
    window = MainWindow()
    
    def show_main():
        login.close()
        window.show()
    
    login.login_successful.connect(show_main)
    login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
