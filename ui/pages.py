from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QSizePolicy, QLineEdit, QApplication, QDialog, QComboBox, QDateEdit, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QCheckBox
)
from PyQt6.QtCore import Qt, QSize, QDate
from ui.widgets.attendance_table import AttendanceTable
import json
import os

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        header = QLabel("Dashboard")
        header.setObjectName("HeaderTitle")
        layout.addWidget(header)

        # Stats Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        self.total_emp_card = self.create_stat_card("Total Employees", "124", "")
        self.present_card = self.create_stat_card("Present Today", "98", "")
        self.late_card = self.create_stat_card("Late Arrivals", "12", "")
        self.absent_card = self.create_stat_card("Absent", "14", "")

        stats_layout.addWidget(self.total_emp_card)
        stats_layout.addWidget(self.present_card)
        stats_layout.addWidget(self.late_card)
        stats_layout.addWidget(self.absent_card)
        
        layout.addLayout(stats_layout)

        # Recent Activity Section
        activity_frame = QFrame()
        activity_frame.setObjectName("Card")
        activity_layout = QVBoxLayout(activity_frame)
        
        lbl = QLabel("Recent Activity")
        lbl.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #003366;")
        activity_layout.addWidget(lbl)
        
        # Recent Attendance Table (Preview)
        self.table = AttendanceTable()
        self.load_dashboard_data()
        
        activity_layout.addWidget(self.table)
        
        layout.addWidget(activity_frame)
        layout.addStretch()

    def load_dashboard_data(self):
        from database.connection import db_manager
        from database.models import AttendanceRecord, Employee, Leave
        from datetime import datetime
        
        try:
            session_factory = db_manager.get_session()
            session = session_factory()
            
            # Update Stat Cards
            total_emp = session.query(Employee).count()
            self.total_emp_card.findChild(QLabel, "StatValue").setText(str(total_emp))
            
            # Count present today (at least one 'in' record)
            today = datetime.now().date()
            present_today = session.query(AttendanceRecord.employee_id).filter(
                AttendanceRecord.punch_time >= today
            ).distinct().count()
            self.present_card.findChild(QLabel, "StatValue").setText(str(present_today))
            
            # Count late (stub logic: after 09:00:00)
            late_today = session.query(AttendanceRecord.employee_id).filter(
                AttendanceRecord.punch_time >= datetime.combine(today, datetime.min.time().replace(hour=9))
            ).filter(AttendanceRecord.punch_type == 'in').distinct().count()
            self.late_card.findChild(QLabel, "StatValue").setText(str(late_today))
            
            # Count on leave
            on_leave_today = session.query(Leave).filter(
                Leave.start_date <= today,
                Leave.end_date >= today,
                Leave.status == 'approved'
            ).count()
            
            absent_today = max(0, total_emp - present_today - on_leave_today)
            self.absent_card.findChild(QLabel, "StatValue").setText(str(absent_today))
            
            # Load recent activity and aggregate by employee/date
            records = session.query(AttendanceRecord).order_by(AttendanceRecord.punch_time.desc()).limit(50).all()
            formatted_data = AttendanceTable.aggregate_attendance_rows(records)[:10]
            self.table.load_data(formatted_data)
            
        except Exception as e:
            print(f"Error loading dashboard: {e}")
        finally:
            if 'session' in locals():
                session.close()

    def create_stat_card(self, title, value, icon):
        card = QFrame()
        card.setObjectName("Card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setMinimumHeight(120)
        
        layout = QVBoxLayout(card)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 24px;")
        layout.addWidget(icon_lbl)
        
        val_lbl = QLabel(value)
        val_lbl.setObjectName("StatValue")
        val_lbl.setStyleSheet("font-size: 28px; font-weight: bold; color: #333333;")
        layout.addWidget(val_lbl)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #666666; font-size: 14px;")
        layout.addWidget(title_lbl)
        
        return card

class AddLeaveDialog(QDialog):
    def __init__(self, employee_id, parent=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.setWindowTitle("Grant Leave")
        self.setFixedSize(400, 350)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Leave Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["vacation", "sick", "personal", "other"])
        layout.addWidget(self.type_combo)
        
        layout.addWidget(QLabel("Start Date:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        layout.addWidget(self.start_date)
        
        layout.addWidget(QLabel("End Date:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addDays(1))
        layout.addWidget(self.end_date)
        
        layout.addWidget(QLabel("Reason:"))
        self.reason_input = QLineEdit()
        layout.addWidget(self.reason_input)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setObjectName("ActionButton")
        save_btn.clicked.connect(self.save_leave)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_leave(self):
        from database.connection import db_manager
        from database.models import Leave
        
        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()
        
        if start > end:
            QMessageBox.warning(self, "Invalid Date", "End date must be after start date.")
            return

        try:
            session_factory = db_manager.get_session()
            session = session_factory()
            
            leave = Leave(
                employee_id=self.employee_id,
                start_date=start,
                end_date=end,
                leave_type=self.type_combo.currentText(),
                status='approved',
                reason=self.reason_input.text()
            )
            session.add(leave)
            session.commit()
            session.close()
            
            QMessageBox.information(self, "Success", "Leave granted successfully.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

class EmployeeDetailDialog(QDialog):
    def __init__(self, employee_id):
        super().__init__()
        self.employee_id = employee_id
        self.setWindowTitle("Employee Details")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Profile Header
        header = QFrame()
        header.setObjectName("Card")
        header_layout = QHBoxLayout(header)
        
        self.name_lbl = QLabel("Loading...")
        self.name_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #003366;")
        header_layout.addWidget(self.name_lbl)
        header_layout.addStretch()
        
        # Grant Leave Button
        leave_btn = QPushButton("Grant Leave")
        leave_btn.setObjectName("ActionButton")
        leave_btn.clicked.connect(self.open_leave_dialog)
        header_layout.addWidget(leave_btn)
        
        self.id_lbl = QLabel("ID: --")
        self.id_lbl.setStyleSheet("color: #666666;")
        header_layout.addWidget(self.id_lbl)
        
        layout.addWidget(header)

        # Info Grid
        info_frame = QFrame()
        info_frame.setObjectName("Card")
        info_layout = QGridLayout(info_frame)
        
        self.dept_lbl = QLabel("Department: ")
        self.status_lbl = QLabel("Status: ")
        self.hire_lbl = QLabel("Hire Date: ")
        self.email_lbl = QLabel("Email: ")

        info_layout.addWidget(self.dept_lbl, 0, 0)
        info_layout.addWidget(self.status_lbl, 0, 1)
        info_layout.addWidget(self.hire_lbl, 1, 0)
        info_layout.addWidget(self.email_lbl, 1, 1)
        
        layout.addWidget(info_frame)

        # Attendance History
        hist_lbl = QLabel("Attendance History")
        hist_lbl.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(hist_lbl)

        self.table = AttendanceTable()
        layout.addWidget(self.table)

        # Close Button
        close_btn = QPushButton("Close")
        close_btn.setObjectName("ActionButton")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)

    def open_leave_dialog(self):
        dialog = AddLeaveDialog(self.employee_id, self)
        dialog.exec()

    def load_data(self):
        from database.connection import db_manager
        from database.models import Employee, AttendanceRecord
        
        try:
            session_factory = db_manager.get_session()
            session = session_factory()
            
            emp = session.query(Employee).filter_by(id=self.employee_id).first()
            if not emp:
                return

            self.name_lbl.setText(f"{emp.first_name} {emp.last_name}")
            self.id_lbl.setText(f"Employee Number: {emp.employee_number}")
            self.id_lbl.setStyleSheet("color: #666666;")
            self.dept_lbl.setText(f"Department: {emp.department.name if emp.department else 'N/A'}")
            self.status_lbl.setText(f"Status: {emp.status.capitalize()}")
            self.hire_lbl.setText(f"Hire Date: {emp.hire_date.strftime('%Y-%m-%d') if emp.hire_date else 'N/A'}")
            self.email_lbl.setText(f"Email: {emp.email or 'N/A'}")

            # Attendance
            records = session.query(AttendanceRecord).filter_by(employee_id=emp.id).order_by(AttendanceRecord.punch_time.desc()).all()
            formatted_data = AttendanceTable.aggregate_attendance_rows(records)
            self.table.load_data(formatted_data)
            
        except Exception as e:
            print(f"Error loading detail dialog: {e}")
        finally:
            if 'session' in locals():
                session.close()

class EmployeesPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header = QLabel("Employee Management")
        header.setObjectName("HeaderTitle")
        layout.addWidget(header)

        # Toolbar
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("Add Employee")
        self.add_btn.setObjectName("ActionButton")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or ID...")
        self.search_input.setFixedWidth(300)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Employees", "Permanent", "Short Contract", "Intern"])
        self.filter_combo.currentTextChanged.connect(self.load_employees)
        self.filter_combo.setFixedWidth(150)
        
        self.sync_btn = QPushButton("Sync from Device")
        self.sync_btn.setObjectName("ActionButton")
        self.sync_btn.clicked.connect(self.sync_users)
        self.search_input.textChanged.connect(self.load_employees)
        
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.sync_btn)
        toolbar.addStretch()
        toolbar.addWidget(self.filter_combo)
        toolbar.addWidget(self.search_input)
        layout.addLayout(toolbar)

        # Employee Table
        self.table = AttendanceTable()
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Department", "Job Title", "Status", "Hire Date", "Action"])
        self.table.cellClicked.connect(self.on_row_clicked)
        
        layout.addWidget(self.table)
        layout.addStretch()
        
        self.employee_cache = [] # Store full objects for lookup
        self.load_employees()

    def on_row_clicked(self, row, column):
        emp_number = self.table.item(row, 0).text()
        # Find ID in cache
        for obj in self.employee_cache:
            if str(obj.employee_number) == str(emp_number):
                dialog = EmployeeDetailDialog(obj.id)
                dialog.exec()
                break

    def load_employees(self):
        from database.connection import db_manager
        from database.models import Employee, Department
        
        try:
            session_factory = db_manager.get_session()
            session = session_factory()
            
            search_text = self.search_input.text().strip().lower()
            filter_type = self.filter_combo.currentText()
            
            query = session.query(Employee).join(Department)
            
            if search_text:
                query = query.filter(
                    (Employee.first_name.ilike(f"%{search_text}%")) |
                    (Employee.last_name.ilike(f"%{search_text}%")) |
                    (Employee.employee_number.ilike(f"%{search_text}%")) |
                    (Department.name.ilike(f"%{search_text}%"))
                )
            
            if filter_type != "All Employees":
                if filter_type == "Short Contract":
                    query = query.filter(Employee.contract_type == 'short_contract')
                elif filter_type == "Permanent":
                    query = query.filter(Employee.contract_type == 'permanent')
                elif filter_type == "Intern":
                    query = query.filter(Employee.contract_type == 'intern')

            employees = query.all()
            self.employee_cache = employees # Update cache for detail lookup
            
            formatted_data = []
            for emp in employees:
                formatted_data.append({
                    'uid': emp.employee_number,
                    'name': f"{emp.first_name} {emp.last_name}",
                    'date': emp.department.name if emp.department else "N/A",
                    'time': emp.contract_type.capitalize() if emp.contract_type else "N/A",  # Reuse 'time' col for Job Title/Contract
                    'type': emp.status,
                    'device': emp.hire_date.strftime('%Y-%m-%d') if emp.hire_date else "N/A",
                    'status': 'Edit'
                })
            
            self.table.load_data(formatted_data)
        except Exception as e:
            print(f"Error loading employees: {e}")
        finally:
            if 'session' in locals():
                session.close()

    def sync_users(self):
        from devices.identix_k20 import IdentiXK20Adapter
        from database.connection import db_manager
        from database.models import Employee, Organization, Department
        from PyQt6.QtWidgets import QMessageBox

        # Load IP from settings
        settings_file = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                default_ip = settings.get('device_ip', '192.168.1.1')
        else:
            default_ip = '192.168.1.1'
        
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText("Syncing...")
        QApplication.processEvents()

        try:
            device = IdentiXK20Adapter(default_ip, timeout=5)
            if device.connect():
                users = device.get_users()
                device.disconnect()

                if not users:
                    QMessageBox.information(self, "Sync", "No users found on the device.")
                    return

                session_factory = db_manager.get_session()
                session = session_factory()

                # Ensure we have an organization and department (stub)
                org = session.query(Organization).first()
                if not org:
                    org = Organization(name="Default Org", code="DEFAULT")
                    session.add(org)
                    session.flush()
                
                dept = session.query(Department).first()
                if not dept:
                    dept = Department(organization_id=org.id, name="General", code="GEN")
                    session.add(dept)
                    session.flush()

                new_count = 0
                updated_count = 0
                for u in users:
                    # User user_id as employee_number
                    uid_str = str(u.user_id)
                    emp = session.query(Employee).filter_by(employee_number=uid_str).first()
                    
                    if not emp:
                        emp = Employee(
                            organization_id=org.id,
                            department_id=dept.id,
                            employee_number=uid_str,
                            first_name=u.name or "User",
                            last_name=uid_str,
                            status='active'
                        )
                        session.add(emp)
                        new_count += 1
                    else:
                        if emp.first_name != u.name and u.name:
                            emp.first_name = u.name
                            updated_count += 1
                
                session.commit()
                session.close()
                
                self.load_employees()
                QMessageBox.information(self, "Success", f"Synced {len(users)} users. {new_count} new, {updated_count} updated.")
            else:
                QMessageBox.warning(self, "Connection Error", f"Failed to connect to device at {default_ip}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            self.sync_btn.setEnabled(True)
            self.sync_btn.setText("Sync from Device")

class AttendancePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header = QLabel("Attendance Records")
        header.setObjectName("HeaderTitle")
        layout.addWidget(header)

        # Filters
        filters = QHBoxLayout()
        self.filter_checkbox = QCheckBox("Filter by Date:")
        self.filter_checkbox.setChecked(False)
        self.filter_checkbox.stateChanged.connect(self.on_filter_changed)
        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.dateChanged.connect(self.load_from_db)
        self.refresh_btn = QPushButton("Refresh Records")
        self.refresh_btn.setObjectName("ActionButton")
        
        self.refresh_btn.clicked.connect(self.refresh_attendance)
        
        filters.addWidget(self.filter_checkbox)
        filters.addWidget(self.date_filter)
        filters.addWidget(self.refresh_btn)
        filters.addStretch()
        layout.addLayout(filters)

        self.table = AttendanceTable()
        layout.addWidget(self.table)
        
        layout.addStretch()
        
        # Load initial data from DB
        self.load_from_db()

    def load_from_db(self):
        from database.connection import db_manager
        from database.models import AttendanceRecord, Employee
        
        try:
            session_factory = db_manager.get_session()
            session = session_factory()
            
            query = session.query(AttendanceRecord).join(Employee)
            records = query.order_by(AttendanceRecord.punch_time.desc()).all()
            
            if self.filter_checkbox.isChecked():
                selected_date = self.date_filter.date().toString("yyyy-MM-dd")
                records = [rec for rec in records if rec.punch_time.strftime('%Y-%m-%d') == selected_date]

            formatted_data = AttendanceTable.aggregate_attendance_rows(records)
            self.table.load_data(formatted_data)
        except Exception as e:
            print(f"Error loading from DB: {e}")
        finally:
            if 'session' in locals():
                session.close()

    def on_filter_changed(self):
        self.date_filter.setEnabled(self.filter_checkbox.isChecked())
        self.load_from_db()

    def refresh_attendance(self):
        from devices.identix_k20 import IdentiXK20Adapter
        from PyQt6.QtWidgets import QMessageBox
        from database.connection import db_manager
        from database.models import AttendanceRecord, Employee, Organization, Department
        from datetime import datetime

        # Load IP from settings
        settings_file = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                default_ip = settings.get('device_ip', '192.168.1.1')
        else:
            default_ip = '192.168.1.1'
        
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Refreshing...")
        QApplication.processEvents()

        try:
            device = IdentiXK20Adapter(default_ip, timeout=5)
            if device.connect():
                records = device.get_attendance()
                users = device.get_users()
                device.disconnect()

                if not records:
                    QMessageBox.information(self, "Attendance", "No new records found on the device.")
                    self.refresh_btn.setEnabled(True)
                    self.refresh_btn.setText("Refresh Records")
                    return

                session_factory = db_manager.get_session()
                session = session_factory()

                # Ensure we have an organization and department (stub)
                org = session.query(Organization).first()
                if not org:
                    org = Organization(name="Default Org", code="DEFAULT")
                    session.add(org)
                    session.flush()
                
                dept = session.query(Department).first()
                if not dept:
                    dept = Department(organization_id=org.id, name="General", code="GEN")
                    session.add(dept)
                    session.flush()

                # Sync users to Employees
                user_map = {} # uid -> employee_id
                for u in users:
                    emp = session.query(Employee).filter_by(employee_number=str(u.user_id)).first()
                    if not emp:
                        emp = Employee(
                            organization_id=org.id,
                            department_id=dept.id,
                            employee_number=str(u.user_id),
                            first_name=u.name or "User",
                            last_name=str(u.user_id),
                            status='active'
                        )
                        session.add(emp)
                        session.flush()
                    user_map[str(u.user_id)] = emp.id

                # Save attendance records
                new_count = 0
                for rec in records:
                    uid = str(getattr(rec, 'user_id', ''))
                    if uid not in user_map:
                        continue # Skip if user not found (shouldn't happen)
                    
                    punch_time = getattr(rec, 'timestamp', None)
                    if not punch_time: continue

                    # Check for duplicate
                    existing = session.query(AttendanceRecord).filter_by(
                        employee_id=user_map[uid],
                        punch_time=punch_time
                    ).first()
                    
                    if not existing:
                        # Map punch type
                        # 0: Check-In, 1: Check-Out, 4: Check-In, 5: Check-Out (sometimes)
                        # We'll use 0 as 'in' and anything else as 'out' for now, 
                        # but let's be more inclusive if possible.
                        p_val = getattr(rec, 'punch', 0)
                        p_type = 'in' if p_val in [0, 4] else 'out'
                        
                        new_rec = AttendanceRecord(
                            employee_id=user_map[uid],
                            device_id=1, # Stub device id
                            punch_time=punch_time,
                            punch_type=p_type,
                            status='valid'
                        )
                        session.add(new_rec)
                        new_count += 1
                
                session.commit()
                session.close()
                
                # Reload UI from DB
                self.load_from_db()
                QMessageBox.information(self, "Success", f"Synced {len(records)} records. {new_count} new records added.")
            else:
                QMessageBox.warning(self, "Connection Error", f"Failed to connect to device at {default_ip}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("Refresh Records")

class DevicesPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header = QLabel("Device Management")
        header.setObjectName("HeaderTitle")
        layout.addWidget(header)
        
        # Controls
        controls = QHBoxLayout()
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Device IP (e.g., 192.168.1.201)")
        self.ip_input.setFixedWidth(200)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("ActionButton")
        self.connect_btn.clicked.connect(self.test_connection)

        self.fetch_att_btn = QPushButton("Fetch Attendance")
        self.fetch_att_btn.setObjectName("ActionButton")
        self.fetch_att_btn.clicked.connect(self.fetch_attendance)
        
        controls.addWidget(self.ip_input)
        controls.addWidget(self.connect_btn)
        controls.addWidget(self.fetch_att_btn)
        controls.addStretch()
        layout.addLayout(controls)
        
        # Console/Status Output
        self.console_output = QLabel("Enter IP and click Connect to test device...")
        self.console_output.setWordWrap(True)
        self.console_output.setStyleSheet("background-color: #f1f5f9; padding: 10px; border-radius: 6px; font-family: monospace; color: #333333; border: 1px solid #d1d9e6;")
        self.console_output.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        layout.addWidget(self.console_output)
        layout.addStretch()

    def test_connection(self):
        from devices.identix_k20 import IdentiXK20Adapter
        
        ip = self.ip_input.text().strip()
        if not ip:
            self.console_output.setText("Please enter an IP address.")
            return
            
        self.console_output.setText(f"Connecting to {ip}...")
        QApplication.processEvents() # Force UI update
        
        try:
            device = IdentiXK20Adapter(ip, timeout=5)
            if device.connect():
                info = device.get_device_info()
                users = device.get_users()
                device.disconnect()
                
                msg = f"✅ Connected successfully!\n\n"
                msg += f"Device: {info.get('device_name', 'Unknown')}\n"
                msg += f"Serial: {info.get('serial', 'Unknown')}\n"
                msg += f"Firmware: {info.get('firmware', 'Unknown')}\n"
                msg += f"Users Found: {len(users)}"
                
                self.console_output.setText(msg)
            else:
                self.console_output.setText("❌ Connection failed. Check IP and network.")
        except Exception as e:
            self.console_output.setText(f"❌ Error: {str(e)}")

    def fetch_attendance(self):
        from devices.identix_k20 import IdentiXK20Adapter

        ip = self.ip_input.text().strip()
        if not ip:
            self.console_output.setText("Please enter an IP address.")
            return

        self.console_output.setText(f"Fetching attendance from {ip}...")
        QApplication.processEvents()

        try:
            device = IdentiXK20Adapter(ip, timeout=5)
            if device.connect():
                records = device.get_attendance()
                device.disconnect()

                if not records:
                    self.console_output.setText("No attendance records found.")
                    return

                msg = f"✅ Attendance fetched: {len(records)} records\n\n"
                for rec in records[:10]:
                    uid = getattr(rec, 'user_id', getattr(rec, 'uid', ''))
                    ts = getattr(rec, 'timestamp', getattr(rec, 'time', ''))
                    msg += f"UID: {uid}  Time: {ts}\n"

                if len(records) > 10:
                    msg += f"\n...and {len(records)-10} more records"

                self.console_output.setText(msg)
            else:
                self.console_output.setText("❌ Connection failed. Check IP and network.")
        except Exception as e:
            self.console_output.setText(f"❌ Error fetching attendance: {str(e)}")

class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header = QLabel("Reports & Analytics")
        header.setObjectName("HeaderTitle")
        layout.addWidget(header)

        # Report Types
        report_grid = QGridLayout()
        report_grid.setSpacing(20)

        reports = [
            ("Daily Attendance Report", "Summary of today\'s attendance with check-in, check-out and hours"),
            ("Weekly Attendance Report", "Weekly attendance summary with check-in, check-out and hours"),
            ("Monthly Attendance Report", "Monthly attendance summary with check-in, check-out and hours"),
            ("Monthly Leave Summary", "Overview of leave balances and types"),
            ("Employee Working Hours", "Detailed breakdown of payroll hours"),
            ("Device Sync Logs", "History of device communication and errors")
        ]

        for i, (title, desc) in enumerate(reports):
            card = QFrame()
            card.setObjectName("Card")
            card_layout = QVBoxLayout(card)
            
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
            d_lbl = QLabel(desc)
            d_lbl.setStyleSheet("color: #666666;")
            
            gen_btn = QPushButton("Generate PDF")
            gen_btn.setObjectName("ActionButton")
            gen_btn.clicked.connect(lambda checked, t=title: self.generate_report(t))
            
            card_layout.addWidget(t_lbl)
            card_layout.addWidget(d_lbl)
            card_layout.addStretch()
            card_layout.addWidget(gen_btn)
            
            report_grid.addWidget(card, i // 2, i % 2)

        layout.addLayout(report_grid)
        layout.addStretch()

    def generate_report(self, report_type):
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from database.connection import db_manager
        from database.models import AttendanceRecord, Employee
        from datetime import datetime, timedelta
        import calendar
        import os

        # Ensure directory exists
        report_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        filename = f"{report_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(report_dir, filename)
        
        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            elements.append(Paragraph(f"<b>{report_type}</b>", styles['Title']))
            elements.append(Spacer(1, 12))
            
            # Data Fetching Logic (Stubified for now based on report type)
            session = db_manager.get_session()()
            
            def build_attendance_rows(records):
                summary = {}
                for rec in records:
                    employee_number = getattr(rec.employee, 'employee_number', '')
                    employee_name = f"{getattr(rec.employee, 'first_name', '')} {getattr(rec.employee, 'last_name', '')}".strip()
                    attendance_date = rec.punch_time.date()
                    key = (employee_number, attendance_date)

                    entry = summary.get(key)
                    if entry is None:
                        entry = {
                            'uid': employee_number,
                            'name': employee_name,
                            'date': attendance_date.strftime('%Y-%m-%d'),
                            'check_in': '',
                            'check_out': '',
                            'device': f"Device {rec.device_id}" if rec.device_id is not None else '',
                            'status': rec.status,
                            '_earliest_in': None,
                            '_latest_out': None,
                            '_latest_time': rec.punch_time,
                        }
                        summary[key] = entry

                    if rec.punch_type == 'in':
                        if entry['_earliest_in'] is None or rec.punch_time < entry['_earliest_in']:
                            entry['_earliest_in'] = rec.punch_time
                            entry['check_in'] = rec.punch_time.strftime('%H:%M:%S')
                    elif rec.punch_type == 'out':
                        if entry['_latest_out'] is None or rec.punch_time > entry['_latest_out']:
                            entry['_latest_out'] = rec.punch_time
                            entry['check_out'] = rec.punch_time.strftime('%H:%M:%S')

                    if rec.punch_time > entry['_latest_time']:
                        entry['_latest_time'] = rec.punch_time
                        entry['device'] = f"Device {rec.device_id}" if rec.device_id is not None else entry['device']
                        entry['status'] = rec.status or entry['status']

                rows = []
                for entry in sorted(summary.values(), key=lambda item: (item['date'], item['name'])):
                    if entry['_earliest_in'] and entry['_latest_out']:
                        duration = entry['_latest_out'] - entry['_earliest_in']
                        hours = round(duration.total_seconds() / 3600, 2)
                        entry['hours'] = f"{hours:.2f}"
                    else:
                        entry['hours'] = ''
                    rows.append(entry)
                return rows

            data = []
            if "Daily Attendance" in report_type:
                today = datetime.now().date()
                start_dt = datetime.combine(today, datetime.min.time())
                end_dt = datetime.combine(today, datetime.max.time())
                data = [["ID", "Name", "Date", "Check In", "Check Out", "Hours", "Status"]]
                records = session.query(AttendanceRecord).join(Employee).filter(
                    AttendanceRecord.punch_time >= start_dt,
                    AttendanceRecord.punch_time <= end_dt
                ).order_by(AttendanceRecord.punch_time.asc()).all()
                for row in build_attendance_rows(records):
                    data.append([row['uid'], row['name'], row['date'], row['check_in'], row['check_out'], row['hours'], row['status']])
            elif "Weekly Attendance" in report_type:
                today = datetime.now().date()
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
                start_dt = datetime.combine(start_date, datetime.min.time())
                end_dt = datetime.combine(end_date, datetime.max.time())
                elements.append(Paragraph(f"Week: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", styles['Normal']))
                elements.append(Spacer(1, 10))
                data = [["ID", "Name", "Date", "Check In", "Check Out", "Hours", "Status"]]
                records = session.query(AttendanceRecord).join(Employee).filter(
                    AttendanceRecord.punch_time >= start_dt,
                    AttendanceRecord.punch_time <= end_dt
                ).order_by(AttendanceRecord.punch_time.asc()).all()
                for row in build_attendance_rows(records):
                    data.append([row['uid'], row['name'], row['date'], row['check_in'], row['check_out'], row['hours'], row['status']])
            elif "Monthly Attendance" in report_type:
                today = datetime.now().date()
                start_date = today.replace(day=1)
                last_day = calendar.monthrange(today.year, today.month)[1]
                end_date = today.replace(day=last_day)
                start_dt = datetime.combine(start_date, datetime.min.time())
                end_dt = datetime.combine(end_date, datetime.max.time())
                elements.append(Paragraph(f"Month: {today.strftime('%B %Y')}", styles['Normal']))
                elements.append(Spacer(1, 10))
                data = [["ID", "Name", "Date", "Check In", "Check Out", "Hours", "Status"]]
                records = session.query(AttendanceRecord).join(Employee).filter(
                    AttendanceRecord.punch_time >= start_dt,
                    AttendanceRecord.punch_time <= end_dt
                ).order_by(AttendanceRecord.punch_time.asc()).all()
                for row in build_attendance_rows(records):
                    data.append([row['uid'], row['name'], row['date'], row['check_in'], row['check_out'], row['hours'], row['status']])
            elif "Leave" in report_type:
                data = [["ID", "Name", "Leave Type", "Date", "Status"]]
                # Stub data
                data.append(["101", "John Doe", "Sick", "2024-01-10", "Approved"])
            else:
                data = [["Info"], ["No specific logic implemented for this report type."]]

            session.close()

            if len(data) > 1:
                t = Table(data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
            else:
                elements.append(Paragraph("No data found for this report.", styles['Normal']))

            doc.build(elements)
            QMessageBox.information(self, "Success", f"Report generated:\n{filepath}")
            
        except ImportError:
            QMessageBox.critical(self, "Error", "ReportLab library is missing. Install it with: pip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("Settings")
        header.setObjectName("HeaderTitle")
        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e2e8f0; background: white; border-radius: 4px; }
            QTabBar::tab { background: #f1f5f9; padding: 10px 20px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: white; border-bottom: 2px solid #003366; font-weight: bold; color: #003366; }
        """)
        
        # Initialize UI Tabs
        self.setup_general_tab()
        self.setup_admin_tab()
        self.setup_device_tab()
        self.setup_database_tab()
        
        layout.addWidget(self.tabs)
        
        # Load Data
        self.load_admins()
        self.load_general_settings()

    def setup_general_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Organization
        grp = QFrame()
        grp.setObjectName("Card")
        g_layout = QVBoxLayout(grp)
        
        lbl = QLabel("Organization Configuration")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f172a;")
        g_layout.addWidget(lbl)
        
        form = QGridLayout()
        form.setVerticalSpacing(15)
        
        form.addWidget(QLabel("Organization Name:"), 0, 0)
        self.org_input = QLineEdit()
        self.org_input.setPlaceholderText("Enter your organization name")
        form.addWidget(self.org_input, 0, 1)
        
        form.addWidget(QLabel("Timezone:"), 1, 0)
        self.tz_combo = QComboBox()
        self.tz_combo.addItems(["UTC", "Africa/Johannesburg", "US/Pacific", "US/Eastern"])
        form.addWidget(self.tz_combo, 1, 1)
        
        g_layout.addLayout(form)
        
        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("ActionButton")
        save_btn.setFixedWidth(150)
        save_btn.clicked.connect(self.save_general_settings)
        g_layout.addWidget(save_btn, 0, Qt.AlignmentFlag.AlignRight)
        
        layout.addWidget(grp)
        layout.addStretch()
        self.tabs.addTab(tab, "General")

    def setup_admin_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Add Admin Form
        form_frame = QFrame()
        form_frame.setObjectName("Card")
        f_layout = QHBoxLayout(form_frame)
        
        self.new_admin_user = QLineEdit()
        self.new_admin_user.setPlaceholderText("New Username")
        self.new_admin_pass = QLineEdit()
        self.new_admin_pass.setPlaceholderText("New Password")
        self.new_admin_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_admin_role = QComboBox()
        self.new_admin_role.addItems(["admin", "viewer", "superadmin"])
        
        add_btn = QPushButton("Create Admin")
        add_btn.setObjectName("ActionButton")
        add_btn.clicked.connect(self.add_admin)
        
        f_layout.addWidget(QLabel("Add New Admin:"))
        f_layout.addWidget(self.new_admin_user)
        f_layout.addWidget(self.new_admin_pass)
        f_layout.addWidget(self.new_admin_role)
        f_layout.addWidget(add_btn)
        
        layout.addWidget(form_frame)
        
        # Admin List
        self.admin_list = QTableWidget()
        self.admin_list.setColumnCount(4)
        self.admin_list.setHorizontalHeaderLabels(["ID", "Username", "Role", "Actions"])
        self.admin_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.admin_list.setAlternatingRowColors(True)
        self.admin_list.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #e2e8f0; border-radius: 4px; }
            QHeaderView::section { background-color: #f8fafc; color: #334155; padding: 8px; border: none; font-weight: bold; }
            QTableWidget::item { padding: 8px; }
        """)
        
        layout.addWidget(self.admin_list)
        self.tabs.addTab(tab, "Admin Users")

    def setup_device_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        conn_frame = QFrame()
        conn_frame.setObjectName("Card")
        c_layout = QVBoxLayout(conn_frame)
        
        c_layout.addWidget(QLabel("Biometric Device Connection"))
        
        controls = QHBoxLayout()
        self.dev_ip_input = QLineEdit()
        self.dev_ip_input.setPlaceholderText("Device IP (192.168.1.201)")
        # Load IP from settings
        settings_file = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                self.dev_ip_input.setText(settings.get('device_ip', '192.168.1.201'))
        else:
            self.dev_ip_input.setText("192.168.1.201")
        
        conn_btn = QPushButton("Connect & Test")
        conn_btn.setObjectName("ActionButton")
        conn_btn.clicked.connect(self.test_device_connection)
        
        fetch_btn = QPushButton("Fetch Logs")
        fetch_btn.setObjectName("ActionButton")
        fetch_btn.clicked.connect(self.fetch_attendance)
        
        controls.addWidget(self.dev_ip_input)
        controls.addWidget(conn_btn)
        controls.addWidget(fetch_btn)
        c_layout.addLayout(controls)
        
        self.dev_status_lbl = QLabel("Status: Idle")
        self.dev_status_lbl.setStyleSheet("font-weight: bold; color: #64748b; margin-top: 10px;")
        c_layout.addWidget(self.dev_status_lbl)
        
        self.dev_console = QLabel("Ready...")
        self.dev_console.setWordWrap(True)
        self.dev_console.setStyleSheet("background: #f1f5f9; padding: 10px; border-radius: 4px; font-family: monospace;")
        self.dev_console.setMinimumHeight(200)
        c_layout.addWidget(self.dev_console)
        
        layout.addWidget(conn_frame)
        layout.addStretch()
        self.tabs.addTab(tab, "Devices")

    def setup_database_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(30, 30, 30, 30)
        
        db_frame = QFrame()
        db_frame.setObjectName("Card")
        d_layout = QVBoxLayout(db_frame)
        
        d_layout.addWidget(QLabel("Database Management"))
        
        d_layout.addWidget(QLabel("Current Configuration: SQLite"))
        path_lbl = QLabel("Path: data/timetracker.db")
        path_lbl.setStyleSheet("color: #64748b; margin-bottom: 20px;")
        d_layout.addWidget(path_lbl)
        
        btns = QHBoxLayout()
        test_btn = QPushButton("Test Connection")
        test_btn.setObjectName("ActionButton")
        test_btn.clicked.connect(self.test_db_connection)
        
        init_btn = QPushButton("Re-Initialize Tables")
        init_btn.setObjectName("DangerButton") # Styled as warning if possible
        init_btn.clicked.connect(self.init_db_tables)
        
        btns.addWidget(test_btn)
        btns.addWidget(init_btn)
        btns.addStretch()
        d_layout.addLayout(btns)
        
        self.db_status = QLabel("")
        self.db_status.setWordWrap(True)
        d_layout.addWidget(self.db_status)
        
        layout.addWidget(db_frame)
        layout.addStretch()
        self.tabs.addTab(tab, "Databases")

    # --- Logic Methods ---

    def load_admins(self):
        from database.connection import db_manager
        from database.models import AdminUser
        try:
            session = db_manager.get_session()()
            admins = session.query(AdminUser).all()
            self.admin_list.setRowCount(0)
            for row, admin in enumerate(admins):
                self.admin_list.insertRow(row)
                self.admin_list.setItem(row, 0, QTableWidgetItem(str(admin.id)))
                self.admin_list.setItem(row, 1, QTableWidgetItem(admin.username))
                self.admin_list.setItem(row, 2, QTableWidgetItem(admin.role))
                
                if admin.username != 'admin':
                    del_btn = QPushButton("Delete")
                    del_btn.setStyleSheet("""
                        QPushButton { background-color: #ef4444; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; }
                        QPushButton:hover { background-color: #dc2626; }
                    """)
                    del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    del_btn.clicked.connect(lambda checked, aid=admin.id: self.delete_admin(aid))
                    self.admin_list.setCellWidget(row, 3, del_btn)
                else:
                    self.admin_list.setItem(row, 3, QTableWidgetItem("Protected"))
            session.close()
        except Exception as e:
            print(f"Error loading admins: {e}")

    def load_general_settings(self):
        import json
        import os
        settings_file = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                self.org_input.setText(settings.get('organization_name', ''))

    def save_general_settings(self):
        import json
        import os
        org_name = self.org_input.text().strip()
        settings_file = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        settings = {}
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        settings['organization_name'] = org_name
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=4)
        QMessageBox.information(self, "Saved", "General settings saved successfully.")

    def add_admin(self):
        from database.connection import db_manager
        from database.models import AdminUser
        
        u = self.new_admin_user.text().strip()
        p = self.new_admin_pass.text().strip()
        r = self.new_admin_role.currentText()
        
        if not u or not p:
            QMessageBox.warning(self, "Required", "Username and Password required.")
            return
            
        try:
            session = db_manager.get_session()()
            if session.query(AdminUser).filter_by(username=u).first():
                QMessageBox.warning(self, "Error", "User exists.")
                session.close()
                return
            session.add(AdminUser(username=u, password_hash=p, role=r))
            session.commit()
            session.close()
            self.new_admin_user.clear()
            self.new_admin_pass.clear()
            self.load_admins()
            QMessageBox.information(self, "Success", "Admin created.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def delete_admin(self, aid):
        from database.connection import db_manager
        from database.models import AdminUser
        
        if QMessageBox.question(self, "Confirm", "Delete this admin?") != QMessageBox.StandardButton.Yes:
            return
            
        try:
            session = db_manager.get_session()()
            session.query(AdminUser).filter_by(id=aid).delete()
            session.commit()
            session.close()
            self.load_admins()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def test_device_connection(self):
        from devices.identix_k20 import IdentiXK20Adapter
        ip = self.dev_ip_input.text().strip()
        self.dev_status_lbl.setText("Status: Connecting...")
        self.dev_console.setText("Connecting...")
        QApplication.processEvents()
        
        try:
            dev = IdentiXK20Adapter(ip, timeout=5)
            if dev.connect():
                # Save the IP to settings since connection succeeded
                settings_file = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
                settings = {}
                if os.path.exists(settings_file):
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                settings['device_ip'] = ip
                with open(settings_file, 'w') as f:
                    json.dump(settings, f, indent=4)
                
                self.dev_status_lbl.setText("Status: Connected")
                self.dev_status_lbl.setStyleSheet("font-weight: bold; color: #22c55e;")
                info = dev.get_device_info()
                dev.disconnect()
                self.dev_console.setText(f"Connected!\nInfo: {info}")
            else:
                self.dev_status_lbl.setText("Status: Failed")
                self.dev_status_lbl.setStyleSheet("font-weight: bold; color: #ef4444;")
                self.dev_console.setText("Connection failed.")
        except Exception as e:
            self.dev_status_lbl.setText("Status: Error")
            self.dev_console.setText(str(e))

    def fetch_attendance(self):
        from devices.identix_k20 import IdentiXK20Adapter
        ip = self.dev_ip_input.text().strip()
        self.dev_console.setText("Fetching records...")
        QApplication.processEvents()
        try:
            dev = IdentiXK20Adapter(ip, timeout=5)
            if dev.connect():
                recs = dev.get_attendance()
                dev.disconnect()
                self.dev_console.setText(f"Fetched {len(recs)} records.")
            else:
                self.dev_console.setText("Connection failed.")
        except Exception as e:
            self.dev_console.setText(str(e))

    def test_db_connection(self):
        from database.connection import db_manager
        from config import DATABASE_CONFIGS
        if db_manager.connect(DATABASE_CONFIGS['sqlite']):
             self.db_status.setText("✅ Connection Successful")
             self.db_status.setStyleSheet("color: green; padding: 10px; background: #dcfce7;")
        else:
             self.db_status.setText("❌ Connection Failed")

    def init_db_tables(self):
        from database.connection import db_manager
        if db_manager.init_database():
            self.db_status.setText("✅ Database Initialized")
            self.db_status.setStyleSheet("color: green; padding: 10px; background: #dcfce7;")
        else:
            self.db_status.setText("❌ Initialization Failed")

