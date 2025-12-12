# Database Schema Documentation

## Overview
This document defines the complete database schema for the E-Time Tracker system. The schema is database-agnostic and works with any SQL database supported by SQLAlchemy.

---

## Entity Relationship Diagram (Textual)

```
Organizations (1) ─────< (N) Departments
                              │
Departments (1) ──────────< (N) Employees
                              │
Employees (1) ────────────< (N) Attendance Records
         │                    │
         │                    │
         ├─< (N) Leave Requests
         │
         ├─< (N) Employee Shifts
         │
         └─< (N) Biometric Data
         
Devices (N) ─────────────> (N) Attendance Records
Shifts (1) ──────────────< (N) Employee Shifts
Leave Types (1) ─────────< (N) Leave Requests
```

---

## Table Definitions

### 1. Organizations Table
Stores organization/company information.

```sql
CREATE TABLE organizations (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'UTC',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**Indexes:**
- `idx_org_code` on `code`
- `idx_org_active` on `active`

---

### 2. Departments Table
Organizational departments.

```sql
CREATE TABLE departments (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    organization_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    parent_department_id INTEGER NULL,
    manager_id INTEGER NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_department_id) REFERENCES departments(id) ON DELETE SET NULL,
    FOREIGN KEY (manager_id) REFERENCES employees(id) ON DELETE SET NULL,
    UNIQUE (organization_id, code)
);
```

**Indexes:**
- `idx_dept_org` on `organization_id`
- `idx_dept_parent` on `parent_department_id`
- `idx_dept_active` on `active`

---

### 3. Employees Table
Employee master data.

```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    organization_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    employee_number VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    date_of_birth DATE,
    hire_date DATE NOT NULL,
    termination_date DATE NULL,
    job_title VARCHAR(100),
    employment_type ENUM('full-time', 'part-time', 'contract', 'intern') DEFAULT 'full-time',
    status ENUM('active', 'inactive', 'suspended', 'terminated') DEFAULT 'active',
    overtime_eligible BOOLEAN DEFAULT FALSE,
    default_shift_id INTEGER NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE RESTRICT,
    FOREIGN KEY (default_shift_id) REFERENCES shifts(id) ON DELETE SET NULL
);
```

**Indexes:**
- `idx_emp_number` on `employee_number`
- `idx_emp_org` on `organization_id`
- `idx_emp_dept` on `department_id`
- `idx_emp_status` on `status`
- `idx_emp_email` on `email`

---

### 4. Biometric Data Table
Stores biometric templates for employees.

```sql
CREATE TABLE biometric_data (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    employee_id INTEGER NOT NULL,
    biometric_type ENUM('fingerprint', 'face', 'rfid', 'palm', 'iris') NOT NULL,
    template_data BLOB NOT NULL,
    template_index INTEGER NOT NULL,
    quality_score INTEGER,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    device_id INTEGER NULL,
    active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL,
    UNIQUE (employee_id, biometric_type, template_index)
);
```

**Indexes:**
- `idx_bio_emp` on `employee_id`
- `idx_bio_type` on `biometric_type`
- `idx_bio_active` on `active`

---

### 5. Devices Table
Biometric devices and terminals.

```sql
CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    organization_id INTEGER NOT NULL,
    device_name VARCHAR(100) NOT NULL,
    device_model VARCHAR(100) NOT NULL,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    mac_address VARCHAR(20),
    ip_address VARCHAR(45),
    connection_type ENUM('lan', 'wifi', 'serial', 'usb') NOT NULL,
    protocol VARCHAR(50),
    port INTEGER,
    location VARCHAR(255),
    department_id INTEGER NULL,
    device_type ENUM('entry', 'exit', 'both') DEFAULT 'both',
    status ENUM('online', 'offline', 'error', 'maintenance') DEFAULT 'offline',
    last_sync_at TIMESTAMP NULL,
    last_heartbeat_at TIMESTAMP NULL,
    firmware_version VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);
