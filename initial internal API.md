# Internal API Documentation

## Overview
This document describes the internal API layer for the E-Time Tracker desktop application. These APIs are used for inter-module communication and optional local REST API for integrations.

---

## Architecture Pattern

The application follows a **Service Layer Pattern** where:
1. UI Layer calls Service Layer
2. Service Layer contains business logic
3. Service Layer calls Repository Layer
4. Repository Layer interacts with Database

```
UI Layer → Service Layer → Repository Layer → Database
              ↓
         Device Layer
```

---

## 1. Authentication Service API

### Purpose
Handles user authentication, session management, and authorization.

### Methods

#### `authenticate(username: str, password: str) -> Dict`
Authenticates a user and creates a session.

**Parameters:**
- `username` (str): User's username
- `password` (str): User's plain text password

**Returns:**
```python
{
    "success": bool,
    "user": {
        "id": int,
        "username": str,
        "role": str,
        "employee_id": int,
        "full_name": str
    },
    "token": str,  # Session token
    "expires_at": datetime
}
```

**Exceptions:**
- `InvalidCredentialsError`: Invalid username or password
- `AccountLockedError`: Account is locked due to failed attempts
- `AccountDisabledError`: User account is disabled

---

#### `logout(token: str) -> bool`
Logs out a user and invalidates the session.

**Parameters:**
- `token` (str): Session token

**Returns:** Boolean indicating success

---

#### `validate_session(token: str) -> bool`
Checks if a session is valid and active.

**Parameters:**
- `token` (str): Session token

**Returns:** Boolean indicating validity

---

#### `check_permission(user_id: int, permission: str) -> bool`
Checks if user has specific permission.

**Parameters:**
- `user_id` (int): User ID
- `permission` (str): Permission string (e.g., 'attendance.view', 'employee.create')

**Returns:** Boolean indicating permission status

---

## 2. Employee Service API

### Purpose
Manages employee data and operations.

### Methods

#### `create_employee(data: Dict) -> Employee`
Creates a new employee record.

**Parameters:**
```python
{
    "organization_id": int,
    "department_id": int,
    "employee_number": str,
    "first_name": str,
    "last_name": str,
    "middle_name": str (optional),
    "email": str,
    "phone": str (optional),
    "date_of_birth": date,
    "hire_date": date,
    "job_title": str,
    "employment_type": str,  # 'full-time', 'part-time', 'contract', 'intern'
    "overtime_eligible": bool
}
```

**Returns:** Employee object

**Exceptions:**
- `ValidationError`: Invalid data
- `DuplicateEmployeeError`: Employee number already exists

---

#### `get_employee(employee_id: int) -> Employee`
Retrieves employee by ID.

**Parameters:**
- `employee_id` (int): Employee ID

**Returns:** Employee object

**Exceptions:**
- `EmployeeNotFoundError`: Employee doesn't exist

---

#### `update_employee(employee_id: int, data: Dict) -> Employee`
Updates employee information.

**Parameters:**
- `employee_id` (int): Employee ID
- `data` (Dict): Fields to update

**Returns:** Updated Employee object

---

#### `delete_employee(employee_id: int) -> bool`
Soft deletes an employee (changes status to terminated).

**Parameters:**
- `employee_id` (int): Employee ID

**Returns:** Boolean indicating success

---

#### `search_employees(filters: Dict, page: int = 1, limit: int = 50) -> Dict`
Searches employees with filters.

**Parameters:**
```python
{
    "department_id": int (optional),
    "status": str (optional),
    "search_query": str (optional),  # Searches name, email, employee_number
    "employment_type": str (optional)
}
```

**Returns:**
```python
{
    "employees": List[Employee],
    "total": int,
    "page": int,
    "pages": int
}
```

---

#### `enroll_biometric(employee_id: int, biometric_type: str, template_data: bytes) -> BiometricData`
Enrolls biometric data for employee.

**Parameters:**
- `employee_id` (int): Employee ID
- `biometric_type` (str): 'fingerprint', 'face', 'rfid', 'palm', 'iris'
- `template_data` (bytes): Binary biometric template

