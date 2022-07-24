import configparser
from os import path
import sys

CONFIG_FILE = "backend_config/settings.ini"
ENCODING = "utf-8"

DB_HOST = ""
DB_PORT = ""
DB_PASSWORD = ""
DB_USER = ""
DB_DATABASE = ""

MAX_CLIENTS = 0
TIMEOUT = 0
ADDRESS = ("", 0)

if not path.exists(CONFIG_FILE):
    print(f"Config file {CONFIG_FILE} is missing!", file=sys.stderr)
    exit(1)

config = configparser.ConfigParser()
config.read(CONFIG_FILE, ENCODING)

if config.has_section("DATABASE"):
    DB_HOST = config["DATABASE"].get("host", "localhost")
    DB_PORT = config["DATABASE"].getint("port", 5432)
    DB_PASSWORD = config["DATABASE"].get("password", "password")
    DB_USER = config["DATABASE"].get("user", "posgress")
    DB_DATABASE = config["DATABASE"].get("database", "logging")
else:
    print("DATABASE section in config is missing", file=sys.stderr)

if config.has_section("GENERAL"):
    MAX_CLIENTS = config["GENERAL"].getint("max_clients", 1_000)
    TIMEOUT = config["GENERAL"].getfloat("timeout", 1)
    ADDRESS = (
        config["GENERAL"].get("host", "0.0.0.0"),
        config["GENERAL"].getint("port", 1337)
    )
else:
    print("GENERAL section is config is missing", file=sys.stderr)
