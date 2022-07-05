CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

DROP TABLE IF EXISTS logging_sessions CASCADE;
DROP TABLE IF EXISTS probe_entries CASCADE;
DROP TABLE IF EXISTS probes CASCADE;

CREATE TABLE probes (
    id serial primary key,
    name varchar(256),
    memory_total bigint,
    swap_total bigint,
    cpu_cors int,

    disks_names varchar(64)[32],
    disks_mountpoint varchar(64)[32],
    disks_fstype varchar(64)[32],
    disks_size bigint[32],

    ipv4 varchar(20)[32],
    ipv6 varchar(50)[32],

    temp_sensor_names varchar(64)[64],
    fan_names varchar(64)[32],

    network_names varchar(64)[32]
);

CREATE TABLE logging_sessions (
    id serial primary key,
    name varchar(256),
    creation_date timestamp default current_timestamp
);

CREATE TABLE probe_entries (
    id serial primary key,
    log_session serial not null,
    probe serial not null,
    timestamp timestamp,

    cpu_usage_total real,
    cpu_freq_total real,
    cpu_usage_per_core real[32],
    cpu_freq_per_core real[32],

    disk_usage real[32],
    disk_reads real[32],
    disk_writs real[32],

    network_online bool[32],
    network_rx real[32],
    network_tx real[32],

    temp real[64],
    fan real[64],

    memory_used real,
    swap_used real,
    battery real,

    foreign key (log_session) REFERENCES logging_sessions(id),
    foreign key (probe) REFERENCES probes(id)
);

INSERT INTO logging_sessions (id, name) VALUES (0, 'Dev-Session');
INSERT INTO probes (id, name) VALUES (0, 'Dev-Probe');