**Returns:** BiometricData object

---

## 3. Attendance Service API

### Purpose
Manages attendance recording and processing.

### Methods

#### `record_punch(data: Dict) -> AttendanceRecord`
Records a clock-in or clock-out event.

**Parameters:**
```python
{
    "employee_id": int,
    "device_id": int,
    "punch_time": datetime,
    "punch_type": str,  # 'in', 'out', 'break_start', 'break_end'
    "verification_type": str,  # 'fingerprint', 'face', 'rfid', etc.
    "verification_score": int (optional),
    "temperature": float (optional),
    "photo": bytes (optional)
}
```

**Returns:** AttendanceRecord object

**Exceptions:**
- `EmployeeNotFoundError`
- `DeviceNotFoundError`
- `DuplicatePunchError`: Duplicate punch within threshold

---

#### `get_attendance_records(employee_id: int, start_date: date, end_date: date) -> List[AttendanceRecord]`
Retrieves attendance records for date range.

**Parameters:**
- `employee_id` (int): Employee ID
- `start_date` (date): Start date
- `end_date` (date): End date

**Returns:** List of AttendanceRecord objects

---

#### `process_daily_attendance(employee_id: int, attendance_date: date) -> DailyAttendance`
Processes raw punches into daily summary.

**Parameters:**
- `employee_id` (int): Employee ID
- `attendance_date` (date): Date to process

**Returns:** DailyAttendance object with calculated hours

---

#### `calculate_work_hours(punches: List[AttendanceRecord], shift: Shift) -> Dict`
Calculates work hours from punch records.

**Parameters:**
- `punches` (List[AttendanceRecord]): Punch records for the day
- `shift` (Shift): Employee's shift

**Returns:**
```python
{
    "total_hours": float,
    "regular_hours": float,
    "overtime_hours": float,
    "break_hours": float,
    "late_minutes": int,
    "early_departure_minutes": int,
    "status": str  # 'present', 'late', 'half_day', 'absent'
}
```

---

#### `get_daily_summary(employee_id: int, month: int, year: int) -> List[DailyAttendance]`
Gets monthly attendance summary.

**Parameters:**
- `employee_id` (int): Employee ID
- `month` (int): Month (1-12)
- `year` (int): Year

**Returns:** List of DailyAttendance objects

---

#### `mark_manual_attendance(data: Dict, user_id: int) -> AttendanceRecord`
Manually records attendance (requires permission).

**Parameters:**
```python
{
    "employee_id": int,
    "punch_time": datetime,
    "punch_type": str,
    "reason": str,
    "notes": str (optional)
}
```

**Returns:** AttendanceRecord object

---

#### `validate_attendance(record_id: int, is_valid: bool, notes: str) -> bool`
Validates or invalidates an attendance record.

**Parameters:**
- `record_id` (int): Attendance record ID
- `is_valid` (bool): Validation status
- `notes` (str): Validation notes

**Returns:** Boolean indicating success

---

## 4. Shift Service API

### Purpose
Manages shift definitions and assignments.

### Methods

#### `create_shift(data: Dict) -> Shift`
Creates a new shift template.

**Parameters:**
```python
{
    "organization_id": int,
    "shift_name": str,
    "shift_code": str,
    "start_time": time,
    "end_time": time,
    "break_minutes": int,
    "grace_period_in": int,  # minutes
    "grace_period_out": int,
    "late_threshold_minutes": int,
    "is_overnight": bool,
    "is_flexible": bool
}
```

**Returns:** Shift object

---

#### `assign_shift(employee_id: int, shift_id: int, effective_date: date, end_date: date = None) -> EmployeeShift`
Assigns shift to employee.

**Parameters:**
- `employee_id` (int): Employee ID
- `shift_id` (int): Shift ID
- `effective_date` (date): Start date
- `end_date` (date, optional): End date (null for permanent)

**Returns:** EmployeeShift object

---

#### `get_employee_shift(employee_id: int, target_date: date) -> Shift`
Gets employee's shift for specific date.

