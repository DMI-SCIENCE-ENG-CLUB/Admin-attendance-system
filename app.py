
import logging
import sys
from devices.identix_k20 import IdentiXK20Adapter
from config import DEVICE_CONFIGS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_connection(ip='192.168.1.198'):
    logger.info(f"Attempting to connect to K20 at {ip}...")
    device = IdentiXK20Adapter(ip)
    
    if device.connect():
        logger.info("Connection successful!")
        
        info = device.get_device_info()
        logger.info(f"Device Info: {info}")
        
        users = device.get_users()
        logger.info(f"Found {len(users)} users.")
        
        for user in users[:5]: # Show first 5 users
            logger.info(f"User: {user.name} (UID: {user.uid})")
        
        # Get attendance records
        try:
            records = device.get_attendance()
            logger.info(f"Found {len(records)} attendance records.")
            for rec in records[:5]:
                logger.info(f"Record: UID={getattr(rec, 'user_id', getattr(rec, 'uid', None))}  Time={getattr(rec, 'timestamp', getattr(rec, 'time', None))}  Status={getattr(rec, 'status', '')}")
        except Exception as e:
            logger.error(f"Error fetching attendance: {e}")
            
        device.disconnect()
    else:
        logger.error("Failed to connect.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ip_addr = sys.argv[1]
        test_connection(ip_addr)
    else:
        # Default IP from previous app.py
        test_connection('192.168.1.198')