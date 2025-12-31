
from abc import ABC, abstractmethod

class BaseDeviceAdapter(ABC):
    def __init__(self, ip_address, port=4370, timeout=10, password=0):
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout
        self.password = password
        self.connected = False

    @abstractmethod
    def connect(self):
        """Connect to the device."""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the device."""
        pass

    @abstractmethod
    def get_users(self):
        """Get all users from the device."""
        pass

    @abstractmethod
    def get_attendance(self):
        """Get attendance records."""
        pass

    @abstractmethod
    def clear_attendance(self):
        """Clear attendance records."""
        pass

    @abstractmethod
    def set_user(self, uid, name, privilege, password, group_id, user_id, card):
        """Set/Create a user on the device."""
        pass

    @abstractmethod
    def delete_user(self, uid, user_id):
        """Delete a user from the device."""
        pass
