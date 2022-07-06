import time
import os
import psycopg2
import psutil
import threading
import signal
import datetime
from typing import Tuple, List, Dict

# Global Variables for Config Stuff
OS = "win" if os.name == "nt" else "unix"

MEASURE_INTERVAL = 1

BACKLOG_MAX_SIZE = 1000
BACKLOG = []

DB_CONNECTION_ALIVE = True

LOGGING_SESSION_ID = 0
PROBE_ID = 0

DATABASE_NAME = "logging"
DATABASE_USER = "postgres"
DATABASE_PASSWORD = "password"
DATABASE_HOST = "localhost"
DATABASE_PORT = 5432

# Connecting to database
db_conn: psycopg2._psycopg.connection = None
# Creating signal handlers for SIGINT, SIGTERM to close db connection proper
signal.signal(signal.SIGINT, lambda: db_conn.close())
signal.signal(signal.SIGTERM, lambda: db_conn.close())


def connect_to_db():
    global db_conn
    try:
        db_conn = psycopg2.connect(
            dbname=DATABASE_NAME,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            host=DATABASE_HOST,
            port=DATABASE_PORT
        )
    except (psycopg2.InterfaceError, psycopg2.OperationalError):
        pass


def push_to_backlog(s):
    if len(BACKLOG) < BACKLOG_MAX_SIZE:
        BACKLOG.append(s)
    else:
        print("!WARNING! Dropped Sample because of overflowing Backlog")


# Reads Disk info in the following manner: disk_info, io_counts_write, ic_counts_read
def get_disk_info() -> Tuple[Dict, List, List, List]:
    disk_info = {
        disk.device: (disk.mountpoint, disk.fstype, psutil.disk_usage(disk.mountpoint).total)
        for disk in psutil.disk_partitions(all=False) if disk.fstype != "squashfs"
    }
    disk_io_counts = psutil.disk_io_counters(perdisk=True, nowrap=True)
    return disk_info, \
        [psutil.disk_usage(v[0]).percent for _, v in disk_info.items()], \
        [disk_io_counts[k.replace("/dev/", "") if OS == "unix" else k].write_bytes for k, _ in disk_info.items()], \
        [disk_io_counts[k.replace("/dev/", "") if OS == "unix" else k].read_bytes for k, _ in disk_info.items()]


# Reads Network info in the following manner: network_info, bytes_send, bytes_recv
def get_network_info() -> Tuple[Dict, List, List, List]:
    network_state = psutil.net_if_stats()
    network_info = {
        network_name: (j[0].address, j[1].address)
        for network_name, j in psutil.net_if_addrs().items()
        if network_name[:3] != "br-" and network_name[:4] != "veth"
    }
    network_io_counts = psutil.net_io_counters(pernic=True, nowrap=True)
    return network_info, \
        [network_state[network_name].isup for network_name in network_info.keys()], \
        [network_io_counts[network_name].bytes_sent for network_name in network_info.keys()], \
        [network_io_counts[network_name].bytes_recv for network_name in network_info.keys()]


# Getting Initial Values for measurement
init_disk_info, init_disk_usage, init_disk_writs, init_disk_reads = get_disk_info()
init_network_info, _, init_network_sent, init_network_recv = get_network_info()


