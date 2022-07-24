import socket
import threading
import time
from typing import Tuple, List, Dict
import pickle
import uuid
import traceback

import psycopg2

from backend_config import config
import util
from util import recv_all

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 1337  # Port to listen on (non-privileged ports are > 1023)

SESSION = 1

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((HOST, PORT))
sock.listen()
sock.settimeout(config.TIMEOUT)

db_conn: psycopg2._psycopg.connection = psycopg2.connect(
    host=config.DB_HOST,
    port=config.DB_PORT,
    database=config.DB_DATABASE,
    user=config.DB_USER,
    password=config.DB_PASSWORD
)


class Client_Info:
    sock: socket.socket
    thread: threading.Thread
    addr: Tuple[str, int]
    type: str = "undefined"
    sub_session_id: int = -1
    sub_probe_id: int = -1

    def __init__(self, sock_: socket.socket, thread_: threading.Thread, addr_: Tuple[str, int]):
        self.sock = sock_
        self.thread = thread_
        self.addr = addr_


thread_table: Dict[uuid.UUID, Client_Info] = {}


def _handle_client(address: Tuple[str, int], c: socket.socket, identifier: uuid.UUID):
    cursor: psycopg2._psycopg.cursor = db_conn.cursor()
    try:
        handle_client(address, c, identifier, cursor)
    except Exception as e:
        traceback.print_exc()
    finally:
        try:
            c.close()
        except Exception as e:
            pass
        cursor.close()
        db_conn.reset()
        del thread_table[identifier]


def handle_client(
        address: Tuple[str, int], c: socket.socket,
        identifier: uuid.UUID, cursor: psycopg2._psycopg.cursor):
    try:
        client_type = recv_all(c)
        c.sendall(b"ok")
        if client_type == b"probe":
            thread_table[identifier].type = "probe"
            probe_id = int.from_bytes(recv_all(c), "big")
            c.sendall(b"ok")

            try:
                while True:
                    data = recv_all(c)
                    if len(data) <= 0:
                        return
                    s: util.Sample = pickle.loads(data)
                    s.insert_into_db(cursor, SESSION, probe_id)
                    broadcast_sample(s)
                    db_conn.commit()
            except BrokenPipeError or TimeoutError:
                pass

        elif client_type == b"monitor":
            thread_table[identifier].type = "monitor"
            while True:
                data = recv_all(c)
                if len(data) <= 0:
                    request_id = data[0]
    except KeyError:
        return


def broadcast_sample(s: util.Sample):
    for k, v in thread_table.items():
        if v.type == "monitor":
            try:
                v.sock.sendall(int.to_bytes(util.MonitorPackageIds.UPDATE.value, 1, "big") + pickle.dumps(s))
            except BrokenPipeError:
                v.sock.close()


try:
    while True:
        try:
            conn, addr = sock.accept()

            if len(thread_table) >= config.MAX_CLIENTS:
                continue

            thread_id = uuid.uuid4()

            thread = threading.Thread(target=_handle_client, args=(addr, conn, thread_id))
            thread.daemon = True
            thread.start()
            new_client_info = Client_Info(conn, thread, addr)
            thread_table.update({thread_id: new_client_info})

        except TimeoutError:
            pass

except KeyboardInterrupt:
    pass
