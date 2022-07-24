DROP TABLE IF EXISTS log_sessions CASCADE;
DROP TABLE IF EXISTS log CASCADE;
DROP TABLE IF EXISTS probes CASCADE;

CREATE TABLE log_sessions (
    id serial primary key,
    creation_date timestamp not null default now(),
    name varchar(256)
);

CREATE TABLE probes (
    id serial primary key,
    name varchar(256)
);

CREATE TABLE log (
    id serial primary key,
    probe serial,
    timestamp timestamp,
    session serial,

    cpu_usage real,
    cpu_usage_per_core real[32],

    ram_usage real,
    swap_usage real,

    network_tx real[32],
    network_rx real[32],

    disk_usage real[32],
    disk_reads real[32],
    disk_writs real[32],

    temperature real[32],
    user_count int,

    foreign key (session) references log_sessions(id),
    foreign key (probe) references probes(id)
);

INSERT INTO log_sessions(id, name) VALUES (1, 'Test-Session');
INSERT INTO probes(id, name) VALUES  (1, 'Server-Probe');