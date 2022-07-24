import enum
from typing import List, Tuple, Dict
import time
import datetime
import threading
import asyncio
import socket

import psycopg2
import psutil


async def wait_until_time_passed(duration: float, start: float) -> bool:
    delta = time.time() - start
    if delta < duration:
        await asyncio.sleep(duration-delta)
        return True
    return False


last_network_tx: List[int] | None = None
last_network_rx: List[int] | None = None

last_disk_reads: List[int] | None = None
last_disk_writs: List[int] | None = None


class MonitorPackageIds(enum.Enum):
    INFO = 0
    UPDATE = 1
    PROBE_LIST = 2


class Sample:
    timestamp: float

    cpu_usage: float
    cpu_usage_per_core: List[float]

    ram_total: float
    swap_total: float
    ram_usage: float
    swap_usage: float

    network_name: List[Tuple[str, str]]
    network_addr: List[str]
    network_rx: List[float]
    network_tx: List[float]

    disk_name: List[Tuple[str, str]]
    disk_size: List[int]
    disk_usage: List[float]
    disk_reads: List[float]
    disk_writs: List[float]

    temp_names: List[str]
    temp: List[float]
    nginx_number_of_clients: int
    nginx_user_list:  List[tuple[str]]

    def get_sample(self, measure_interval, f=0.5, nginx=False):
        self.timestamp = time.time()

        # Getting NGINX stats if enabled
        if nginx:
            pass #TODO: Insert nginx messurement
        else:
            self.nginx_number_of_clients = 0
            self.nginx_user_list = []

        # Create threads for messuring cpu usage
        def sample_cpu_usage_total_thread():
            self.cpu_usage = psutil.cpu_percent(interval=measure_interval*f, percpu=False)

        def sample_cpu_usage_core_thread():
            self.cpu_usage_per_core = psutil.cpu_percent(interval=measure_interval*f, percpu=True)

        cpu_usage_core_thread = threading.Thread(target=sample_cpu_usage_core_thread, daemon=True)
        cpu_usage_total_thread = threading.Thread(target=sample_cpu_usage_total_thread, daemon=True)

        cpu_usage_core_thread.start()
        cpu_usage_total_thread.start()

        # Get Disk data
        global last_disk_writs
        global last_disk_reads

        disk_info = psutil.disk_partitions()

        self.disk_name = [
            (i.device, i.mountpoint) for i in disk_info
            if i.device[:9] != "/dev/loop" and i.mountpoint[:9] != "/boot/efi"
        ]

        self.disk_size = []
        self.disk_usage = []

        disk_operations = psutil.disk_io_counters(perdisk=True, nowrap=True)
        internal_disk_names = []

        for i in self.disk_name:
            usage = psutil.disk_usage(i[1])
            self.disk_size.append(usage.total)
            self.disk_usage.append(usage.percent)

            for j in disk_operations.keys():
                if j == i[0].replace("/dev/", ""):
                    internal_disk_names.append(j)
                    break

        if last_disk_reads is None:
            self.disk_reads = [0 for _ in internal_disk_names]
            last_disk_reads = [disk_operations[i].read_bytes for i in internal_disk_names]
        else:
            self.disk_reads = [
                disk_operations[i].read_bytes for i in internal_disk_names
            ]
            tmp = self.disk_reads.copy()
            self.disk_reads = [
                (self.disk_reads[i] - last_disk_reads[i]) / measure_interval / 1024
                for i, _ in enumerate(internal_disk_names)
            ]
            last_disk_reads = tmp

        if last_disk_writs is None:
            self.disk_writs = [0 for _ in internal_disk_names]
            last_disk_writs = [disk_operations[i].write_bytes for i in internal_disk_names]
        else:
            self.disk_writs = [
                disk_operations[i].write_bytes for i in internal_disk_names
            ]
            tmp = self.disk_writs.copy()
            self.disk_writs = [
                (self.disk_writs[i] - last_disk_writs[i]) / measure_interval / 1024
                for i, _ in enumerate(internal_disk_names)
            ]
            last_disk_writs = tmp

        # Get Network data
        global last_network_rx
        global last_network_tx

        network_info = psutil.net_io_counters(pernic=True)

        self.network_name = [
            (j, i[0].address) for j, i in psutil.net_if_addrs().items()
            if i[0:3] != "br-" and i[0:4] != "veth"
        ]

        if last_network_rx is None:
            self.network_rx = [0 for _ in self.network_name]
            last_network_rx = [network_info[i[0]].bytes_recv for i in self.network_name]
        else:
            self.network_rx = [
                network_info[i[0]].bytes_recv for i in self.network_name
            ]
            tmp = self.network_rx.copy()
            self.network_rx = [
                (self.network_rx[i] - last_network_rx[i]) / measure_interval / 1024
                for i, _ in enumerate(self.network_name)
            ]
            last_network_rx = tmp

        if last_network_tx is None:
            self.network_tx = [0 for _ in self.network_name]
            last_network_tx = [network_info[i[0]].bytes_sent for i in self.network_name]
        else:
            self.network_tx = [
                network_info[i[0]].bytes_sent for i in self.network_name
            ]
            tmp = self.network_tx.copy()
            self.network_tx = [
                (self.network_tx[i] - last_network_tx[i]) / measure_interval / 1024
                for i, _ in enumerate(self.network_name)
            ]
            last_network_tx = tmp

        # Get RAM/SWAP usage
        self.ram_total = psutil.virtual_memory().total
        self.ram_usage = psutil.virtual_memory().percent
        self.swap_total = psutil.swap_memory().total
        self.swap_usage = psutil.swap_memory().percent

        # Get Core temp
        self.temp = []
        self.temp_names = []

        for v, k1 in psutil.sensors_temperatures(fahrenheit=False).items():
            for n, k2 in enumerate(k1):
                self.temp.append(k2.current)
                self.temp_names.append(f"{v}-{n}{'-'+k2.label if k2.label != '' else ''}")

        # Join CPU sample threads
        cpu_usage_total_thread.join()
        cpu_usage_core_thread.join()

    def insert_into_db(self, cursor: psycopg2._psycopg.cursor, session, probe_id):
        cursor.execute("""
        INSERT INTO log(timestamp, session, probe,
        cpu_usage, cpu_usage_per_core, 
        ram_usage, swap_usage, 
        network_tx, network_rx, 
        disk_usage, disk_reads, disk_writs, 
        temperature, user_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (datetime.datetime.fromtimestamp(self.timestamp), session, probe_id,
              self.cpu_usage, self.cpu_usage_per_core,
              self.ram_usage, self.swap_usage,
              self.network_tx, self.network_rx,
              self.disk_usage, self.disk_reads, self.disk_writs,
              self.temp, self.nginx_number_of_clients or 0)
        )


def recv_all(conn: socket.socket, chunk_size=4096):
    data = b""
    while True:
        c = conn.recv(chunk_size)
        data += bytes(c)
        if len(c) < chunk_size:
            break
    return data
