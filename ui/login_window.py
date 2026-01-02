from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class LoginWindow(QWidget):
    login_successful = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - DMI Admin Attendance System")
        # Prefer a responsive minimum size so centering works well on different screens
        self.setMinimumSize(400, 480)

        # For the login window we want a minimal white background to avoid contrast issues
        # Keep form controls styled for readability but ensure main background is pure white
        self.setStyleSheet("""
            QWidget { background-color: #ffffff; font-family: 'Segoe UI', sans-serif; color: #222222; }
            QFrame#LoginCard { background-color: #ffffff; border-radius: 10px; border: 1px solid #e6eef8; }
            QLineEdit { background-color: #ffffff; color: #222222; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px; font-size: 14px; }
            QLineEdit:focus { border: 1px solid #007acc; }
            QLineEdit::placeholder { color: #6b7280; }
            QPushButton { background-color: #007acc; color: #ffffff; border: none; border-radius: 6px; padding: 10px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #006bb3; }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Simple container (no framed "modal") so fields sit directly on white background
        container = QWidget()
        container.setFixedWidth(380)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(24, 32, 24, 24)
        container_layout.setSpacing(12)

        # Logo/Title (centered)
        title_lbl = QLabel("DMI Admin")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #007acc;")
        container_layout.addWidget(title_lbl)

        subtitle_lbl = QLabel("Attendance System")
        subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_lbl.setStyleSheet("font-size: 14px; color: #475569;")
        container_layout.addWidget(subtitle_lbl)

        container_layout.addSpacing(10)

        # Inputs (directly on the white background)
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        container_layout.addWidget(self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.returnPressed.connect(self.check_login)
        container_layout.addWidget(self.pass_input)

        # Button
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.check_login)
        container_layout.addWidget(login_btn)

        container_layout.addStretch()

        layout.addWidget(container)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        version_lbl = QLabel("v1.0.2")
        version_lbl.setStyleSheet("color: #999; font-size: 11px; margin: 10px;")
        footer_layout.addWidget(version_lbl)
        layout.addLayout(footer_layout)

    def center(self):
        try:
            from PyQt6.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
            if screen is None:
                return
            screen_geo = screen.availableGeometry()
            x = screen_geo.x() + (screen_geo.width() - self.width()) // 2
            y = screen_geo.y() + (screen_geo.height() - self.height()) // 2
            self.move(x, y)
        except Exception:
            pass

    def showEvent(self, event):
        # Ensure window is centered when shown
        self.center()
        super().showEvent(event)

    def check_login(self):
        from database.connection import db_manager
        from database.models import AdminUser
        import logging, hmac, hashlib
        logger = logging.getLogger(__name__)

        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Validation", "Please enter username and password.")
            return

        try:
            session_factory = db_manager.get_session()
            session = session_factory()

            user = session.query(AdminUser).filter_by(username=username).first()
            session.close()

            logger.debug("DB lookup result for %r: %s", username, "FOUND" if user else "NOT FOUND")

            if not user:
                logger.warning("Login failed - user not found: %r", username)
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
                return

            stored = (getattr(user, "password_hash", "") or "")

            def is_raw_sha256(s):
                s = s.lower()
                return len(s) == 64 and all(c in "0123456789abcdef" for c in s)

            ok = False
            # 1. Try raw SHA256 hex match (most common in this app)
            if is_raw_sha256(stored):
                provided_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
                ok = hmac.compare_digest(stored.lower(), provided_hash)

            # 2. Try werkzeug (pbkdf2/bcrypt) if not already matched
            if not ok:
                try:
                    from werkzeug.security import check_password_hash as _check_pw
                    ok = bool(_check_pw(stored, password))
                except Exception:
                    pass

            # 3. Last resort: plain-text comparison (for legacy/unhashed entries)
            if not ok:
                ok = hmac.compare_digest(stored, password)

            if ok:
                logger.info("Login successful for %r", username)
                self.login_successful.emit()
            else:
                logger.warning("Login failed for %r", username)
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")

        except Exception as e:
            logger.exception("Error during login attempt: %s", e)
            QMessageBox.critical(self, "Connection Error", f"Database connection failed: {str(e)}")

    # Settings removed from Login per request
    # def open_settings(self): ...




