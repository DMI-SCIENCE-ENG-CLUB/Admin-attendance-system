from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFrame, QStackedWidget, QLabel, QApplication
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
import sys
import os

from ui.pages import (
    DashboardPage, EmployeesPage, AttendancePage, 
    DevicesPage, DatabasesPage, ReportsPage, SettingsPage
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("E-Time Tracker Pro")
        self.setMinimumSize(1280, 800)
        
        # Load Stylesheet
        self.load_stylesheet()
        
        # Main Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Sidebar
        self.create_sidebar()
        
        # Content Area
        self.content_area = QStackedWidget()
        self.content_area.setObjectName("Content")
        self.main_layout.addWidget(self.content_area)
        
        # Initialize Pages
        self.dashboard_page = DashboardPage()
        self.employees_page = EmployeesPage()
        self.attendance_page = AttendancePage()
        self.devices_page = DevicesPage()
        self.databases_page = DatabasesPage()
        self.reports_page = ReportsPage()
        self.settings_page = SettingsPage()
        
        # Page indices:
        self.content_area.addWidget(self.dashboard_page)   # 0
        self.content_area.addWidget(self.employees_page)   # 1
        self.content_area.addWidget(self.attendance_page)  # 2
        self.content_area.addWidget(self.devices_page)     # 3
        self.content_area.addWidget(self.databases_page)   # 4
        self.content_area.addWidget(self.reports_page)     # 5
        self.content_area.addWidget(self.settings_page)    # 6
        
        # Default Selection
        self.btn_dashboard.setChecked(True)

    def load_stylesheet(self):
        try:
            with open("ui/resources/styles.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Stylesheet not found")

    def create_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(10)
        
        # Logo / Title
        app_title = QLabel("E-Tracker")
        app_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #89b4fa; padding: 10px;")
        layout.addWidget(app_title)
        
        # Navigation Buttons
        self.btn_dashboard = self.create_nav_button("Dashboard", 0)
        self.btn_employees = self.create_nav_button("Employees", 1)
        self.btn_attendance = self.create_nav_button("Attendance", 2)
        self.btn_devices = self.create_nav_button("Devices", 3)
        self.btn_databases = self.create_nav_button("Databases", 4)
        self.btn_reports = self.create_nav_button("Reports", 5)
        self.btn_settings = self.create_nav_button("Settings", 6)
        
        layout.addWidget(self.btn_dashboard)
        layout.addWidget(self.btn_employees)
        layout.addWidget(self.btn_attendance)
        layout.addWidget(self.btn_devices)
        layout.addWidget(self.btn_databases)
        layout.addWidget(self.btn_reports)
        
        layout.addStretch()
        layout.addWidget(self.btn_settings)

        self.main_layout.addWidget(self.sidebar)

    def create_nav_button(self, text, index):
        btn = QPushButton(text)
        btn.setObjectName("NavButton")
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.clicked.connect(lambda: self.switch_page(index))
        return btn

    def switch_page(self, index):
        if index < self.content_area.count():
            page = self.content_area.widget(index)
            self.content_area.setCurrentIndex(index)
            
            # Refresh data on the page if it has a loading method
            if hasattr(page, "load_dashboard_data"):
                page.load_dashboard_data()
            elif hasattr(page, "load_employees"):
                page.load_employees()
            elif hasattr(page, "load_from_db"):
                page.load_from_db()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
