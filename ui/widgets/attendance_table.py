
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt

class AttendanceTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # Configure standard columns
        columns = ["Employee ID", "Name", "Date", "Time", "Type", "Device", "Status"]
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
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
        record expecting dict: {'uid':..., 'name':..., 'date':..., 'time':..., 'type':..., 'device':..., 'status':...}
        """
        row = self.rowCount()
        self.insertRow(row)
        
        self.setItem(row, 0, QTableWidgetItem(str(record.get('uid', ''))))
        self.setItem(row, 1, QTableWidgetItem(str(record.get('name', ''))))
        self.setItem(row, 2, QTableWidgetItem(str(record.get('date', ''))))
        self.setItem(row, 3, QTableWidgetItem(str(record.get('time', ''))))
        self.setItem(row, 4, QTableWidgetItem(str(record.get('type', ''))))
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
