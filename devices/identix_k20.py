
from zk import ZK, const
from devices.base_adapter import BaseDeviceAdapter
import logging

logger = logging.getLogger(__name__)

class IdentiXK20Adapter(BaseDeviceAdapter):
    def __init__(self, ip_address, port=4370, timeout=10, password=0):
        super().__init__(ip_address, port, timeout, password)
        self.zk = ZK(
            ip_address, 
            port=port, 
            timeout=timeout, 
            password=password, 
            force_udp=False, 
            ommit_ping=False
        )
        self.conn = None

    def connect(self):
        try:
            logger.info(f"Connecting to K20 device at {self.ip_address}:{self.port}")
            self.conn = self.zk.connect()
            self.connected = True
            logger.info("Connected successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to K20 device: {e}")
            self.connected = False
            return False

    def disconnect(self):
        if self.conn:
            try:
                self.conn.disconnect()
                logger.info("Disconnected from K20 device")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
        self.connected = False
        self.conn = None

    def enable_device(self):
        if self.conn:
            self.conn.enable_device()

    def disable_device(self):
        if self.conn:
            self.conn.disable_device()

    def get_users(self):
        if not self.conn:
            return []
        try:
            self.disable_device()
            users = self.conn.get_users()
            self.enable_device()
            return users
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []

    def get_attendance(self):
        if not self.conn:
            return []
        try:
            self.disable_device()
            records = self.conn.get_attendance()
            self.enable_device()
            return records
        except Exception as e:
            logger.error(f"Error getting attendance: {e}")
            return []

    def clear_attendance(self):
        if not self.conn:
            return False
        try:
            self.disable_device()
            self.conn.clear_attendance()
            self.enable_device()
            return True
        except Exception as e:
            logger.error(f"Error clearing attendance: {e}")
            return False

    def set_user(self, uid, name, privilege=0, password='', group_id='', user_id='', card=0):
        if not self.conn:
            return False
        try:
            self.disable_device()
            self.conn.set_user(
                uid=uid,
                name=name,
                privilege=privilege,
                password=password,
                group_id=group_id,
                user_id=user_id,
                card=card
            )
            self.enable_device()
            return True
        except Exception as e:
            logger.error(f"Error setting user: {e}")
            return False

    def delete_user(self, uid=None, user_id=None):
        if not self.conn:
            return False
        try:
            self.disable_device()
            self.conn.delete_user(uid=uid, user_id=user_id)
            self.enable_device()
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
            
    def get_device_info(self):
        if not self.conn:
            return {}
        try:
            return {
                'firmware': self.conn.get_firmware_version(),
                'serial': self.conn.get_serialnumber(),
                'platform': self.conn.get_platform(),
                'device_name': self.conn.get_device_name(),
                'mac': self.conn.get_mac()
            }
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return {}
