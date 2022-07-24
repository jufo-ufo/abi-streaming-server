import asyncio
import enum

import util
from util import recv_all

import time
import threading
import socket

import tkinter as tk
import sv_ttk


class NetworkStats(enum.Enum):
    offline = "offline"
    connecting_1 = "connecting..."
    online = "online"


network_status: NetworkStats = NetworkStats.offline
conn: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
reconnection_thread: threading.Thread

LOG_SESSION = 1
PROBE = 1


def change_network_status(new_state: NetworkStats):
    global network_status
    old_state = network_status
    network_status = new_state
    on_network_status_change(old_state, new_state)


def reconnect():
    global conn
    change_network_status(NetworkStats.connecting_1)

    while True:
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.settimeout(5)
            conn.connect(("localhost", 1337))
            conn.sendall(b"monitor")
            recv_all(conn)
            conn.sendall(b"monitor")
            change_network_status(NetworkStats.online)
            return
        except ConnectionRefusedError or ConnectionError:
            time.sleep(0.5)


def launch_reconnect():
    global reconnection_thread
    if network_status == NetworkStats.offline:
        reconnect_thread = threading.Thread(target=reconnect)
        reconnect_thread.daemon = True
        reconnect_thread.start()


class App(tk.Tk):

    def __init__(self, loop, interval=1/60):
        super().__init__()
        self.running = True
        sv_ttk.use_dark_theme()

        self.loop = loop
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.tasks = []
        self.tasks.append(self.loop.create_task(self.updater(interval)))
        self.tasks.append(self.loop.create_task(self.on_start()))

    def on_message(self):
        pass

    def handle_connection(self):
        global conn

        if conn is None:
            launch_reconnect()
            return

        try:
            while self.running:
                data = recv_all(conn)
                if len(data) <= 0:
                    raise BrokenPipeError
                elif data == b"ping":
                    conn.sendall(b"pong")
                print(data[0])

        except (BrokenPipeError, TimeoutError):
            change_network_status(NetworkStats.offline)
            launch_reconnect()
            pass

    async def on_start(self):
        launch_reconnect()

    async def updater(self, interval):
        while True:
            self.update()
            await asyncio.sleep(interval)

    def close(self):
        if conn is not None:
            conn.close()
        self.running = False
        for task in self.tasks:
            task.cancel()
        self.loop.stop()
        self.destroy()


loop = asyncio.get_event_loop()
app = App(loop)


connection_thread: threading.Thread


def on_network_status_change(old: NetworkStats, new: NetworkStats):
    global connection_thread

    print(old, "->", new)

    if new == NetworkStats.online:
        connection_thread = threading.Thread(target=app.handle_connection, args=())
        connection_thread.daemon = True
        connection_thread.start()


loop.run_forever()
loop.close()
