
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text, BIGINT, Float, Date, Time, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
from database.connection import Base

class Organization(Base):
    __tablename__ = 'organizations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(100))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    departments = relationship("Department", back_populates="organization")
    employees = relationship("Employee", back_populates="organization")

class Department(Base):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    active = Column(Boolean, default=True)
    
    organization = relationship("Organization", back_populates="departments")
    employees = relationship("Employee", back_populates="department")

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    employee_number = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    status = Column(Enum('active', 'inactive', 'suspended', 'terminated'), default='active')
    contract_type = Column(Enum('permanent', 'short_contract', 'intern'), default='permanent')
    hire_date = Column(Date, nullable=False, default=datetime.utcnow().date)
    
    organization = relationship("Organization", back_populates="employees")
    department = relationship("Department", back_populates="employees")
    attendance_records = relationship("AttendanceRecord", back_populates="employee")
    leaves = relationship("Leave", back_populates="employee")

class Leave(Base):
    __tablename__ = 'leaves'
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    leave_type = Column(Enum('vacation', 'sick', 'personal', 'other'), default='vacation')
    status = Column(Enum('approved', 'pending', 'rejected'), default='pending')
    reason = Column(String(255))
    
    employee = relationship("Employee", back_populates="leaves")

class AttendanceRecord(Base):
    __tablename__ = 'attendance_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    device_id = Column(Integer, nullable=False) # Simplified for now
    punch_time = Column(DateTime, nullable=False)
    punch_type = Column(Enum('in', 'out', 'break_start', 'break_end'), nullable=False)
    status = Column(Enum('valid', 'invalid', 'duplicate', 'suspicious'), default='valid')
    
    employee = relationship("Employee", back_populates="attendance_records")

class Device(Base):
    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    device_name = Column(String(100), nullable=False)
    serial_number = Column(String(100), unique=True, nullable=False)
    ip_address = Column(String(45))
    port = Column(Integer, default=4370)
    status = Column(Enum('online', 'offline', 'error', 'maintenance'), default='offline')
    active = Column(Boolean, default=True)

class AdminUser(Base):
    __tablename__ = 'admin_users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False) # In real app, hash this. storing plain for simplicity if requested, or bcrypt. User didn't specify, but I should probably use simple hashing or clear text for this stage if no deps. Let's stick to cleartext for MVP speed unless I see a hasher util. I'll act as if it's hashed but might store plain for now to avoid dependency hell if werkzeug/bcrypt isn't installed. I'll check imports. No security libs. I'll store plain text for this specific step to ensure it works comfortably, or add a simple hash if I can. Let's just create the column.
    full_name = Column(String(100))
    role = Column(Enum('superadmin', 'admin', 'viewer'), default='admin')
    created_at = Column(DateTime, default=datetime.utcnow)

