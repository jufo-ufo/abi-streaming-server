from probe_config import config
import util

import time
import sys
import asyncio
import threading
import socket
import pickle

loop = asyncio.get_event_loop()

conn: socket.socket
backlog = []

reconnecting = False
reconnect_thread: threading.Thread
data_send_thread: threading.Thread


def reconnect():
    global conn
    global reconnecting
    reconnecting = True
    while True:
        try:
            conn = socket.create_connection((config.API_HOST, config.API_PORT))
            conn.sendall(b"probe")
            conn.recv(16)
            conn.sendall(config.PROBE_ID.to_bytes(4, "big"))
            conn.recv(16)

            reconnecting = False
            return
        except ConnectionRefusedError or ConnectionError:
            time.sleep(0.5)


def launch_reconnect():
    global reconnect_thread
    if not reconnecting:
        reconnect_thread = threading.Thread(target=reconnect)
        reconnect_thread.daemon = True
        reconnect_thread.start()


def send_data(s: util.Sample):
    data = pickle.dumps(s)

    try:
        if reconnecting:
            raise BrokenPipeError

        conn.send(data)
    except BrokenPipeError:
        launch_reconnect()

        if len(backlog) < config.BACKLOG_MAX_SIZE:
            backlog.append(data)
            print(f"Connection to Server broken: filling backlog ({len(backlog)}/{config.BACKLOG_MAX_SIZE})",
                  file=sys.stderr)
        else:
            print("Reached max backlog: dropping...", file=sys.stderr)
        return

    popping = len(backlog) > 0

    for i in range(min(5, len(backlog))):
        try:
            data = backlog[0]
            conn.send(data)
            backlog.pop(0)
        except BrokenPipeError:
            launch_reconnect()
            print(f"Failed popping backlog ({len(backlog)}/{config.BACKLOG_MAX_SIZE})")
            break

    if popping:
        print(f"Popping backlog ({len(backlog)}/{config.BACKLOG_MAX_SIZE})")


async def main():
    reconnect()

    s = util.Sample()
    s.get_sample(1)

    while True:
        start = time.time()

        s = util.Sample()
        s.get_sample(config.MEASURE_INTERVAL, nginx=config.NGINX_ENABLED)
        data_send_thread = threading.Thread(target=send_data, args=(s,))
        data_send_thread.daemon = True
        data_send_thread.start()

        res = await util.wait_until_time_passed(config.MEASURE_INTERVAL, start)
        if not res:
            print("Can't keep up!", file=sys.stderr)

loop.run_until_complete(main())
