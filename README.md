# E-Time Tracker Desktop System Architecture

## System Overview
A comprehensive desktop-based time and attendance tracking system built with Python. Supports multiple biometric devices (including identiX K20), any SQL database via connection string, and provides complete shift, leave, and attendance management capabilities.

---

## Master Directory Structure

```
e-time-tracker/
│
├── app.py                          # Main application entry point
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
├── .env.example                    # Environment variables template
│
├── core/                           # Core business logic
│   ├── __init__.py
│   ├── attendance.py               # Attendance processing logic
│   ├── shifts.py                   # Shift management logic
│   ├── leaves.py                   # Leave management logic
│   ├── employees.py                # Employee management logic
│   └── reports.py                  # Report generation logic
│
├── database/                       # Database layer
│   ├── __init__.py
│   ├── connection.py               # Database connection manager
│   ├── models.py                   # SQLAlchemy models
│   ├── repositories.py             # Data access layer
│   └── migrations/                 # Database migrations
│       └── alembic.ini
│
├── devices/                        # Device integration layer
│   ├── __init__.py
│   ├── base_adapter.py             # Abstract device interface
│   ├── identix_k20.py              # identiX K20 adapter
│   ├── generic_adapter.py          # Generic device adapter
│   ├── connection_manager.py       # Device connection handler
│   └── protocols/                  # Communication protocols
│       ├── tcp_handler.py
│       ├── udp_handler.py
│       └── serial_handler.py
│
├── services/                       # Application services
│   ├── __init__.py
│   ├── attendance_service.py       # Attendance operations
│   ├── shift_service.py            # Shift operations
│   ├── leave_service.py            # Leave operations
│   ├── employee_service.py         # Employee operations
│   ├── device_service.py           # Device operations
│   ├── sync_service.py             # Data synchronization
│   └── backup_service.py           # Backup operations
│
├── ui/                             # User interface (Desktop GUI)
│   ├── __init__.py
│   ├── main_window.py              # Main application window
│   ├── dialogs/                    # Dialog windows
│   │   ├── employee_dialog.py
│   │   ├── shift_dialog.py
│   │   ├── leave_dialog.py
│   │   └── device_dialog.py
│   ├── widgets/                    # Reusable UI components
│   │   ├── attendance_table.py
│   │   ├── calendar_widget.py
│   │   └── device_status.py
│   └── resources/                  # UI resources
│       ├── icons/
│       └── styles.qss
│
├── utils/                          # Utility functions
│   ├── __init__.py
│   ├── validators.py               # Data validation
│   ├── formatters.py               # Data formatting
│   ├── encryption.py               # Encryption utilities
│   ├── logger.py                   # Logging configuration
│   └── exceptions.py               # Custom exceptions
│
├── api/                            # Internal API layer (optional)
│   ├── __init__.py
│   ├── local_api.py                # Local REST API for integrations
│   └── endpoints/                  # API endpoints
│       ├── attendance.py
│       ├── employees.py
│       └── reports.py
│
├── tasks/                          # Background tasks
│   ├── __init__.py
│   ├── scheduler.py                # Task scheduler
│   ├── backup_task.py              # Automated backups
│   ├── sync_task.py                # Device synchronization
│   └── notification_task.py        # Notifications
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── test_core/
│   ├── test_services/
│   ├── test_devices/
│   └── test_database/
│
├── data/                           # Application data
│   ├── backups/                    # Database backups
│   ├── logs/                       # Application logs
│   ├── exports/                    # Exported reports
│   └── cache/                      # Temporary cache
│
├── docs/                           # Documentation
│   ├── API.md                      # API documentation
│   ├── DATABASE_SCHEMA.md          # Database schema
│   ├── DEVICE_INTEGRATION.md       # Device integration guide
│   ├── DEPLOYMENT.md               # Deployment guide
│   └── USER_MANUAL.md              # User manual
│
└── scripts/                        # Utility scripts
    ├── setup_db.py                 # Database initialization
    ├── migrate_data.py             # Data migration
    ├── backup_restore.py           # Backup/restore utilities
    └── device_discovery.py         # Network device discovery
```

---

## Technology Stack

### Core Technologies
- **Python 3.11+** - Main programming language
- **PyQt6 / PySide6** - Desktop GUI framework (recommended)
- **SQLAlchemy 2.0+** - ORM for database abstraction
- **Alembic** - Database migrations
- **APScheduler** - Task scheduling
- **python-dotenv** - Environment configuration

### Database Support
- PostgreSQL
- MySQL / MariaDB
- Microsoft SQL Server
- Oracle Database
- SQLite (for development/testing)

### Additional Libraries
- **cryptography** - Data encryption
- **pyserial** - Serial communication
- **asyncio** - Async operations
- **pandas** - Data processing
- **reportlab** - PDF generation
- **openpyxl** - Excel export
- **requests** - HTTP communication

