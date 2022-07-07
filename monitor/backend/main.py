from flask import Flask
from flask_cors import CORS
import config
import psycopg2

db_conn = psycopg2.connect(
    dbname=config.DATABASE_NAME,
    user=config.DATABASE_USER,
    password=config.DATABASE_PASSWORD,
    host=config.DATABASE_HOST,
    port=config.DATABASE_PORT
)

app = Flask(__name__)
CORS(app)  # Disable all cors errors


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/probe/<int:probe_id>/info")
def probe_info(probe_id: int):
    cursor: psycopg2._psycopg.cursor = db_conn.cursor()
    cursor.execute("""
    SELECT name, memory_total, swap_total, cpu_cors, 
    disks_names, disks_mountpoint, disks_fstype, disks_size, 
    ipv4, ipv6, network_names
    FROM probes 
    WHERE id = %s;
    """, (probe_id,))
    res = cursor.fetchone()

    if res is None:
        return "", 404
    else:
        return {
            "name": res[0],
            "id": probe_id,
            "memory": res[1],
            "swap": res[2],
            "cores": res[3],
            "addresses": [
                {"ipv6": ipv6, "ipv4": ipv4, "name": name}
                for ipv4, ipv6, name in zip(res[8], res[9], res[10])
            ],
            "disks": [
                {"format": fstype, "size": size, "name": name, "mount": mount}
                for name, mount, fstype, size in zip(res[4], res[5], res[6], res[7])
            ]
        }


if __name__ == "__main__":
    app.run(debug=config.DEBUG)
