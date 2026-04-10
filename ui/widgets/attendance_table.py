
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt

class AttendanceTable(QTableWidget):
    def __init__(self, parent=None, columns=None):
        super().__init__(parent)
        self.columns = columns or ["Employee ID", "Name", "Date", "Check In", "Check Out", "Device", "Status"]
        self.setup_ui()
        
    def setup_ui(self):
        # Configure standard columns
        self.setColumnCount(len(self.columns))
        self.setHorizontalHeaderLabels(self.columns)
        
        # Style and behavior
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setShowGrid(False)
        
    def add_record(self, record):
        """
        Adds a record to the table.
        Supports attendance summary records with keys: 'uid', 'name', 'date', 'check_in', 'check_out', 'device', 'status'.
        Also supports legacy row records with 'time', 'type'.
        """
        row = self.rowCount()
        self.insertRow(row)
        
        self.setItem(row, 0, QTableWidgetItem(str(record.get('uid', ''))))
        self.setItem(row, 1, QTableWidgetItem(str(record.get('name', ''))))
        self.setItem(row, 2, QTableWidgetItem(str(record.get('date', ''))))
        self.setItem(row, 3, QTableWidgetItem(str(record.get('check_in', record.get('time', '')))))
        self.setItem(row, 4, QTableWidgetItem(str(record.get('check_out', record.get('type', '')))))
        self.setItem(row, 5, QTableWidgetItem(str(record.get('device', ''))))
        
        status_item = QTableWidgetItem(str(record.get('status', '')))
        # Basic conditional formatting for status
        if record.get('status', '').lower() == 'late':
            status_item.setForeground(Qt.GlobalColor.red)
        
        self.setItem(row, 6, status_item)

    def load_data(self, data):
        self.setRowCount(0)
        for row in data:
            self.add_record(row)

    @staticmethod
    def aggregate_attendance_rows(records):
        """Aggregate punch records into per-employee per-date check-in/check-out summary rows."""
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

        rows = sorted(summary.values(), key=lambda item: (item['date'], item['_latest_time']), reverse=True)
        for row in rows:
            row.pop('_earliest_in', None)
            row.pop('_latest_out', None)
            row.pop('_latest_time', None)
        return rows
