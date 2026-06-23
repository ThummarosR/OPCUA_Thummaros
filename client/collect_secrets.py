"""collect_secrets.py — connect to every peer broker in peers.csv,
grab each retained secret, and store it in a local SQLite database.

Run (re-run any time — it's idempotent):
    python collect_secrets.py
"""
import csv
import json
import sqlite3
import time
import os
import paho.mqtt.client as mqtt

from config import BROKER_PORT

DB = "secrets.db"
PEERS = "peers.csv"


def init_db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS secrets(
        id TEXT PRIMARY KEY, name TEXT, secret TEXT,
        src_ip TEXT, ts TEXT)""")
    con.commit()
    con.close()


def save(rec, ip):
    con = sqlite3.connect(DB)
    con.execute("REPLACE INTO secrets VALUES (?,?,?,?,?)",
                (rec["id"], rec.get("name", ""), rec["secret"],
                 ip, rec.get("ts", "")))
    con.commit()
    con.close()


def on_message(client, userdata, msg):
    try:
        rec = json.loads(msg.payload.decode())
        save(rec, userdata["ip"])
        print(f"  got {rec['id']:>3} ({rec.get('name','')}): {rec['secret']}")
    except Exception as e:
        print("  bad payload:", e)


def grab_from(ip):
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                    client_id=f"collector-{ip}", userdata={"ip": ip})
    c.on_message = on_message
    c.connect(ip, BROKER_PORT, 10)
    c.subscribe("classroom/+/secret", qos=1)
    c.loop_start()
    time.sleep(2)          # let retained messages arrive
    c.loop_stop()
    c.disconnect()


def main():
    if not os.path.exists(PEERS):
        print(f"ERROR: {PEERS} not found. Fill in everyone's Tailscale IPs first.")
        return

    init_db()
    for row in csv.DictReader(open(PEERS)):
        ip = row.get("tailscale_ip", "").strip()
        if not ip:
            continue
        print(f"connecting to {row.get('id','?')} @ {ip} ...")
        try:
            grab_from(ip)
        except Exception as e:
            print("  skip", ip, "-", e)

    con = sqlite3.connect(DB)
    count = con.execute("SELECT COUNT(*) FROM secrets").fetchone()[0]
    con.close()
    print(f"\nDone. {count} secrets stored in {DB}")


if __name__ == "__main__":
    main()