```

**Indexes:**
- `idx_device_serial` on `serial_number`
- `idx_device_ip` on `ip_address`
- `idx_device_org` on `organization_id`
- `idx_device_status` on `status`
- `idx_device_active` on `active`

---

### 6. Shifts Table
Shift templates and definitions.

```sql
CREATE TABLE shifts (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    organization_id INTEGER NOT NULL,
    shift_name VARCHAR(100) NOT NULL,
    shift_code VARCHAR(50) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_minutes INTEGER NOT NULL,
    break_minutes INTEGER DEFAULT 0,
    grace_period_in INTEGER DEFAULT 0,
    grace_period_out INTEGER DEFAULT 0,
    late_threshold_minutes INTEGER DEFAULT 0,
    early_departure_threshold INTEGER DEFAULT 0,
    is_overnight BOOLEAN DEFAULT FALSE,
    is_flexible BOOLEAN DEFAULT FALSE,
    color_code VARCHAR(7),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    UNIQUE (organization_id, shift_code)
);
```

**Indexes:**
- `idx_shift_org` on `organization_id`
- `idx_shift_code` on `shift_code`
- `idx_shift_active` on `active`

---

### 7. Employee Shifts Table
Assignment of shifts to employees.

```sql
CREATE TABLE employee_shifts (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    employee_id INTEGER NOT NULL,
    shift_id INTEGER NOT NULL,
    effective_date DATE NOT NULL,
    end_date DATE NULL,
    day_of_week TINYINT NULL,
    is_recurring BOOLEAN DEFAULT FALSE,
    rotation_pattern VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (shift_id) REFERENCES shifts(id) ON DELETE CASCADE
);
```

**Indexes:**
- `idx_empshift_emp` on `employee_id`
- `idx_empshift_shift` on `shift_id`
- `idx_empshift_date` on `effective_date`
- Composite index on `(employee_id, effective_date)`

---

### 8. Attendance Records Table
Core attendance punch records.

```sql
CREATE TABLE attendance_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    employee_id INTEGER NOT NULL,
    device_id INTEGER NOT NULL,
    punch_time TIMESTAMP NOT NULL,
    punch_type ENUM('in', 'out', 'break_start', 'break_end') NOT NULL,
    punch_date DATE NOT NULL,
    verification_type ENUM('fingerprint', 'face', 'rfid', 'palm', 'password', 'manual') NOT NULL,
    verification_score INTEGER,
    temperature DECIMAL(4,2),
    mask_detected BOOLEAN,
    photo BLOB,
    device_location VARCHAR(255),
    ip_address VARCHAR(45),
    status ENUM('valid', 'invalid', 'duplicate', 'suspicious') DEFAULT 'valid',
    notes TEXT,
    is_manual BOOLEAN DEFAULT FALSE,
    created_by INTEGER NULL,
    synced_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE RESTRICT
);
```

**Indexes:**
- `idx_att_emp` on `employee_id`
- `idx_att_device` on `device_id`
- `idx_att_date` on `punch_date`
- `idx_att_time` on `punch_time`
- `idx_att_status` on `status`
- Composite index on `(employee_id, punch_date)`
- Composite index on `(punch_date, punch_time)`

---

### 9. Daily Attendance Summary Table
Processed daily attendance summaries.

```sql
CREATE TABLE daily_attendance (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    employee_id INTEGER NOT NULL,
    attendance_date DATE NOT NULL,
    shift_id INTEGER NULL,
    first_in TIMESTAMP NULL,
    last_out TIMESTAMP NULL,
    total_hours DECIMAL(5,2) DEFAULT 0,
    regular_hours DECIMAL(5,2) DEFAULT 0,
    overtime_hours DECIMAL(5,2) DEFAULT 0,
    break_hours DECIMAL(5,2) DEFAULT 0,
    late_minutes INTEGER DEFAULT 0,
    early_departure_minutes INTEGER DEFAULT 0,
    status ENUM('present', 'absent', 'late', 'half_day', 'leave', 'holiday', 'weekend', 'off') DEFAULT 'absent',
    is_processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (shift_id) REFERENCES shifts(id) ON DELETE SET NULL,
    UNIQUE (employee_id, attendance_date)
);
```

**Indexes:**
- `idx_daily_emp` on `employee_id`
- `idx_daily_date` on `attendance_date`
- `idx_daily_status` on `status`
- Composite index on `(employee_id, attendance_date)`
- Composite index on `(attendance_date, status)`

---

### 10. Leave Types Table
Definition of leave categories.

```sql
CREATE TABLE leave_types (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    organization_id INTEGER NOT NULL,
    leave_name VARCHAR(100) NOT NULL,
    leave_code VARCHAR(50) NOT NULL,
    description TEXT,
    is_paid BOOLEAN DEFAULT TRUE,
    requires_approval BOOLEAN DEFAULT TRUE,
    max_days_per_year INTEGER,
    max_consecutive_days INTEGER,
    advance_notice_days INTEGER DEFAULT 0,
    carry_forward BOOLEAN DEFAULT FALSE,
    prorate_on_joining BOOLEAN DEFAULT TRUE,
    applicable_after_days INTEGER DEFAULT 0,
    color_code VARCHAR(7),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    UNIQUE (organization_id, leave_code)
);
```

**Indexes:**
- `idx_leavetype_org` on `organization_id`
- `idx_leavetype_code` on `leave_code`
- `idx_leavetype_active` on `active`

---

### 11. Leave Balances Table
Employee leave balances.

```sql
CREATE TABLE leave_balances (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    employee_id INTEGER NOT NULL,
    leave_type_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    opening_balance DECIMAL(5,2) DEFAULT 0,
    earned DECIMAL(5,2) DEFAULT 0,
    used DECIMAL(5,2) DEFAULT 0,
    adjusted DECIMAL(5,2) DEFAULT 0,
    closing_balance DECIMAL(5,2) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (leave_type_id) REFERENCES leave_types(id) ON DELETE CASCADE,
    UNIQUE (employee_id, leave_type_id, year)
);
```

**Indexes:**
- `idx_balance_emp` on `employee_id`
- `idx_balance_year` on `year`
- Composite index on `(employee_id, leave_type_id, year)`

---

### 12. Leave Requests Table
Employee leave applications.

```sql
CREATE TABLE leave_requests (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    employee_id INTEGER NOT NULL,
    leave_type_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_days DECIMAL(4,2) NOT NULL,
    reason TEXT NOT NULL,
    emergency BOOLEAN DEFAULT FALSE,
    urgent BOOLEAN DEFAULT FALSE,
    status ENUM('pending', 'approved', 'rejected', 'cancelled', 'withdrawn') DEFAULT 'pending',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_by INTEGER NULL,
    approved_at TIMESTAMP NULL,
    rejection_reason TEXT,
    attachments TEXT,
    notes TEXT,
    
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (leave_type_id) REFERENCES leave_types(id) ON DELETE RESTRICT,
    FOREIGN KEY (approved_by) REFERENCES employees(id) ON DELETE SET NULL
);
```

**Indexes:**
- `idx_leave_emp` on `employee_id`
- `idx_leave_type` on `leave_type_id`
- `idx_leave_status` on `status`
- `idx_leave_dates` on `start_date, end_date`
- Composite index on `(employee_id, status)`

---

### 13. Holidays Table
Public and organizational holidays.

```sql
CREATE TABLE holidays (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    organization_id INTEGER NOT NULL,
    holiday_name VARCHAR(255) NOT NULL,
    holiday_date DATE NOT NULL,
    holiday_type ENUM('public', 'optional', 'restricted') DEFAULT 'public',
    is_recurring BOOLEAN DEFAULT FALSE,
    applies_to_all BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);