---

## Configuration Management

### config.py Structure
```python
# Database configurations
DATABASE_CONFIGS = {
    'postgresql': 'postgresql://user:pass@host:port/dbname',
    'mysql': 'mysql+pymysql://user:pass@host:port/dbname',
    'mssql': 'mssql+pyodbc://user:pass@host:port/dbname?driver=...',
    'oracle': 'oracle+cx_oracle://user:pass@host:port/dbname',
    'sqlite': 'sqlite:///data/timetracker.db'
}

# Device configurations
DEVICE_CONFIGS = {
    'scan_interval': 5,              # seconds
    'connection_timeout': 30,         # seconds
    'max_retry_attempts': 3,
    'supported_protocols': ['tcp', 'udp', 'serial']
}

# Backup configurations
BACKUP_CONFIGS = {
    'auto_backup': True,
    'backup_interval': 'daily',       # daily, weekly, monthly
    'backup_time': '02:00',          # HH:MM format
    'retention_days': 30,
    'backup_location': 'data/backups/'
}

# Application settings
APP_CONFIGS = {
    'max_concurrent_devices': 50,
    'session_timeout': 3600,          # seconds
    'cache_enabled': True,
    'log_level': 'INFO'
}
```

---

## Core Components Overview

### 1. Database Layer
- **Connection Manager**: Handles database connections with connection pooling
- **Models**: SQLAlchemy models for all entities
- **Repositories**: Data access patterns for CRUD operations
- **Migrations**: Version-controlled schema changes

### 2. Device Integration Layer
- **Base Adapter**: Abstract interface all device adapters must implement
- **Device-Specific Adapters**: Implementation for each device type
- **Connection Manager**: Manages multiple concurrent device connections
- **Protocol Handlers**: TCP, UDP, Serial communication protocols

### 3. Business Logic Layer (Core)
- **Attendance Module**: Clock-in/out processing, validation, calculations
- **Shift Module**: Shift creation, assignment, rotation logic
- **Leave Module**: Leave requests, approvals, balance management
- **Employee Module**: Employee data management

### 4. Service Layer
- **Orchestration**: Coordinates between core logic, database, and devices
- **Business Rules**: Enforces policies and validations
- **Transaction Management**: Ensures data consistency
- **Error Handling**: Centralized error management

### 5. UI Layer (Desktop)
- **Main Window**: Primary application interface
- **Dialogs**: Modal windows for data entry
- **Widgets**: Reusable UI components
- **Resource Management**: Icons, styles, themes

### 6. Background Tasks
- **Scheduler**: Manages periodic tasks
- **Backup Task**: Automated database backups
- **Sync Task**: Device data synchronization
- **Notification Task**: Alerts and reminders

---

## Key Features Implementation

### Multi-Device Support
- Concurrent connection handling with asyncio
- Device pool management
- Automatic reconnection on connection loss
- Device health monitoring
- Load balancing across devices

### Database Abstraction
- Connection string-based configuration
- Automatic dialect detection
- Query optimization per database
- Transaction management
- Connection pooling

### Data Backup
- Scheduled automatic backups
- On-demand manual backups
- Incremental and full backup support
- Backup verification
- Point-in-time restore
- Backup rotation and cleanup

### Shift Management
- Flexible shift templates
- Fixed and rotating schedules
- Override capabilities
- Conflict detection
- Shift swap requests

### Leave Management
- Multiple leave types (sick, vacation, emergency, urgent)
- Multi-level approval workflow
- Leave balance tracking
- Policy enforcement
- Leave calendar integration

### Network Flexibility
- LAN (wired) support
- WiFi (wireless) support
- Auto-discovery of network devices
- Fallback mechanisms
- Offline mode with sync queue

---

## Deployment Model

### Standalone Desktop Application
- Single executable (PyInstaller/cx_Freeze)
- Embedded database option (SQLite)
- Local data storage
- No internet required

### Client-Server Model (Optional)
- Desktop clients connect to central database
- Shared device pool
- Centralized data management
- Multi-location support

---

## Security Features

- **Authentication**: User login with password hashing
- **Authorization**: Role-based access control (Admin, Manager, Employee)
- **Encryption**: Database connection encryption
- **Audit Trail**: Complete activity logging
- **Data Integrity**: Transaction-based operations
- **Backup Security**: Encrypted backup files

---

## Next Steps

1. Review the detailed implementation documents:
   - `DATABASE_SCHEMA.md` - Complete database design
   - `API.md` - Internal API specifications
   - `DEVICE_INTEGRATION.md` - Device adapter implementation
   
2. Set up development environment
3. Initialize database schema
4. Implement core services
5. Build UI components
6. Test with identiX K20 device
7. Deploy and train users

---

**Note**: This architecture is designed to be scalable, maintainable, and extensible. Each component is loosely coupled to allow for easy testing and future enhancements.
