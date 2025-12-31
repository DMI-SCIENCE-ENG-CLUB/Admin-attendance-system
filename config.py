
# Database configurations
DATABASE_CONFIGS = {
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
