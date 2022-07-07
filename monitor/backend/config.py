import configparser
from os import path
import sys

DEBUG = False

DATABASE_NAME = ""
DATABASE_USER = ""
DATABASE_HOST = ""
DATABASE_PORT = 0
DATABASE_PASSWORD = ""

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
    DEBUG = config["GENERAL"].getboolean("debug", False)
else:
    print("GENERAL section is config is missing", file=sys.stderr)