**Parameters:**
- `employee_id` (int): Employee ID
- `target_date` (date): Date to check

**Returns:** Shift object or None

---

#### `create_shift_rotation(data: Dict) -> List[EmployeeShift]`
Creates rotating shift pattern.

**Parameters:**
```python
{
    "employee_ids": List[int],
    "shift_ids": List[int],
    "start_date": date,
    "rotation_days": int,  # Number of days before rotation
    "pattern": str  # e.g., "A-B-C-A-B-C" or "weekly"
}
```

**Returns:** List of EmployeeShift objects

---

#### `swap_shift_request(from_employee_id: int, to_employee_id: int, swap_date: date) -> Dict`
Requests a shift swap.

**Parameters:**
- `from_employee_id` (int): Requesting employee
- `to_employee_id` (int): Target employee
- `swap_date` (date): Date to swap

**Returns:** Swap request object

---

#### `get_shift_schedule(department_id: int, start_date: date, end_date: date) -> Dict`
Gets shift schedule for department.

**Parameters:**
- `department_id` (int): Department ID
- `start_date` (date): Start date
- `end_date` (date): End date

**Returns:**
```python
{
    "schedule": [
        {
            "date": date,
            "employees": [
                {
                    "employee_id": int,
                    "employee_name": str,
                    "shift": Shift
                }
            ]
        }
    ]
}
```

---

## 5. Leave Service API

### Purpose
Manages leave requests and balances.

### Methods

#### `apply_leave(data: Dict) -> LeaveRequest`
Submits a leave request.

**Parameters:**
```python
{
    "employee_id": int,
    "leave_type_id": int,
    "start_date": date,
    "end_date": date,
    "reason": str,
    "emergency": bool,
    "urgent": bool,
    "attachments": List[str] (optional)
}
```

**Returns:** LeaveRequest object

**Exceptions:**
- `InsufficientLeaveBalanceError`
- `LeaveOverlapError`
- `InvalidLeaveDateError`

---

#### `approve_leave(request_id: int, approved_by: int, notes: str = None) -> LeaveRequest`
Approves a leave request.

**Parameters:**
- `request_id` (int): Leave request ID
- `approved_by` (int): Approver's user ID
- `notes` (str, optional): Approval notes

**Returns:** Updated LeaveRequest object

---

#### `reject_leave(request_id: int, rejected_by: int, reason: str) -> LeaveRequest`
Rejects a leave request.

**Parameters:**
- `request_id` (int): Leave request ID
- `rejected_by` (int): Rejector's user ID
- `reason` (str): Rejection reason

**Returns:** Updated LeaveRequest object

---

#### `cancel_leave(request_id: int, employee_id: int, reason: str) -> LeaveRequest`
Cancels an approved leave.

**Parameters:**
- `request_id` (int): Leave request ID
- `employee_id` (int): Employee ID
- `reason` (str): Cancellation reason

**Returns:** Updated LeaveRequest object

---

#### `get_leave_balance(employee_id: int, leave_type_id: int, year: int) -> LeaveBalance`
Gets leave balance for employee.

**Parameters:**
- `employee_id` (int): Employee ID
- `leave_type_id` (int): Leave type ID
- `year` (int): Year

**Returns:** LeaveBalance object

---

#### `get_pending_approvals(manager_id: int) -> List[LeaveRequest]`
Gets pending leave requests for approval.

**Parameters:**
- `manager_id` (int): Manager's employee ID

**Returns:** List of pending LeaveRequest objects

---

#### `calculate_leave_days(start_date: date, end_date: date, include_weekends: bool = False) -> float`
Calculates leave days excluding weekends/holidays.

**Parameters:**
- `start_date` (date): Start date
- `end_date` (date): End date
- `include_weekends` (bool): Whether to include weekends

**Returns:** Number of leave days (can be fractional for half-days)

---

#### `update_leave_balance(employee_id: int, leave_type_id: int, year: int, adjustment: float, reason: str) -> LeaveBalance`
Adjusts leave balance (admin function).

