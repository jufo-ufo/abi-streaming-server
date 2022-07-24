import configparser
from os import path
import sys

CONFIG_FILE = "probe_config/settings.ini"
ENCODING = "utf-8"

MEASURE_INTERVAL = 0
BACKLOG_MAX_SIZE = 0
BACKLOG_POP_OFF_SIZE = 0
PROBE_ID = 0

NGINX_ENABLED = False

API_HOST = ""
API_PORT = 0

if not path.exists(CONFIG_FILE):
    print(f"Config file {CONFIG_FILE} is missing!", file=sys.stderr)
    exit(1)

config = configparser.ConfigParser()
config.read(CONFIG_FILE, ENCODING)

if config.has_section("API"):
    API_HOST = config["API"].get("host", "localhost")
    API_PORT = config["API"].getint("port", 1337)
else:
    print("API section in config is missing", file=sys.stderr)

if config.has_section("NGINX"):
    NGINX_ENABLED = config["NGINX"].getboolean("enabled", False)
else:
    print("NGINX section in config is missing", file=sys.stderr)

if config.has_section("GENERAL"):
    BACKLOG_MAX_SIZE = config["GENERAL"].getint("max_backlog", 1_000)
    MEASURE_INTERVAL = config["GENERAL"].getfloat("measure_interval", 1)
    BACKLOG_POP_OFF_SIZE = config["GENERAL"].getfloat("backlog_pop_off_size", 1)
    PROBE_ID = config["GENERAL"].getint("probe_id", 0)
else:
    print("GENERAL section is config is missing", file=sys.stderr)