# Class for holding information about a taken Sample
class Sample:
    timestamp: float

    cpu_usage_total: float
    cpu_freq_total: float
    cpu_usage_per_core: list[float]
    cpu_freq_per_core: list[float]

    memory_total: float
    memory_used: float
    swap_total: float
    swap_used: float

    disk_info: dict[str, tuple[str, str, int]]
    disk_usage: List[float]
    disk_reads: List[float]
    disk_writs: List[float]

    network_addresses: Dict[str, bool]
    network_status: List[bool]
    network_tx: List[float]
    network_rx: List[float]

    temp_names: List[str]
    temp: List[float]
    fan_names: List[str]
    fan: List[float]

    battery: float

    def get_sample(self):
        self.timestamp = time.time()

        def sample_disk_usage_total():
            self.cpu_usage_total = psutil.cpu_percent(interval=MEASURE_INTERVAL*0.5, percpu=False)

        def sample_disk_usage_per_core():
            self.cpu_usage_per_core = psutil.cpu_percent(interval=MEASURE_INTERVAL*0.5, percpu=True)

        cpu_usage_total_thread = threading.Thread(target=sample_disk_usage_total, daemon=True)
        cpu_usage_core_thread = threading.Thread(target=sample_disk_usage_per_core, daemon=True)

        cpu_usage_core_thread.start()
        cpu_usage_total_thread.start()

        self.disk_info, self.disk_usage, self.disk_writs, self.disk_reads = get_disk_info()
        self.network_addresses, self.network_status, self.network_tx, self.network_rx = get_network_info()

        global init_disk_writs
        global init_disk_reads
        global init_network_sent
        global init_network_recv

        old_init_disk_writs = init_disk_writs.copy()
        old_init_disk_reads = init_disk_reads.copy()
        old_init_network_sent = init_network_sent.copy()
        old_init_network_recv = init_network_recv.copy()
        init_disk_writs = self.disk_writs.copy()
        init_disk_reads = self.disk_reads.copy()
        init_network_sent = self.network_tx.copy()
        init_network_recv = self.network_rx.copy()

        for i, _ in enumerate(init_disk_writs):
            self.disk_writs[i] = (self.disk_writs[i]-old_init_disk_writs[i]) / MEASURE_INTERVAL / 1024 / 2
            self.disk_reads[i] = (self.disk_reads[i]-old_init_disk_reads[i]) / MEASURE_INTERVAL / 1024 / 2

        for i, _ in enumerate(init_network_sent):
            self.network_tx[i] = (self.network_tx[i]-old_init_network_sent[i]) / MEASURE_INTERVAL / 1024 / 2
            self.network_rx[i] = (self.network_rx[i]-old_init_network_recv[i]) / MEASURE_INTERVAL / 1024 / 2

        self.cpu_freq_total = psutil.cpu_freq(percpu=False).current
        self.cpu_freq_per_core = [i.current for i in psutil.cpu_freq(percpu=True)]

        self.memory_total = psutil.virtual_memory().total
        self.memory_used = psutil.virtual_memory().percent
        self.swap_total = psutil.swap_memory().total
        self.swap_used = psutil.swap_memory().percent

        self.temp = []
        self.temp_names = []
        self.fan = []
        self.fan_names = []

        for v, k1 in psutil.sensors_temperatures(fahrenheit=False).items():
            for n, k2 in enumerate(k1):
                self.temp.append(k2.current)
                self.temp_names.append(f"{v}-{n}{'-'+k2.label if k2.label != '' else ''}")

        for v, k1 in psutil.sensors_fans().items():
            for n, k2 in enumerate(k1):
                self.fan.append(k2.current)
                self.fan_names.append(f"{v}-{n}{'-'+k2.label if k2.label != '' else ''}")

        battery = psutil.sensors_battery()
        self.battery = battery.percent if battery is not None else 1

        cpu_usage_total_thread.join()
        cpu_usage_core_thread.join()

    def write_to_db(self, conn: psycopg2._psycopg.connection):
        try:
            cur: psycopg2._psycopg.cursor = conn.cursor()
            cur.execute("""
            INSERT INTO probe_entries (
            log_session, probe, timestamp, 
            cpu_usage_total, cpu_freq_total, cpu_usage_per_core, cpu_freq_per_core,
            memory_used, swap_used, battery,
            disk_usage, disk_reads, disk_writs,
            network_online, network_rx, network_tx, temp, fan
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                LOGGING_SESSION_ID, PROBE_ID, datetime.datetime.fromtimestamp(self.timestamp),
                self.cpu_usage_total, self.cpu_freq_total, self.cpu_usage_per_core, self.cpu_freq_per_core,
                self.memory_used, self.swap_used, self.battery,
                self.disk_usage, self.disk_reads, self.disk_writs,
                self.network_status, self.network_rx, self.network_tx, self.temp, self.fan
            ))
            conn.commit()
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            global DB_CONNECTION_ALIVE
            DB_CONNECTION_ALIVE = False
            push_to_backlog(self)

    # This for initially setting all of static values that do not change like cpu core count
    def initial_write_to_db(self, conn: psycopg2._psycopg.connection):
        cur: psycopg2._psycopg.cursor = conn.cursor()
        cur.execute("""
        UPDATE probes
        SET 
        memory_total = %s, swap_total = %s, cpu_cors = %s,
        disks_names = %s, 
        disks_fstype = %s, 
        disks_mountpoint = %s, 
        disks_size = %s,
        network_names = %s, 
        ipv4 = %s, ipv6 = %s, 
        temp_sensor_names = %s, fan_names = %s
        WHERE id = %s;
        """, (
            self.memory_total, self.swap_total, len(self.cpu_usage_per_core),
            list(self.disk_info.keys()),
            [self.disk_info[i][0] for i in self.disk_info.keys()],
            [self.disk_info[i][1] for i in self.disk_info.keys()],
            [self.disk_info[i][2] for i in self.disk_info.keys()],
            list(self.network_addresses.keys()),
            [addr[0] for addr in self.network_addresses], [addr[1] for addr in self.network_addresses],
            self.temp_names, self.fan_names,
            PROBE_ID
        ))


connect_to_db()

# Taking the first sample to get initial values and setting timing for network and disk
new_sample = Sample()
new_sample.get_sample()
new_sample.initial_write_to_db(db_conn)
time.sleep(MEASURE_INTERVAL)

# Creating Thread-object, for handling reconnecting stuff
reconnection_thread = threading.Thread(target=connect_to_db, daemon=True)

while True:
    start = time.time()
    new_sample = Sample()
    new_sample.get_sample()

    # Testing DB_Connection with simple query
    try:
        if not DB_CONNECTION_ALIVE:  # ...but only if any db write failed
            db_conn.cursor().execute("SELECT 1 WHERE 1 = 1")
            DB_CONNECTION_ALIVE = True
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        DB_CONNECTION_ALIVE = False
        # And if the connection is not working and the reconnection Thread isn't stated...
        if not reconnection_thread.is_alive():
            reconnection_thread = threading.Thread(target=connect_to_db, daemon=True)
            reconnection_thread.start()  # ...start the little bugger up and hope for the best!

    if DB_CONNECTION_ALIVE:
        cursor = db_conn.cursor()
        if len(BACKLOG) > 0:  # If any old backlog exists, it will be popped of her
            BACKLOG.append(new_sample)
            for _ in range(min(len(BACKLOG), 5)):
                sample = BACKLOG[0]
                BACKLOG = BACKLOG[1:]
                sample.write_to_db(db_conn)
            print(f"Popping of backlog: {len(BACKLOG)}/{BACKLOG_MAX_SIZE} Samples in backlog")
        else:
            # Usually the Sample is writen directly to database
            new_sample.write_to_db(db_conn)
    else:
        # Creating backlog if the connection is dead
        print(f"Connection Error; Building up backlog: {len(BACKLOG)}/{BACKLOG_MAX_SIZE} Samples in backlog")
        push_to_backlog(new_sample)

    # Measuring passed time and sleeping accordingly to match the measure interval
    delta_time = time.time() - start
    if round(delta_time, 1) > MEASURE_INTERVAL:
        print("!WARNING! Measure interval is not meet!")
    else:
        time.sleep(MEASURE_INTERVAL - round(delta_time, 1))
    print(time.time()-start)