```

**Indexes:**
- `idx_holiday_org` on `organization_id`
- `idx_holiday_date` on `holiday_date`
- Composite index on `(organization_id, holiday_date)`

---

### 14. Users Table
System users and authentication.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    employee_id INTEGER UNIQUE,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'manager', 'hr', 'employee', 'operator') NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP NULL,
    password_changed_at TIMESTAMP NULL,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);
```

**Indexes:**
- `idx_user_username` on `username`
- `idx_user_email` on `email`
- `idx_user_active` on `is_active`

---

### 15. Audit Logs Table
System activity tracking.

```sql
CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    record_id INTEGER,
    old_values TEXT,
    new_values TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
```

**Indexes:**
- `idx_audit_user` on `user_id`
- `idx_audit_action` on `action`
- `idx_audit_table` on `table_name`
- `idx_audit_created` on `created_at`

---

### 16. System Settings Table
Application configuration.

```sql
CREATE TABLE system_settings (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50),
    category VARCHAR(50),
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    updated_by INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
);
```

---

### 17. Backup History Table
Backup tracking.

```sql
CREATE TABLE backup_history (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    backup_name VARCHAR(255) NOT NULL,
    backup_type ENUM('full', 'incremental', 'differential') NOT NULL,
    backup_path VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT,
    status ENUM('success', 'failed', 'in_progress') NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NULL,
    error_message TEXT,
    created_by INTEGER,
    
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);
```

