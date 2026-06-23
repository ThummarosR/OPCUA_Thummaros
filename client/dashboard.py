"""dashboard.py — live view of every peer's secret.

Reads the expected roster from peers.csv and the collected secrets from
secrets.db, then shows each peer as either COLLECTED or WAITING. The
dashboard only READS — the collector is what writes secrets.db (this keeps
the Streamlit + paho threading concern out of the UI, exactly how SCADA
separates data acquisition from visualization).

Run:
    streamlit run dashboard.py
Opens at http://localhost:8501 and auto-refreshes every 3 seconds.
"""
import csv
import os
import sqlite3

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

DB = "secrets.db"
PEERS = "peers.csv"

st.set_page_config(
    layout="wide",
    page_title="Classroom Secret Collector",
    page_icon="🔐",
)
st_autorefresh(interval=3000, key="r")   # refresh every 3s

# ---------------------------------------------------------------- styling
st.markdown(
    """
    <style>
      .stApp { background-color: #0e1117; }
      .hero {
        background: linear-gradient(110deg, #14b8a6 0%, #0f766e 55%, #0d3b66 100%);
        padding: 26px 34px; border-radius: 16px; margin-bottom: 22px;
        box-shadow: 0 8px 28px rgba(0,0,0,.35);
      }
      .hero h1 { color: #ffffff; margin: 0; font-size: 34px; font-weight: 800; }
      .hero p  { color: #d1faf3; margin: 6px 0 0; font-size: 15px; }
      .card {
        border-radius: 14px; padding: 18px 22px; color: #fff;
        box-shadow: 0 4px 16px rgba(0,0,0,.30);
      }
      .card .big   { font-size: 40px; font-weight: 800; line-height: 1; }
      .card .label { font-size: 13px; text-transform: uppercase; letter-spacing: .08em; opacity: .9; }
      .c-collected { background: linear-gradient(135deg, #10b981, #047857); }
      .c-waiting   { background: linear-gradient(135deg, #f59e0b, #b45309); }
      .c-total     { background: linear-gradient(135deg, #3b82f6, #1e3a8a); }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>🔐 Classroom Secret Collector</h1>
      <p>Live MQTT pub/sub network · one broker per student · auto-refreshing every 3 s</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- load data
def load_peers():
    if not os.path.exists(PEERS):
        return pd.DataFrame(columns=["id", "name", "tailscale_ip"])
    with open(PEERS, newline="") as f:
        rows = list(csv.DictReader(f))
    return pd.DataFrame(rows)


def load_secrets():
    if not os.path.exists(DB):
        return pd.DataFrame(columns=["id", "name", "secret", "src_ip", "ts"])
    return pd.read_sql(
        "SELECT id, name, secret, src_ip, ts FROM secrets ORDER BY id",
        sqlite3.connect(DB),
    )


peers = load_peers()
secrets = load_secrets()

if peers.empty and secrets.empty:
    st.warning(
        f"No `{PEERS}` roster and no `{DB}` yet. "
        "Fill in peers.csv and run `python collect_secrets.py`."
    )
    st.stop()

# Build the merged roster: every peer in peers.csv, plus any extra that was
# collected but isn't listed. Status = Collected if we have a secret, else Waiting.
collected_ids = set(secrets["id"])

rows = []
seen = set()
for _, p in peers.iterrows():
    pid = p["id"]
    seen.add(pid)
    if pid in collected_ids:
        s = secrets[secrets["id"] == pid].iloc[0]
        rows.append({
            "Status": "✅ Collected",
            "id": pid,
            "name": s["name"] or p.get("name", ""),
            "secret": s["secret"],
            "ip": s["src_ip"] or p.get("tailscale_ip", ""),
            "ts": s["ts"],
        })
    else:
        rows.append({
            "Status": "⏳ Waiting",
            "id": pid,
            "name": p.get("name", ""),
            "secret": "—  (broker not up / not published yet)",
            "ip": p.get("tailscale_ip", ""),
            "ts": "",
        })

# any collected secret whose id isn't in peers.csv
for _, s in secrets.iterrows():
    if s["id"] not in seen:
        rows.append({
            "Status": "✅ Collected",
            "id": s["id"],
            "name": s["name"],
            "secret": s["secret"],
            "ip": s["src_ip"],
            "ts": s["ts"],
        })

table = pd.DataFrame(rows).sort_values(
    by=["Status", "id"], ascending=[True, True]
).reset_index(drop=True)

total = len(table)
n_collected = int((table["Status"] == "✅ Collected").sum())
n_waiting = total - n_collected

# ---------------------------------------------------------------- metric cards
c1, c2, c3 = st.columns(3)
c1.markdown(
    f'<div class="card c-collected"><div class="big">{n_collected}</div>'
    f'<div class="label">Collected</div></div>', unsafe_allow_html=True)
c2.markdown(
    f'<div class="card c-waiting"><div class="big">{n_waiting}</div>'
    f'<div class="label">Waiting</div></div>', unsafe_allow_html=True)
c3.markdown(
    f'<div class="card c-total"><div class="big">{n_collected} / {total}</div>'
    f'<div class="label">Progress</div></div>', unsafe_allow_html=True)

st.write("")
st.progress(n_collected / total if total else 0.0)

# ---------------------------------------------------------------- styled table
def color_rows(row):
    if row["Status"].startswith("✅"):
        css = "background-color: #11261d; color: #6ee7b7;"
    else:
        css = "background-color: #2a2110; color: #fcd34d;"
    return [css] * len(row)


styler = (
    table.style
    .apply(color_rows, axis=1)
    .set_properties(**{"font-size": "15px", "padding": "8px 12px"})
    .hide(axis="index")
)

st.dataframe(styler, use_container_width=True, height=520)

st.caption(
    f"{n_collected} collected · {n_waiting} waiting · roster of {total} "
    "· dashboard reads secrets.db (the collector writes it)."
)
