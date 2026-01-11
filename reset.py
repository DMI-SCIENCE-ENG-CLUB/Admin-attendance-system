from zk import ZK, const
import json
import os

# Load IP from settings
settings_file = os.path.join(os.path.dirname(__file__), 'settings.json')
if os.path.exists(settings_file):
    with open(settings_file, 'r') as f:
        settings = json.load(f)
        ip = settings.get('device_ip', '192.168.1.198')
else:
    ip = '192.168.1.198'

conn = None
# create ZK instance
zk = ZK(ip, port=4370, timeout=5, password=0, force_udp=False, ommit_ping=False)

conn = zk.connect()

conn.clear_data()