**Indexes:**
- `idx_backup_status` on `status`
- `idx_backup_date` on `started_at`

---

## SQLAlchemy Model Example

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    employee_number = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    status = Column(Enum('active', 'inactive', 'suspended', 'terminated'), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="employees")
    department = relationship("Department", back_populates="employees")
    attendance_records = relationship("AttendanceRecord", back_populates="employee")
    leave_requests = relationship("LeaveRequest", back_populates="employee")
    biometric_data = relationship("BiometricData", back_populates="employee")
```

---

## Database Connection String Examples

```python
# PostgreSQL
SQLALCHEMY_DATABASE_URI = "postgresql://username:password@localhost:5432/timetracker"

# MySQL
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://username:password@localhost:3306/timetracker"

# SQL Server
SQLALCHEMY_DATABASE_URI = "mssql+pyodbc://username:password@localhost/timetracker?driver=ODBC+Driver+17+for+SQL+Server"

# Oracle
SQLALCHEMY_DATABASE_URI = "oracle+cx_oracle://username:password@localhost:1521/timetracker"

# SQLite (for development)
SQLALCHEMY_DATABASE_URI = "sqlite:///data/timetracker.db"
```

---

## Migration Strategy

1. Use Alembic for version control
2. Create migration scripts for schema changes
3. Support rollback capabilities
4. Test migrations on all supported databases
5. Document breaking changes

---

## Data Retention Policy

- Attendance records: 7 years (configurable)
- Audit logs: 3 years
- Backup files: 30 days (configurable)
- Archived data: Separate archive database

---

## Performance Optimization

1. **Indexing**: Create indexes on frequently queried columns
2. **Partitioning**: Partition large tables by date (attendance_records)
3. **Archiving**: Move old data to archive tables
4. **Query Optimization**: Use proper joins and avoid N+1 queries
5. **Connection Pooling**: Configure appropriate pool sizes
6. **Caching**: Cache frequently accessed lookup data

---

## Backup Strategy

1. **Full Backup**: Weekly on Sunday 2:00 AM
2. **Incremental Backup**: Daily at 2:00 AM
3. **Transaction Log Backup**: Every 4 hours (for supported databases)
4. **Backup Verification**: Automated restore testing
5. **Off-site Storage**: Copy backups to secondary location
6. **Retention**: Keep 30 days of backups

---

This schema provides a robust foundation for the time tracking system with support for all major SQL databases.
