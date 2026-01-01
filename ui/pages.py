from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QSizePolicy, QLineEdit, QApplication, QDialog, QComboBox, QDateEdit, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QSize, QDate
from ui.widgets.attendance_table import AttendanceTable

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
        
        self.total_emp_card = self.create_stat_card("Total Employees", "124", "👥")
        self.present_card = self.create_stat_card("Present Today", "98", "✅")
        self.late_card = self.create_stat_card("Late Arrivals", "12", "⚠️")
        self.absent_card = self.create_stat_card("Absent", "14", "❌")

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
            
            # Load recent activity
            records = session.query(AttendanceRecord).order_by(AttendanceRecord.punch_time.desc()).limit(10).all()
            formatted_data = []
            for rec in records:
                formatted_data.append({
                    'uid': rec.employee.employee_number,
                    'name': f"{rec.employee.first_name} {rec.employee.last_name}",
                    'date': rec.punch_time.strftime('%Y-%m-%d'),
                    'time': rec.punch_time.strftime('%H:%M:%S'),
                    'type': 'Check-In' if rec.punch_type == 'in' else 'Check-Out',
                    'device': f"Device {rec.device_id}",
                    'status': rec.status
                })
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
            formatted_data = []
            for rec in records:
                formatted_data.append({
                    'uid': emp.employee_number,
                    'name': f"{emp.first_name} {emp.last_name}",
                    'date': rec.punch_time.strftime('%Y-%m-%d'),
                    'time': rec.punch_time.strftime('%H:%M:%S'),
                    'type': 'Check-In' if rec.punch_type == 'in' else 'Check-Out',
                    'device': f"Device {rec.device_id}",
                    'status': rec.status
                })
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

        default_ip = "192.168.1.198" 
        
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
        self.date_filter = QLineEdit()
        self.date_filter.setPlaceholderText("Filter by Date (YYYY-MM-DD)")
        self.refresh_btn = QPushButton("Refresh Records")
        self.refresh_btn.setObjectName("ActionButton")
        
        self.refresh_btn.clicked.connect(self.refresh_attendance)
        
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
            
            filter_date = self.date_filter.text().strip()
            
            query = session.query(AttendanceRecord).join(Employee)
            # Add filtering if needed, but for now just load all
            records = query.order_by(AttendanceRecord.punch_time.desc()).all()
            
            formatted_data = []
            for rec in records:
                date_str = rec.punch_time.strftime('%Y-%m-%d')
                
                if filter_date and filter_date != date_str:
                    continue
                    
                formatted_data.append({
                    'uid': rec.employee.employee_number,
                    'name': f"{rec.employee.first_name} {rec.employee.last_name}",
                    'date': date_str,
                    'time': rec.punch_time.strftime('%H:%M:%S'),
                    'type': 'Check-In' if rec.punch_type == 'in' else 'Check-Out',
                    'device': f"Device {rec.device_id}",
                    'status': rec.status
                })
            
            self.table.load_data(formatted_data)
        except Exception as e:
            print(f"Error loading from DB: {e}")
        finally:
            if 'session' in locals():
                session.close()

    def refresh_attendance(self):
        from devices.identix_k20 import IdentiXK20Adapter
        from PyQt6.QtWidgets import QMessageBox
        from database.connection import db_manager
        from database.models import AttendanceRecord, Employee, Organization, Department
        from datetime import datetime

        default_ip = "192.168.1.198" 
        
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
            ("Daily Attendance Report", "Summary of late/absent employees for today"),
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
            
            card_layout.addWidget(t_lbl)
            card_layout.addWidget(d_lbl)
            card_layout.addStretch()
            card_layout.addWidget(gen_btn)
            
            report_grid.addWidget(card, i // 2, i % 2)

        layout.addLayout(report_grid)
        layout.addStretch()

class DatabasesPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header = QLabel("Database Management")
        header.setObjectName("HeaderTitle")
        layout.addWidget(header)

        # Connection List / Card
        self.conn_frame = QFrame()
        self.conn_frame.setObjectName("Card")
        conn_layout = QVBoxLayout(self.conn_frame)

        title = QLabel("Active Database Connection")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        conn_layout.addWidget(title)

        desc = QLabel("Configure the SQL connection string to your database (PostgreSQL, MySQL, SQLite, etc.)")
        desc.setStyleSheet("color: #666666; margin-bottom: 15px;")
        conn_layout.addWidget(desc)

        title = QLabel("Database Configuration")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        conn_layout.addWidget(title)

        desc = QLabel("The system is configured to use SQLite for local data storage.")
        desc.setStyleSheet("color: #666666; margin-bottom: 15px;")
        conn_layout.addWidget(desc)

        self.db_path_info = QLabel("Database Path: data/timetracker.db")
        self.db_path_info.setStyleSheet("background-color: #f1f5f9; padding: 10px; border-radius: 4px; color: #003366; border: 1px solid #d1d9e6;")
        conn_layout.addWidget(self.db_path_info)

        btn_layout = QHBoxLayout()
        self.test_btn = QPushButton("Test SQLite Connection")
        self.test_btn.setObjectName("ActionButton")
        self.test_btn.clicked.connect(self.test_db_connection)
        
        self.init_btn = QPushButton("Initialize Tables")
        self.init_btn.setObjectName("ActionButton")
        self.init_btn.clicked.connect(self.init_db_tables)
        
        btn_layout.addWidget(self.test_btn)
        btn_layout.addWidget(self.init_btn)
        btn_layout.addStretch()
        conn_layout.addLayout(btn_layout)

        self.status_output = QLabel("")
        self.status_output.setWordWrap(True)
        self.status_output.setStyleSheet("padding: 10px; border-radius: 4px; background-color: #f1f5f9; color: #333333; border: 1px solid #d1d9e6;")
        conn_layout.addWidget(self.status_output)

        layout.addWidget(self.conn_frame)
        layout.addStretch()

    def test_db_connection(self):
        from database.connection import db_manager
        from config import DATABASE_CONFIGS
        
        self.show_status(f"Testing SQLite connection...", "info")
        QApplication.processEvents()
        
        if db_manager.connect(DATABASE_CONFIGS['sqlite']):
            self.show_status("✅ SQLite connection successful!", "success")
        else:
            self.show_status("❌ SQLite connection failed.", "error")

    def init_db_tables(self):
        from database.connection import db_manager
        from config import DATABASE_CONFIGS
        import database.models
        
        if not db_manager.engine:
            db_manager.connect(DATABASE_CONFIGS['sqlite'])
        
        self.show_status("Initializing database structure...", "info")
        QApplication.processEvents()
        
        if db_manager.init_database():
            self.show_status("✅ Structure initialized successfully!", "success")
        else:
            self.show_status("❌ Initialization failed.", "error")

    def show_status(self, message, mode):
        colors = {"info": "#89b4fa", "success": "#a6e3a1", "error": "#f38ba8"}
        self.status_output.setText(message)
        self.status_output.setStyleSheet(f"padding: 10px; border-radius: 4px; background-color: #181825; color: {colors.get(mode, '#ffffff')}; border: 1px solid {colors.get(mode, '#313244')};")

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header = QLabel("Settings")
        header.setObjectName("HeaderTitle")
        layout.addWidget(header)

        # Scroll Area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)

        # --- General Settings ---
        gen_frame = QFrame()
        gen_frame.setObjectName("Card")
        gen_layout = QVBoxLayout(gen_frame)
        
        gen_title = QLabel("General Configuration")
        gen_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #003366; margin-bottom: 10px;")
        gen_layout.addWidget(gen_title)

        org_lbl = QLabel("Organization Name")
        self.org_input = QLineEdit()
        self.org_input.setPlaceholderText("Enter organization name")
        
        gen_layout.addWidget(org_lbl)
        gen_layout.addWidget(self.org_input)
        
        save_btn = QPushButton("Save General Settings")
        save_btn.setObjectName("ActionButton")
        save_btn.setFixedWidth(180)
        
        gen_layout.addSpacing(10)
        gen_layout.addWidget(save_btn)
        
        content_layout.addWidget(gen_frame)

        # --- Device Management (Moved from DevicesPage) ---
        dev_frame = QFrame()
        dev_frame.setObjectName("Card")
        dev_layout = QVBoxLayout(dev_frame)
        
        dev_title = QLabel("Device Management")
        dev_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #003366; margin-bottom: 10px;")
        dev_layout.addWidget(dev_title)
        
        # Controls
        controls = QHBoxLayout()
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Device IP (e.g., 192.168.1.201)")
        self.ip_input.setFixedWidth(200)
        self.ip_input.setText("192.168.1.198") # Default for convenience
        
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
        dev_layout.addLayout(controls)
        
        # Status Label
        self.connection_status_lbl = QLabel("Status: Not Connected")
        self.connection_status_lbl.setStyleSheet("font-weight: bold; color: #666666; margin-top: 5px;")
        dev_layout.addWidget(self.connection_status_lbl)

        # Console/Status Output
        self.console_output = QLabel("Enter IP and click Connect to test device...")
        self.console_output.setWordWrap(True)
        self.console_output.setStyleSheet("background-color: #f1f5f9; padding: 10px; border-radius: 6px; font-family: monospace; color: #333333; border: 1px solid #d1d9e6; margin-top: 10px;")
        self.console_output.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.console_output.setMinimumHeight(100)
        
        dev_layout.addWidget(self.console_output)
        
        content_layout.addWidget(dev_frame)

        # --- Admin User Management ---
        admin_frame = QFrame()
        admin_frame.setObjectName("Card")
        admin_layout = QVBoxLayout(admin_frame)
        
        admin_title = QLabel("Admin Management")
        admin_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #003366; margin-bottom: 10px;")
        admin_layout.addWidget(admin_title)
        
        # Add Admin Form
        form_layout = QHBoxLayout()
        self.new_admin_user = QLineEdit()
        self.new_admin_user.setPlaceholderText("Username")
        self.new_admin_pass = QLineEdit()
        self.new_admin_pass.setPlaceholderText("Password")
        self.new_admin_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_admin_role = QComboBox()
        self.new_admin_role.addItems(["admin", "viewer", "superadmin"])
        
        add_admin_btn = QPushButton("Add Admin")
        add_admin_btn.setObjectName("ActionButton")
        add_admin_btn.clicked.connect(self.add_admin)
        
        form_layout.addWidget(self.new_admin_user)
        form_layout.addWidget(self.new_admin_pass)
        form_layout.addWidget(self.new_admin_role)
        form_layout.addWidget(add_admin_btn)
        
        admin_layout.addLayout(form_layout)
        admin_layout.addSpacing(10)
        
        # Admin List
        self.admin_list = QTableWidget()
        self.admin_list.setColumnCount(4)
        self.admin_list.setHorizontalHeaderLabels(["ID", "Username", "Role", "Action"])
        self.admin_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.admin_list.setStyleSheet("min-height: 200px;")
        
        admin_layout.addWidget(self.admin_list)
        
        content_layout.addWidget(admin_frame)
        
        # Load initial
        self.load_admins()

        content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

    def load_admins(self):
        from database.connection import db_manager
        from database.models import AdminUser
        
        try:
            session_factory = db_manager.get_session()
            session = session_factory()
            admins = session.query(AdminUser).all()
            
            self.admin_list.setRowCount(0)
            for row, admin in enumerate(admins):
                self.admin_list.insertRow(row)
                self.admin_list.setItem(row, 0, QTableWidgetItem(str(admin.id)))
                self.admin_list.setItem(row, 1, QTableWidgetItem(admin.username))
                self.admin_list.setItem(row, 2, QTableWidgetItem(admin.role))
                
                # Delete Button
                if admin.username != 'admin': # Prevent deleting default superadmin
                    del_btn = QPushButton("Delete")
                    del_btn.setObjectName("DangerButton")
                    del_btn.clicked.connect(lambda checked, aid=admin.id: self.delete_admin(aid))
                    self.admin_list.setCellWidget(row, 3, del_btn)
                else:
                    self.admin_list.setItem(row, 3, QTableWidgetItem("Protected"))
            
            session.close()
        except Exception as e:
            print(f"Error loading admins: {e}")

    def add_admin(self):
        from database.connection import db_manager
        from database.models import AdminUser
        
        user = self.new_admin_user.text().strip()
        pwd = self.new_admin_pass.text().strip()
        role = self.new_admin_role.currentText()
        
        if not user or not pwd:
            QMessageBox.warning(self, "Validation", "Username and Password are required.")
            return
            
        try:
            session_factory = db_manager.get_session()
            session = session_factory()
            
            # Check exist
            if session.query(AdminUser).filter_by(username=user).first():
                QMessageBox.warning(self, "Error", "Username already exists.")
                session.close()
                return
                
            new_admin = AdminUser(username=user, password_hash=pwd, role=role)
            session.add(new_admin)
            session.commit()
            session.close()
            
            self.new_admin_user.clear()
            self.new_admin_pass.clear()
            self.load_admins()
            QMessageBox.information(self, "Success", "Admin added successfully.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not add admin: {str(e)}")

    def delete_admin(self, admin_id):
        from database.connection import db_manager
        from database.models import AdminUser
        
        confirm = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this admin?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                session_factory = db_manager.get_session()
                session = session_factory()
                
                admin = session.query(AdminUser).get(admin_id)
                if admin:
                    session.delete(admin)
                    session.commit()
                
                session.close()
                self.load_admins()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Deletion failed: {str(e)}")


    def test_connection(self):
        from devices.identix_k20 import IdentiXK20Adapter
        
        ip = self.ip_input.text().strip()
        if not ip:
            self.console_output.setText("Please enter an IP address.")
            return
            
        self.console_output.setText(f"Connecting to {ip}...")
        self.connection_status_lbl.setText("Status: Connecting...")
        self.connection_status_lbl.setStyleSheet("font-weight: bold; color: #eab308;") # Yellow
        QApplication.processEvents()
        
        try:
            device = IdentiXK20Adapter(ip, timeout=5)
            if device.connect():
                info = device.get_device_info()
                users = device.get_users()
                device.disconnect()
                
                dev_name = info.get('device_name', 'Unknown Device')
                
                # Update Status Label
                self.connection_status_lbl.setText(f"Status: Connected to {dev_name}")
                self.connection_status_lbl.setStyleSheet("font-weight: bold; color: #16a34a;") # Green
                
                msg = f"✅ Connected successfully!\n\n"
                msg += f"Device: {dev_name}\n"
                msg += f"Serial: {info.get('serial', 'Unknown')}\n"
                msg += f"Firmware: {info.get('firmware', 'Unknown')}\n"
                msg += f"Users Found: {len(users)}"
                
                self.console_output.setText(msg)
            else:
                self.connection_status_lbl.setText("Status: Connection Failed")
                self.connection_status_lbl.setStyleSheet("font-weight: bold; color: #dc2626;") # Red
                self.console_output.setText("❌ Connection failed. Check IP and network.")
        except Exception as e:
            self.connection_status_lbl.setText("Status: Error")
            self.connection_status_lbl.setStyleSheet("font-weight: bold; color: #dc2626;")
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
                    # Determine type simply for display
                    p_val = getattr(rec, 'punch', 0)
                    p_type = 'Check-In' if p_val in [0, 4] else 'Check-Out'
                    
                    msg += f"UID: {uid} | {ts} | {p_type}\n"

                if len(records) > 10:
                    msg += f"\n...and {len(records)-10} more records"

                self.console_output.setText(msg)
            else:
                self.console_output.setText("❌ Connection failed. Check IP and network.")
        except Exception as e:
            self.console_output.setText(f"❌ Error fetching attendance: {str(e)}")

