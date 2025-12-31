from functools import partial

from zk import ZK, const
import tkinter as tk
conn = None
# create ZK instance
zk = ZK('192.168.1.198', port=4370, timeout=5, password=0, force_udp=False, ommit_ping=False)

root = tk.Tk()
root.title("ETime Bomboclaat")
root.geometry("600x600")

def connect(con):
    # try:
    #     # connect to device
    #     con = zk.connect()
    #     # users = zk.get_users()
    #
    # except Exception as e:
    #     print ("Process terminate : {}".format(e))
    # finally:
    #     if conn:
    #         con.disconnect()
    con = zk.connect()
    con.test_voice(2)
    attendance = con.get_attendance()
    # for e in attendance:
    #     print(e)
    print(attendance[0])



# connect(conn)

btn = tk.Button(root, text="Bomboclaat Connect", command= partial(connect, conn))
btn.pack(pady=20, padx=20)

if __name__ == '__main__':
    root.mainloop()