"""publish_secret.py — publish YOUR secret to YOUR broker, retained.

Run once (or whenever your secret changes):
    python publish_secret.py
"""
import json
import time
import paho.mqtt.client as mqtt

from config import MY_ID, MY_NAME, SECRET, BROKER_HOST, BROKER_PORT

payload = json.dumps({
    "id": MY_ID,
    "name": MY_NAME,
    "secret": SECRET,
    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
})

# paho-mqtt 2.x requires the callback API version
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{MY_ID}-pub")

# Last Will: if this client drops, broker auto-publishes "offline"
c.will_set(f"classroom/{MY_ID}/status", "offline", qos=1, retain=True)

c.connect(BROKER_HOST, BROKER_PORT, 60)

# Announce we are online (retained so late joiners see it)
c.publish(f"classroom/{MY_ID}/status", "online", qos=1, retain=True)

# The key line: retain=True tells the broker to store the secret and hand it
# to anyone who subscribes later. qos=1 = at-least-once delivery.
info = c.publish(f"classroom/{MY_ID}/secret", payload, qos=1, retain=True)
info.wait_for_publish()

print(f"Published secret for {MY_ID} ({MY_NAME}) to {BROKER_HOST}:{BROKER_PORT}")
print(f"  topic: classroom/{MY_ID}/secret")
print(f"  payload: {payload}")

c.disconnect()
