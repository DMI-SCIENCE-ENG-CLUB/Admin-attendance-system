import logging
import os
import sys
sys.path.insert(0, os.path.abspath("./pyzk"))

# Import ZK correctly; fall back to legacy `zk` if present
try:
    from zk import ZK, const
    zk = ZK  # keep a `zk` name for backward compatibility
except Exception:
    from zk import zk, const

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow

# Ensure log directory exists before configuring logging
log_file = "data/logs/app.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=log_file,
)


def main():
    app = QApplication(sys.argv)
    # app.setStyle("Fusion") # Good baseline for custom styling
    app.setStyle("Windows")

    from database.connection import db_manager
    from config import DATABASE_CONFIGS
    db_manager.connect(DATABASE_CONFIGS['sqlite'])

    # REBUILD DATABASE: Drop and recreate all tables
    try:
        from database.connection import Base, engine
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        logging.info("Database schema dropped and recreated.")
    except Exception as e:
        logging.exception("Error rebuilding database: %s", e)

    # Ensure a default admin exists (username: admin / password: admin)
    try:
        from database.models import ensure_default_admin, AdminUser
        ensure_default_admin(db_manager.get_session())
        # DEBUG: List all admin users and their hashes
        session = db_manager.get_session()()
        admins = session.query(AdminUser).all()
        for admin in admins:
            logging.info(f"AdminUser: username={admin.username!r}, password_hash={admin.password_hash!r}")
        session.close()
    except Exception as e:
        logging.exception("Error ensuring default admin or listing admins: %s", e)

    # Show login first; open main app only after successful login
    from ui.login_window import LoginWindow
    login = LoginWindow()
    main_win = {'instance': None}

    def open_main():
        if main_win['instance'] is None:
            main_win['instance'] = MainWindow()
        main_win['instance'].show()
        login.close()

    login.login_successful.connect(open_main)
    login.show()

    # ...main window is opened via login_successful handler...

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
