import time
import os
import psycopg2
import psutil
import threading
import signal
import datetime

OS = "win" if os.name == "nt" else "unix"

MEASURE_INTERVAL = 1

BACKLOG_MAX_SIZE = 1000
BACKLOG = []

LOGGING_SESSION_ID = 0
PROBE_ID = 0

DATABASE_NAME = "logging"
DATABASE_USER = "postgres"
DATABASE_PASSWORD = "password"
DATABASE_HOST = "localhost"
DATABASE_PORT = 5432

db_conn: psycopg2._psycopg.connection = None
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
    except psycopg2.InterfaceError:
        pass
    except psycopg2.OperationalError:
        pass


def push_to_backlog(s):
    if len(BACKLOG) < BACKLOG_MAX_SIZE:
        BACKLOG.append(new_sample)
    else:
        print("!WARNING! Dropped Sample because of overflowing Backlog")


def get_disk_info():
    disk_info = {
        i.device: (i.mountpoint, i.fstype, psutil.disk_usage(i.mountpoint).total)
        for i in psutil.disk_partitions(all=False) if i.fstype != "squashfs"
    }
    disk_io_counts = psutil.disk_io_counters(perdisk=True, nowrap=True)
    return disk_info, {
            i: psutil.disk_usage(j[0]).percent for i, j in disk_info.items()
        }, {
            i: disk_io_counts[
                i.replace("/dev/", "") if OS == "unix" else i
            ].write_bytes
            for i, j in disk_info.items()
        }, {
            i: disk_io_counts[
                i.replace("/dev/", "") if OS == "unix" else i
            ].read_bytes
            for i, j in disk_info.items()
        }


def get_network_info():
    network_state = psutil.net_if_stats()
    network_info = {
        i: (network_state[i].isup, j[0].address, j[1].address)
        for i, j in psutil.net_if_addrs().items() if i[:3] != "br-" and i[:4] != "veth"
    }
    network_io_counts = psutil.net_io_counters(pernic=True, nowrap=True)
    return network_info, {
        i: network_io_counts[i].bytes_sent
        for i in network_info.keys()
    }, {
        i: network_io_counts[i].bytes_recv
        for i in network_info.keys()
    }


init_disk_info, init_disk_usage, init_disk_writs, init_disk_reads = get_disk_info()
init_network_info, init_network_sent, init_network_recv = get_network_info()


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
    disk_usage: dict[str, float]
    disk_reads: dict[str, float]
    disk_writs: dict[str, float]

    network_info: dict[str, bool]
    network_tx: dict[str, float]
    network_rx: dict[str, float]

    temp: dict[str, float]
    fan: dict[str, float]
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
        self.network_info, self.network_tx, self.network_rx = get_network_info()

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

        for i in init_disk_info.keys():
            self.disk_writs[i] = (self.disk_writs[i]-old_init_disk_writs[i]) / MEASURE_INTERVAL / 1024 / 2
            self.disk_reads[i] = (self.disk_reads[i]-old_init_disk_reads[i]) / MEASURE_INTERVAL / 1024 / 2

        for i in init_network_info.keys():
            self.network_tx[i] = (self.network_tx[i] - old_init_network_sent[i]) / MEASURE_INTERVAL / 1024 / 2
            self.network_rx[i] = (self.network_rx[i] - old_init_network_recv[i]) / MEASURE_INTERVAL / 1024 / 2

        self.cpu_freq_total = psutil.cpu_freq(percpu=False).current
        self.cpu_freq_per_core = [i.current for i in psutil.cpu_freq(percpu=True)]

        self.memory_total = psutil.virtual_memory().total
        self.memory_used = psutil.virtual_memory().percent
        self.swap_total = psutil.swap_memory().total
        self.swap_used = psutil.swap_memory().percent

        self.temp = {}
        for i, j in psutil.sensors_temperatures(fahrenheit=False).items():
            for n, k in enumerate(j):
                self.temp.update({
                    f"{i}-{n}{'-'+k.label if k.label != '' else ''}": k.current
                })

        self.fan = {}
        for i, j in psutil.sensors_fans().items():
            for n, k in enumerate(j):
                self.fan.update({
                    f"{i}-{n}{'-'+k.label if k.label != '' else ''}": k.current
                })

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
            battery,
            memory_used, swap_used, disk_usage, disk_reads, disk_writs,
            network_online, network_rx, network_tx, temp, fan
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                LOGGING_SESSION_ID, PROBE_ID, datetime.datetime.fromtimestamp(self.timestamp),
                self.cpu_usage_total, self.cpu_freq_total, self.cpu_usage_per_core, self.cpu_freq_per_core,
                self.memory_used, self.swap_used, self.battery,
                list(self.disk_usage.values()), list(self.disk_reads.values()),
                list(self.disk_writs.values()),
                [i[0] for i in self.network_info.values()],
                list(self.network_rx.values()),
                list(self.network_tx.values()),
                list(self.temp.values()),
                list(self.fan.values())
            ))
            conn.commit()
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            push_to_backlog(self)

    def initial_write_to_db(self, conn: psycopg2._psycopg.connection):
        cur: psycopg2._psycopg.cursor = conn.cursor()
        cur.execute("""
        UPDATE probes
        SET memory_total = %s, swap_total = %s, cpu_cors = %s,
        disks_names = %s, disks_fstype = %s, disks_mountpoint = %s, disks_size = %s,
        network_names = %s, ipv4 = %s, ipv6 = %s, temp_sensor_names = %s, fan_names = %s
        WHERE id = %s;
        """, (
            self.memory_total, self.swap_total, len(self.cpu_usage_per_core),
            list(self.disk_info.keys()),
            [self.disk_info[i][0] for i in self.disk_info.keys()],
            [self.disk_info[i][1] for i in self.disk_info.keys()],
            [self.disk_info[i][2] for i in self.disk_info.keys()],
            list(self.network_info.keys()),
            [i[1] for i in self.network_info.values()],
            [i[2] for i in self.network_info.values()],
            list(self.temp.keys()), list(self.fan.keys()),
            PROBE_ID
        ))


connect_to_db()

new_sample = Sample()
new_sample.get_sample()
new_sample.initial_write_to_db(db_conn)

reconnection_thread = threading.Thread(target=connect_to_db, daemon=True)

while True:
    start = time.time()
    new_sample = Sample()
    new_sample.get_sample()

    connection_working = True
    try:
        db_conn.cursor().execute("SELECT 1 WHERE 1 = 1")
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        connection_working = False
        if not reconnection_thread.is_alive():
            reconnection_thread = threading.Thread(target=connect_to_db, daemon=True)
            reconnection_thread.start()

    if connection_working:
        cursor = db_conn.cursor()
        if len(BACKLOG) > 0:
            BACKLOG.append(new_sample)
            for i in range(min(len(BACKLOG), 5)):
                sample = BACKLOG[0]
                BACKLOG = BACKLOG[1:]
                sample.write_to_db(db_conn)
            print(f"Poping of backlog: {len(BACKLOG)}/{BACKLOG_MAX_SIZE} Samples in backlog")
        else:
            new_sample.write_to_db(db_conn)
    else:
        print(f"Connection Error; Building up backlog: {len(BACKLOG)}/{BACKLOG_MAX_SIZE} Samples in backlog")
        push_to_backlog(new_sample)

    delta_time = time.time() - start
    if round(delta_time, 1) > MEASURE_INTERVAL:
        print("!WARNING! Measure interval is not meet!")
    else:
        time.sleep(MEASURE_INTERVAL - round(delta_time, 1))
    print(time.time()-start)
