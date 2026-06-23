# MQTT Pub/Sub Lab — Broker & Client

Your laptop is one "factory cell": it runs its own MQTT broker, publishes a
secret, and collects every classmate's secret across the Tailscale network.

```
broker/
  mosquitto.conf      broker config (listener 0.0.0.0 + allow_anonymous)
client/
  config.py           EDIT: your id, name, secret
  peers.csv           shared list of all 21 Tailscale IPs
  publish_secret.py   publish your secret, retained
  subscribe_live.py   watch one broker live (testing)
  collect_secrets.py  loop peers -> secrets.db
  dashboard.py        live Streamlit view
  requirements.txt
```

## 0. Install Mosquitto (one time)

1. Download from https://mosquitto.org and install (accept defaults).
2. The installer registers a **Windows Service** — stop it so it doesn't grab
   port 1883: open `services.msc`, find **Mosquitto Broker**, Stop it, set
   Startup type to **Manual**.

## 1. Edit your details

Open `client/config.py` and set `MY_ID` (your seat number `s01`..`s21`),
`MY_NAME`, and `SECRET`.

## 2. Start your broker (leave this console open all session)

```powershell
cd broker
& "C:\Program Files\mosquitto\mosquitto.exe" -c .\mosquitto.conf -v
```

`-v` = verbose, so you watch every connection live. First run: allow it
through the Windows Firewall on **Private** networks (TCP 1883).

## 3. Set up Python (one time)

```powershell
cd client
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Publish your secret

```powershell
python publish_secret.py
```

Verify it's retained on your own broker:

```powershell
mosquitto_sub -h localhost -t "classroom/#" -v
```

## 5. Collect everyone's secrets

1. Fill in `peers.csv` with all classmates' Tailscale IPs (your own row uses
   `127.0.0.1`).
2. Run:

```powershell
python collect_secrets.py
```

## 6. Live dashboard

```powershell
streamlit run dashboard.py
```

Opens at http://localhost:8501. Re-run the collector and watch the count climb
toward 20 / 20.

## Conventions (must match the whole class)

- Topics: `classroom/<id>/secret` (retained, QoS 1), `classroom/<id>/status` (LWT)
- Payload JSON keys: `id`, `name`, `secret`, `ts`
- Port 1883, IDs are seat numbers `s01`..`s21`
- Client IDs: `<id>-pub`, `<id>-sub`, `collector-<ip>`

## Troubleshooting

| Symptom | Fix |
|---|---|
| Can't connect to a peer | Their broker isn't running · firewall blocks 1883 · wrong IP |
| 0 secrets collected | Forgot `retain=True`, or wrong topic name |
| "Connection refused" on own broker | Service vs console conflict — port 1883 in use |
| paho callback error | Missing `mqtt.CallbackAPIVersion.VERSION2` |
| auth error | `allow_anonymous true` missing from mosquitto.conf |