**Parameters:**
- `employee_id` (int): Employee ID
- `leave_type_id` (int): Leave type ID
- `year` (int): Year
- `adjustment` (float): Balance adjustment (+ or -)
- `reason` (str): Reason for adjustment

**Returns:** Updated LeaveBalance object

---

## 6. Device Service API

### Purpose
Manages biometric devices and communication.

### Methods

#### `register_device(data: Dict) -> Device`
Registers a new device.

**Parameters:**
```python
{
    "organization_id": int,
    "device_name": str,
    "device_model": str,
    "serial_number": str,
    "ip_address": str,
    "connection_type": str,  # 'lan', 'wifi', 'serial', 'usb'
    "port": int,
    "location": str,
    "department_id": int (optional)
}
```

**Returns:** Device object

---

#### `connect_device(device_id: int) -> Dict`
Establishes connection with device.

**Parameters:**
- `device_id` (int): Device ID

**Returns:**
```python
{
    "success": bool,
    "status": str,  # 'online', 'offline', 'error'
    "message": str,
    "device_info": Dict
}
```

---

#### `disconnect_device(device_id: int) -> bool`
Disconnects from device.

**Parameters:**
- `device_id` (int): Device ID

**Returns:** Boolean indicating success

---

#### `sync_employees_to_device(device_id: int, employee_ids: List[int] = None) -> Dict`
Syncs employee data to device.

**Parameters:**
- `device_id` (int): Device ID
- `employee_ids` (List[int], optional): Specific employees (None for all)

**Returns:**
```python
{
    "success": bool,
    "synced_count": int,
    "failed_count": int,
    "errors": List[str]
}
```

---

#### `fetch_attendance_from_device(device_id: int, since: datetime = None) -> List[Dict]`
Retrieves attendance records from device.

**Parameters:**
- `device_id` (int): Device ID
- `since` (datetime, optional): Fetch records after this time

**Returns:** List of raw attendance data dictionaries

---

#### `get_device_status(device_id: int) -> Dict`
Gets current device status.

**Parameters:**
- `device_id` (int): Device ID

**Returns:**
```python
{
    "status": str,  # 'online', 'offline', 'error', 'maintenance'
    "last_heartbeat": datetime,
    "last_sync": datetime,
    "employee_count": int,
    "attendance_count": int,
    "storage_usage": float,  # percentage
    "firmware_version": str
}
```

---

#### `discover_devices(network_range: str = None) -> List[Dict]`
Discovers devices on network.

**Parameters:**
- `network_range` (str, optional): IP range to scan (e.g., "192.168.1.0/24")

**Returns:** List of discovered device information

---

#### `update_device_firmware(device_id: int, firmware_path: str) -> Dict`
Updates device firmware.

**Parameters:**
- `device_id` (int): Device ID
- `firmware_path` (str): Path to firmware file

**Returns:** Update status dictionary

---

## 7. Report Service API

### Purpose
Generates various reports and analytics.

### Methods

#### `generate_attendance_report(filters: Dict) -> bytes`
Generates attendance report.

**Parameters:**
```python
{
    "employee_ids": List[int] (optional),
    "department_id": int (optional),
    "start_date": date,
    "end_date": date,
    "format": str,  # 'pdf', 'excel', 'csv'
    "include_summary": bool,
    "group_by": str  # 'employee', 'department', 'date'
}
```

**Returns:** Report file as bytes

---

#### `generate_leave_report(filters: Dict) -> bytes`
Generates leave report.

**Parameters:**
```python
{
    "employee_ids": List[int] (optional),
    "leave_type_id": int (optional),
    "start_date": date,
    "end_date": date,
    "status": str (optional),
    "format": str
}
```

**Returns:** Report file as bytes

---

#### `get_attendance_statistics(department_id: int, month: int, year: int) -> Dict`
Gets attendance statistics.

**Parameters:**
- `department_id` (int): Department ID
- `month` (int): Month
- `year` (int): Year

**Returns:**
```python
{
    "total_employees": int,
    "average_attendance": float,
    "late_arrivals": int,
    "early_departures": int,
    "absences": int,
    "overtime_hours": float,
    "on_leave": int
}
```

