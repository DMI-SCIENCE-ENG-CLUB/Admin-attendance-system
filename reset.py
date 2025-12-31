from zk import ZK, const

conn = None
# create ZK instance
zk = ZK('192.168.1.198', port=4370, timeout=5, password=0, force_udp=False, ommit_ping=False)

conn = zk.connect()

conn.clear_data()