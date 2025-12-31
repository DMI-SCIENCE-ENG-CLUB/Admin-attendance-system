from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class LoginWindow(QWidget):
    login_successful = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - DMI Admin Attendance System")
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f4f8;
                font-family: 'Segoe UI', sans-serif;
                color: #333333;
            }
            QFrame#LoginCard {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #d1d9e6;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #00509e;
            }
            QPushButton {
                background-color: #00509e;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #003d7a;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("LoginCard")
        card.setFixedSize(320, 380)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 40, 30, 40)
        card_layout.setSpacing(20)

        # Logo/Title
        title_lbl = QLabel("DMI Admin")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #00509e;")
        card_layout.addWidget(title_lbl)
        
        subtitle_lbl = QLabel("Attendance System")
        subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_lbl.setStyleSheet("font-size: 16px; color: #666;")
        card_layout.addWidget(subtitle_lbl)

        card_layout.addSpacing(20)

        # Inputs
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        card_layout.addWidget(self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.returnPressed.connect(self.check_login)
        card_layout.addWidget(self.pass_input)

        # Button
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.check_login)
        card_layout.addWidget(login_btn)

        card_layout.addStretch()

        layout.addWidget(card)

    def check_login(self):
        username = self.user_input.text()
        password = self.pass_input.text()

        if username == "admin" and password == "admin123":
            self.login_successful.emit()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