---

#### `export_payroll_data(department_id: int, start_date: date, end_date: date) -> bytes`
Exports payroll-ready data.

**Parameters:**
- `department_id` (int): Department ID
- `start_date` (date): Start date
- `end_date` (date): End date

**Returns:** Excel file with payroll data

---

## 8. Backup Service API

### Purpose
Manages database backups.

### Methods

#### `create_backup(backup_type: str = 'full') -> Dict`
Creates a database backup.

**Parameters:**
- `backup_type` (str): 'full', 'incremental', or 'differential'

**Returns:**
```python
{
    "success": bool,
    "backup_id": int,
    "backup_file": str,
    "file_size": int,
    "started_at": datetime,
    "completed_at": datetime
}
```

---

#### `restore_backup(backup_id: int, confirm: bool = False) -> Dict`
Restores from backup.

**Parameters:**
- `backup_id` (int): Backup ID
- `confirm` (bool): Confirmation flag

**Returns:** Restore status dictionary

**Exceptions:**
- `BackupNotFoundError`
- `RestoreConfirmationRequiredError`

---

#### `list_backups(limit: int = 20) -> List[Dict]`
Lists available backups.

**Parameters:**
- `limit` (int): Maximum number of backups to return

**Returns:** List of backup information dictionaries

---

#### `delete_backup(backup_id: int) -> bool`
Deletes a backup file.

**Parameters:**
- `backup_id` (int): Backup ID

**Returns:** Boolean indicating success

---

#### `verify_backup(backup_id: int) -> Dict`
Verifies backup integrity.

**Parameters:**
- `backup_id` (int): Backup ID

**Returns:**
```python
{
    "valid": bool,
    "checksum_match": bool,
    "can_restore": bool,
    "error": str (if any)
}
```

---

## Error Handling

All API methods follow consistent error handling:

```python
try:
    result = service.method(params)
except ValidationError as e:
    # Handle validation errors
    return {"error": "validation", "message": str(e), "fields": e.fields}
except NotFoundError as e:
    # Handle not found errors
    return {"error": "not_found", "message": str(e)}
except PermissionError as e:
    # Handle permission errors
    return {"error": "permission_denied", "message": str(e)}
except DatabaseError as e:
    # Handle database errors
    return {"error": "database", "message": "Database operation failed"}
except Exception as e:
    # Handle unexpected errors
    logger.error(f"Unexpected error: {e}")
    return {"error": "internal", "message": "An unexpected error occurred"}
```

---

## Response Format

All API responses follow this structure:

```python
# Success Response
{
    "success": True,
    "data": {...},
    "message": "Operation successful"
}

# Error Response
{
    "success": False,
    "error": {
        "code": "error_code",
        "message": "Error description",
        "details": {...}
    }
}
```

---

## Usage Examples

### Example 1: Recording Attendance

```python
from services.attendance_service import AttendanceService

attendance_service = AttendanceService()

# Record clock-in
result = attendance_service.record_punch({
    "employee_id": 123,
    "device_id": 5,
    "punch_time": datetime.now(),
    "punch_type": "in",
    "verification_type": "fingerprint",
    "verification_score": 95
})

print(f"Attendance recorded: {result.id}")
```

### Example 2: Applying for Leave

```python
from services.leave_service import LeaveService

leave_service = LeaveService()

# Apply for leave
leave_request = leave_service.apply_leave({
    "employee_id": 123,
    "leave_type_id": 1,
    "start_date": date(2025, 1, 15),
    "end_date": date(2025, 1, 17),
    "reason": "Family emergency",
    "emergency": True
})

print(f"Leave request submitted: {leave_request.id}")
```

### Example 3: Generating Report

```python
from services.report_service import ReportService

report_service = ReportService()

# Generate monthly attendance report
report_data = report_service.generate_attendance_report({
    "department_id": 5,
    "start_date": date(2025, 1, 1),
    "end_date": date(2025, 1, 31),
    "format": "pdf",
    "include_summary": True
})

with open("attendance_report.pdf", "wb") as f:
    f.write(report_data)
```

---
