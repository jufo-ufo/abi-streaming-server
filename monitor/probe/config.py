import configparser
from os import path
import sys

MEASURE_INTERVAL = 1

BACKLOG_MAX_SIZE = 1000

LOGGING_SESSION_ID = 0
PROBE_ID = 0

DATABASE_NAME = "logging"
DATABASE_USER = "postgres"
DATABASE_HOST = "localhost"
DATABASE_PORT = 5432
DATABASE_PASSWORD = "password"

CONFIG_FILE = "settings.ini"

ENCODING = "utf-8"

if not path.exists(CONFIG_FILE):
    print(f"Config file {CONFIG_FILE} is missing!", file=sys.stderr)
    exit(1)

config = configparser.ConfigParser()
config.read(CONFIG_FILE, ENCODING)

if config.has_section("DATABASE"):
    DATABASE_HOST = config["DATABASE"].get("host", "logging")
    DATABASE_PORT = config["DATABASE"].getint("port", 5432)
    DATABASE_NAME = config["DATABASE"].get("database", "ticket")
    DATABASE_USER = config["DATABASE"].get("user", "postgres")
    DATABASE_PASSWORD = config["DATABASE"].get("password", "4321")
else:
    print("DATABASE section in config is missing", file=sys.stderr)

if config.has_section("GENERAL"):
    BACKLOG_MAX_SIZE = config["GENERAL"].getint("max_backlog", 1_000)
    MEASURE_INTERVAL = config["GENERAL"].getfloat("measure_interval", 1)
    LOGGING_SESSION_ID = config["GENERAL"].getfloat("logging_session_id")
    PROBE_ID = config["GENERAL"].getfloat("probe_id")
else:
    print("API section is config is missing", file=sys.stderr)
