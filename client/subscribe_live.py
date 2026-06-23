"""subscribe_live.py — watch messages arrive on ONE broker in real time.

Handy for testing. By default it listens to YOUR own broker.
Pass an IP to watch a peer's broker:
    python subscribe_live.py                 # localhost
    python subscribe_live.py 100.101.0.2     # a peer

Ctrl-C to stop.
"""
import sys
import paho.mqtt.client as mqtt

from config import BROKER_HOST, BROKER_PORT, MY_ID

host = sys.argv[1] if len(sys.argv) > 1 else BROKER_HOST


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"connected to {host} (rc={reason_code}) — subscribing to classroom/#")
    client.subscribe("classroom/#", qos=1)


def on_message(client, userdata, msg):
    print(f"{msg.topic}  {msg.payload.decode()}")


c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{MY_ID}-sub")
c.on_connect = on_connect
c.on_message = on_message
c.connect(host, BROKER_PORT, 60)
c.loop_forever()
