from zk import ZK, const

conn = None
# create ZK instance
zk = ZK('192.168.1.198', port=4370, timeout=5, password=0, force_udp=False, ommit_ping=False)
try:
    conn = zk.connect()

    conn.test_voice(1)
    conn.disconnect()
except Exception as e:
    print ("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect