import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
from datetime import datetime
import time
from queue import Queue

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Industrial Worker Safety Monitor",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# GLOBAL STYLING + ICON LIBRARIES
# --------------------------------------------------
st.markdown("""
<!-- Icon library (Font Awesome) -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

<style>
    /* GLOBAL APP BACKGROUND */
    .stApp {
        background: radial-gradient(circle at top, #1f2937 0, #020617 45%, #020617 100%);
        color: #e5e7eb;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
    }

    /* REMOVE DEFAULT PADDING */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* TOP NAVBAR */
    .top-nav {
        background: rgba(15, 23, 42, 0.9);
        border-radius: 16px;
        padding: 0.9rem 1.4rem;
        border: 1px solid rgba(148, 163, 184, 0.25);
        display: flex;
        align-items: center;
        justify-content: space-between;
        backdrop-filter: blur(18px);
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.7);
        margin-bottom: 1.5rem;
    }

    .nav-left {
        display: flex;
        align-items: center;
        gap: 0.85rem;
    }

    .nav-icon-badge {
        width: 40px;
        height: 40px;
        border-radius: 999px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: radial-gradient(circle at 30% 0, #22d3ee, #0ea5e9, #1d4ed8);
        color: #e5faff;
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.35);
    }

    .nav-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #f9fafb;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .nav-subtitle {
        font-size: 0.8rem;
        color: #9ca3af;
    }

    .nav-right {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-size: 0.8rem;
        color: #9ca3af;
    }

    .nav-pill {
        padding: 0.35rem 0.8rem;
        border-radius: 999px;
        border: 1px solid rgba(148, 163, 184, 0.4);
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(15, 23, 42, 0.65));
    }

    .nav-pill span {
        font-size: 0.8rem;
    }

    /* SECTION HEADERS */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin: 1.8rem 0 0.9rem 0;
    }

    .section-title-text {
        font-size: 0.95rem;
        font-weight: 600;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: #e5e7eb;
    }

    .section-line {
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, #4b5563, transparent);
    }

    .section-tag {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
        border: 1px solid rgba(148, 163, 184, 0.4);
        color: #9ca3af;
        background: rgba(15, 23, 42, 0.8);
    }

    /* GLASS CARDS */
    .glass-card {
        background: radial-gradient(circle at top left, rgba(56, 189, 248, 0.06) 0, rgba(15, 23, 42, 0.95) 40%, rgba(15, 23, 42, 0.98) 100%);
        border-radius: 16px;
        border: 1px solid rgba(148, 163, 184, 0.42);
        padding: 1.1rem 1.2rem;
        box-shadow: 0 14px 35px rgba(15, 23, 42, 0.85);
        position: relative;
        overflow: hidden;
    }

    .glass-card::before {
        content: "";
        position: absolute;
        inset: -40%;
        opacity: 0.2;
        background: radial-gradient(circle at 0 0, rgba(56, 189, 248, 0.12), transparent 55%);
        pointer-events: none;
    }

    .glass-card-inner {
        position: relative;
        z-index: 2;
    }

    /* TOP METRICS GRID */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 0.85rem;
        margin-bottom: 1.2rem;
    }

    .metric-card {
        border-radius: 14px;
        border: 1px solid rgba(75, 85, 99, 0.8);
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.95), rgba(15, 23, 42, 0.85));
        padding: 0.85rem 0.9rem;
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
    }

    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #9ca3af;
    }

    .metric-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 999px;
        background: radial-gradient(circle at 30% 0, #22c55e, #16a34a);
        color: #ecfdf5;
        font-size: 0.75rem;
    }

    .metric-value {
        font-size: 1.45rem;
        font-weight: 600;
        color: #f9fafb;
    }

    .metric-sub {
        font-size: 0.75rem;
        color: #9ca3af;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .metric-pill-ok {
        font-size: 0.7rem;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        border: 1px solid rgba(34, 197, 94, 0.5);
        color: #bbf7d0;
        background: rgba(22, 163, 74, 0.15);
    }

    .metric-pill-warn {
        font-size: 0.7rem;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        border: 1px solid rgba(234, 179, 8, 0.7);
        color: #fef9c3;
        background: rgba(234, 179, 8, 0.15);
    }

    .metric-pill-crit {
        font-size: 0.7rem;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        border: 1px solid rgba(248, 113, 113, 0.8);
        color: #fee2e2;
        background: rgba(220, 38, 38, 0.18);
    }

    .dot-green {
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: #22c55e;
        box-shadow: 0 0 12px rgba(34, 197, 94, 0.9);
    }
    .dot-red {
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: #ef4444;
        box-shadow: 0 0 12px rgba(239, 68, 68, 0.9);
    }

    /* ALERT BANNER */
    .alert-ribbon {
        margin-bottom: 0.6rem;
        border-radius: 999px;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.35rem 0.8rem;
        background: linear-gradient(to right, rgba(239, 68, 68, 0.12), rgba(248, 250, 252, 0.02));
        border: 1px solid rgba(248, 113, 113, 0.5);
        color: #fecaca;
        font-size: 0.78rem;
    }

    .alert-icon-spinner {
        width: 18px;
        height: 18px;
        border-radius: 999px;
        border: 2px solid rgba(252, 165, 165, 0.35);
        border-top-color: #fecaca;
        animation: spin 0.85s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    .alert-item {
        background: linear-gradient(90deg, rgba(30, 64, 175, 0.32), rgba(15, 23, 42, 0.9));
        border-radius: 10px;
        padding: 0.6rem 0.75rem;
        border: 1px solid rgba(59, 130, 246, 0.65);
        font-size: 0.8rem;
        margin-bottom: 0.25rem;
        display: flex;
        justify-content: space-between;
        gap: 0.4rem;
        align-items: center;
    }

    .alert-badge {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        padding: 0.2rem 0.45rem;
        border-radius: 999px;
        border: 1px solid rgba(251, 191, 36, 0.7);
        color: #fef3c7;
        background: rgba(30, 64, 175, 0.5);
        white-space: nowrap;
    }

    /* SENSOR DETAIL GRID */
    .sensor-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.85rem;
        margin-top: 0.75rem;
    }

    .sensor-card {
        border-radius: 14px;
        padding: 1rem 1rem;
        border: 1px solid rgba(55, 65, 81, 0.85);
        background: radial-gradient(circle at top left, rgba(56, 189, 248, 0.07) 0, rgba(15, 23, 42, 0.94) 50%, rgba(15, 23, 42, 1) 100%);
        position: relative;
        overflow: hidden;
    }

    .sensor-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #9ca3af;
        margin-bottom: 0.4rem;
    }

    .sensor-chip {
        font-size: 0.68rem;
        padding: 0.12rem 0.5rem;
        border-radius: 999px;
        background: rgba(31, 41, 55, 0.9);
        border: 1px solid rgba(75, 85, 99, 0.8);
        color: #9ca3af;
    }

    .sensor-value-main {
        font-size: 1.9rem;
        font-weight: 600;
        color: #f9fafb;
        margin-bottom: 0.25rem;
    }

    .sensor-subvalue {
        font-size: 0.82rem;
        color: #9ca3af;
        margin-bottom: 0.35rem;
    }

    .sensor-caption {
        font-size: 0.72rem;
        color: #6b7280;
    }

    .status-pill {
        font-size: 0.7rem;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
    }

    .status-pill-normal {
        border: 1px solid rgba(34, 197, 94, 0.7);
        background: rgba(22, 163, 74, 0.15);
        color: #bbf7d0;
    }
    .status-pill-warning {
        border: 1px solid rgba(234, 179, 8, 0.8);
        background: rgba(234, 179, 8, 0.18);
        color: #fef9c3;
    }
    .status-pill-critical {
        border: 1px solid rgba(248, 113, 113, 0.85);
        background: rgba(220, 38, 38, 0.23);
        color: #fee2e2;
    }

    /* MINI PROGRESS BARS */
    .risk-bar {
        width: 100%;
        height: 6px;
        border-radius: 999px;
        background: rgba(31, 41, 55, 0.95);
        overflow: hidden;
        margin-top: 0.25rem;
    }
    .risk-bar-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #22c55e, #eab308, #ef4444);
    }

    /* FOOTER LINE */
    .footer-line {
        border-top: 1px solid rgba(55, 65, 81, 0.9);
        margin: 1.7rem 0 0.8rem 0;
    }

    .footer-meta {
        font-size: 0.75rem;
        color: #6b7280;
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.4rem;
    }

    /* DATAFRAME TUNING */
    .dataframe {
        font-size: 0.82rem;
    }

    /* SIDEBAR STYLE (if opened) */
    section[data-testid="stSidebar"] {
        background: #020617;
        border-right: 1px solid rgba(31, 41, 55, 0.8);
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# SESSION STATE INIT
# --------------------------------------------------
if 'global_queues_initialized' not in st.session_state:
    st.session_state.global_queues_initialized = True
    st.session_state.data_queue = Queue()
    st.session_state.alert_queue = Queue()

if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = []
    st.session_state.alerts = []
    st.session_state.latest = {}
    st.session_state.mqtt_connected = False
    st.session_state.last_data_time = None

data_queue = st.session_state.data_queue
alert_queue = st.session_state.alert_queue

# --------------------------------------------------
# MQTT HANDLERS
# --------------------------------------------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe("worker/safety/data")
        client.subscribe("worker/safety/alert")
        print("✅ MQTT Connected to broker.emqx.io")
    else:
        print(f"❌ MQTT Connection failed: {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print(f"📥 Received: {msg.topic}")
        if msg.topic == "worker/safety/data":
            data_queue.put(data)
        elif msg.topic == "worker/safety/alert":
            alert_queue.put(data)
    except Exception as e:
        print(f"❌ Error in on_message: {e}")

if 'mqtt_client' not in st.session_state:
    st.session_state.mqtt_client = mqtt.Client()
    st.session_state.mqtt_client.on_connect = on_connect
    st.session_state.mqtt_client.on_message = on_message
    try:
        st.session_state.mqtt_client.connect("broker.emqx.io", 1883, 60)
        st.session_state.mqtt_client.loop_start()
        st.session_state.mqtt_connected = True
        print("🔄 MQTT Loop started")
    except Exception as e:
        st.error(f"MQTT Error: {e}")
        st.session_state.mqtt_connected = False

# --------------------------------------------------
# INGEST QUEUES INTO SESSION STATE
# --------------------------------------------------
while not data_queue.empty():
    try:
        data = data_queue.get_nowait()
        data['timestamp'] = datetime.now().strftime("%H:%M:%S")
        st.session_state.sensor_data.append(data)
        st.session_state.latest = data
        st.session_state.last_data_time = datetime.now()
        if len(st.session_state.sensor_data) > 300:
            st.session_state.sensor_data.pop(0)
    except Exception:
        break

while not alert_queue.empty():
    try:
        data = alert_queue.get_nowait()
        data['time'] = datetime.now().strftime("%H:%M:%S")
        st.session_state.alerts.insert(0, data)
        if len(st.session_state.alerts) > 50:
            st.session_state.alerts.pop()
    except Exception:
        break

latest = st.session_state.latest if st.session_state.latest else None

# --------------------------------------------------
# HELPER: COMPUTE RISK SCORES FROM EXISTING FIELDS
# --------------------------------------------------
def compute_risk_scores(latest_data):
    if not latest_data:
        return 0, 0, 0

    temp = latest_data.get('body_temp', 0)
    hr = latest_data.get('heart_rate', 0)
    spo2 = latest_data.get('spo2', 100)
    rad = latest_data.get('radiation_uSvh', 0)
    gas = latest_data.get('gas_ppm', 0)
    fall = latest_data.get('fall_detected', False)

    # Physiological risk (0–100)
    phys_risk = 0
    # Temp contribution
    if temp > 37.5:
        phys_risk += min((temp - 37.5) * 25, 40)
    # HR contribution
    if hr > 100:
        phys_risk += min((hr - 100) * 0.6, 35)
    # SpO2 contribution
    if spo2 < 95:
        phys_risk += min((95 - spo2) * 3, 25)
    phys_risk = max(0, min(100, phys_risk))

    # Environmental risk
    env_risk = 0
    if gas > 300:
        env_risk += min((gas - 300) / 3, 45)
    if rad > 0.5:
        env_risk += min((rad - 0.5) * 60, 35)
    if fall:
        env_risk += 30
    env_risk = max(0, min(100, env_risk))

    # Overall score (higher = more risky)
    overall = int(min(100, (phys_risk * 0.55 + env_risk * 0.45)))
    return int(phys_risk), int(env_risk), overall

phys_risk, env_risk, overall_risk = compute_risk_scores(latest)

def risk_label(score):
    if score >= 70:
        return "CRITICAL", "metric-pill-crit"
    elif score >= 40:
        return "WARNING", "metric-pill-warn"
    else:
        return "STABLE", "metric-pill-ok"




# --------------------------------------------------
# TOP NAVBAR
# --------------------------------------------------
connection_status = "Online" if st.session_state.mqtt_connected and latest else "Offline"
last_update_txt = "N/A"
if st.session_state.last_data_time:
    last_secs = (datetime.now() - st.session_state.last_data_time).seconds
    last_update_txt = f"{last_secs}s ago"

st.markdown(f"""
<div class="top-nav">
  <div class="nav-left">
    <div class="nav-icon-badge">
      <i class="fa-solid fa-user-shield"></i>
    </div>
    <div>
      <div class="nav-title">Industrial Worker Safety Monitoring</div>
      <div class="nav-subtitle">
        <i class="fa-solid fa-microchip"></i>&nbsp;
        To Start Simulation · 
        <a href="https://wokwi.com/projects/447224581770989569" target="_blank" style="
            color:#60a5fa;
            text-decoration:none;
            font-weight:600;
        ">
            https://wokwi.com/projects/447224581770989569
        </a>
      </div>
    </div>
  </div>
  <div class="nav-right">
    <div class="nav-pill">
      <i class="fa-solid fa-circle-{ 'check' if connection_status=='Online' else 'xmark' }"></i>
      <span><strong>MQTT:</strong> {connection_status}</span>
    </div>
    <div class="nav-pill">
      <i class="fa-regular fa-clock"></i>
      <span><strong>Last packet:</strong> {last_update_txt}</span>
    </div>
    <div class="nav-pill">
      <i class="fa-solid fa-satellite-dish"></i>
      <span><strong>Broker:</strong> broker.emqx.io</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# TOP METRIC STRIP  (NEW ADVANCED VIEW)
# --------------------------------------------------
alerts_count = len(st.session_state.alerts)
datapoints_count = len(st.session_state.sensor_data)
worker_status = "NO DATA"
if latest:
    temp = latest.get('body_temp', 0)
    hr = latest.get('heart_rate', 0)
    rad = latest.get('radiation_uSvh', 0)
    gas = latest.get('gas_ppm', 0)
    critical_count = sum([temp > 38.5, hr > 110, rad > 1.0, gas > 500])
    worker_status = "CRITICAL" if critical_count > 0 else "NORMAL"

status_pill_class = {
    "CRITICAL": "metric-pill-crit",
    "NORMAL": "metric-pill-ok",
    "NO DATA": "metric-pill-warn"
}.get(worker_status, "metric-pill-warn")

phys_label, phys_class = risk_label(phys_risk)
env_label, env_class = risk_label(env_risk)
overall_label, overall_class = risk_label(overall_risk)

st.markdown("<div class='glass-card'><div class='glass-card-inner'>", unsafe_allow_html=True)

st.markdown("<div class='metric-grid'>", unsafe_allow_html=True)

# SYSTEM STATUS
st.markdown(f"""
<div class="metric-card">
  <div class="metric-header">
    <span>SYSTEM STATUS</span>
    <div class="metric-icon">
      <i class="fa-solid fa-tower-broadcast"></i>
    </div>
  </div>
  <div class="metric-value">{worker_status}</div>
  <div class="metric-sub">
    <span>Device heartbeat</span>
    <span class="{status_pill_class}">{worker_status}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ACTIVE ALERTS
st.markdown(f"""
<div class="metric-card">
  <div class="metric-header">
    <span>ACTIVE ALERTS</span>
    <div class="metric-icon" style="background: radial-gradient(circle at 30% 0,#f97316,#f97316);">
      <i class="fa-solid fa-bell-exclamation"></i>
    </div>
  </div>
  <div class="metric-value">{alerts_count}</div>
  <div class="metric-sub">
    <span>Last 50 events</span>
    <span class="{ 'metric-pill-crit' if alerts_count>0 else 'metric-pill-ok'}">
      { 'ALERTING' if alerts_count>0 else 'CLEAR' }
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

# DATA POINTS
st.markdown(f"""
<div class="metric-card">
  <div class="metric-header">
    <span>DATA POINTS</span>
    <div class="metric-icon" style="background: radial-gradient(circle at 30% 0,#0ea5e9,#3b82f6);">
      <i class="fa-solid fa-database"></i>
    </div>
  </div>
  <div class="metric-value">{datapoints_count}</div>
  <div class="metric-sub">
    <span>Session buffer</span>
    <span class="metric-pill-ok">{'LIVE STREAM' if datapoints_count>0 else 'WAITING'}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# PHYSIO RISK
st.markdown(f"""
<div class="metric-card">
  <div class="metric-header">
    <span>PHYSIOLOGICAL LOAD</span>
    <div class="metric-icon" style="background: radial-gradient(circle at 30% 0,#a855f7,#6366f1);">
      <i class="fa-solid fa-heart-pulse"></i>
    </div>
  </div>
  <div class="metric-value">{phys_risk}</div>
  <div class="metric-sub">
    <span>Temperature · HR · SpO₂</span>
    <span class="{phys_class}">{phys_label}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ENVIRONMENTAL RISK
st.markdown(f"""
<div class="metric-card">
  <div class="metric-header">
    <span>ENV. RISK SCORE</span>
    <div class="metric-icon" style="background: radial-gradient(circle at 30% 0,#22c55e,#16a34a);">
      <i class="fa-solid fa-cloud-bolt"></i>
    </div>
  </div>
  <div class="metric-value">{env_risk}</div>
  <div class="metric-sub">
    <span>Gas · Radiation · Fall</span>
    <span class="{env_class}">{env_label}</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # end metric-grid

# Overall risk mini-bar
st.markdown(f"""
<div style="margin-top:0.5rem; display:flex; justify-content:space-between; align-items:center; gap:0.8rem; font-size:0.78rem; color:#9ca3af;">
  <div style="display:flex; align-items:center; gap:0.45rem;">
    <span style="text-transform:uppercase; letter-spacing:0.12em;">Overall risk index</span>
    <span class="{overall_class}">{overall_label} · {overall_risk}</span>
  </div>
  <div style="flex:1;">
    <div class="risk-bar">
      <div class="risk-bar-fill" style="width:{overall_risk}%;"></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("</div></div>", unsafe_allow_html=True)  # end glass-card & inner

# --------------------------------------------------
# ALERTS RIBBON
# --------------------------------------------------
if st.session_state.alerts:
    st.markdown("""
    <div class="section-header">
      <div class="section-title-text">Critical Events</div>
      <div class="section-line"></div>
      <div class="section-tag"><i class="fa-solid fa-bolt"></i>&nbsp;Live Alert Stream</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="alert-ribbon">
      <div class="alert-icon-spinner"></div>
      <span><strong>Attention:</strong> Safety engine is processing live alerts from the edge device.</span>
    </div>
    """, unsafe_allow_html=True)

    # Filter alerts by keyword (works with existing data structure)
    filter_text = st.text_input("Filter alerts (type, metric, etc.)", "", key="alert_filter")

    filtered_alerts = st.session_state.alerts
    if filter_text.strip():
        keyword = filter_text.lower()
        filtered_alerts = [
            a for a in st.session_state.alerts
            if any(keyword in str(v).lower() for v in a.values())
        ]

    for alert in filtered_alerts[:6]:
        alert_msgs = [f"{k.replace('_alert','').upper()}: {v}" for k, v in alert.items() if k != "time"]
        st.markdown(f"""
        <div class="alert-item">
          <div>
            <strong><i class="fa-solid fa-triangle-exclamation"></i>&nbsp;{alert['time']}</strong> · {" | ".join(alert_msgs)}
          </div>
          <div class="alert-badge">
            <i class="fa-solid fa-shield-halved"></i>&nbsp;Active
          </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="section-header">
      <div class="section-title-text">Critical Events</div>
      <div class="section-line"></div>
      <div class="section-tag"><i class="fa-regular fa-bell"></i>&nbsp;No Active Alerts</div>
    </div>
    """, unsafe_allow_html=True)

    st.info("Alert engine is armed. No alerts have been triggered yet.")

# --------------------------------------------------
# MAIN TABS FOR ADVANCED UI
# --------------------------------------------------
tab_overview, tab_health, tab_environment, tab_system = st.tabs(
    ["📊 Overview Dashboard", "❤️ Health & Biometrics", "🌫️ Environment & Fall", "🛠️ System Logs & Raw Data"]
)

# --------------------------------------------------
# TAB 1: OVERVIEW DASHBOARD
# --------------------------------------------------
with tab_overview:
    st.markdown("""
    <div class="section-header" style="margin-top:1.5rem;">
      <div class="section-title-text">Realtime Telemetry</div>
      <div class="section-line"></div>
      <div class="section-tag"><i class="fa-solid fa-wave-square"></i>&nbsp;Signal Overview</div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns([1.8, 1.2])

    with col_a:
        if st.session_state.sensor_data:
            df = pd.DataFrame(st.session_state.sensor_data)
            # Use last 80 points for charts
            df_tail = df.tail(80)

            # Add a monotonic index for plotting instead of only string timestamps
            df_tail = df_tail.copy()
            df_tail["index"] = range(len(df_tail))
            df_tail.set_index("index", inplace=True)

            st.markdown("**Live Trends (last 80 points)**")
            st.line_chart(
                df_tail[["body_temp", "heart_rate", "gas_ppm", "radiation_uSvh"]],
                use_container_width=True
            )
        else:
            st.warning("Waiting for incoming data stream to render trend charts.")

    with col_b:
        st.markdown("**Session Snapshot**")
        with st.container():
            st.markdown("<div class='glass-card'><div class='glass-card-inner'>", unsafe_allow_html=True)
            if latest:
                worker_id = "Worker-01"
                shift_start = st.session_state.sensor_data[0]["timestamp"] if st.session_state.sensor_data else "N/A"
                fall_flag = "Detected" if latest.get("fall_detected", False) else "None"

                st.markdown(f"""
                <div style="display:flex; align-items:flex-start; gap:0.75rem;">
                  <div style="width:40px;height:40px;border-radius:999px;background:linear-gradient(135deg,#6366f1,#ec4899);display:flex;align-items:center;justify-content:center;">
                    <i class="fa-solid fa-id-badge"></i>
                  </div>
                  <div style="flex:1;">
                    <div style="font-size:0.85rem;color:#9ca3af;">Active Profile</div>
                    <div style="font-size:1.05rem;font-weight:600;color:#f9fafb;">{worker_id}</div>
                    <div style="font-size:0.78rem;color:#6b7280;margin-top:0.2rem;">
                      Shift window started around: <strong>{shift_start}</strong>
                    </div>
                  </div>
                </div>
                <div style="margin-top:0.8rem;font-size:0.82rem;color:#9ca3af;">
                  <ul style="padding-left:1.1rem;margin:0;">
                    <li>Fall detection: <strong>{fall_flag}</strong></li>
                    <li>Gas exposure window: <strong>{latest.get('gas_ppm',0):.0f} ppm</strong></li>
                    <li>Current heart rate: <strong>{latest.get('heart_rate',0)} BPM</strong></li>
                  </ul>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.write("No active worker data available.")
            st.markdown("</div></div>", unsafe_allow_html=True)

# --------------------------------------------------
# TAB 2: HEALTH & BIOMETRICS
# --------------------------------------------------
with tab_health:
    st.markdown("""
    <div class="section-header" style="margin-top:1.5rem;">
      <div class="section-title-text">Biometric Envelope</div>
      <div class="section-line"></div>
      <div class="section-tag"><i class="fa-solid fa-heart-circle-bolt"></i>&nbsp;Body Vitals</div>
    </div>
    """, unsafe_allow_html=True)

    if latest:
        st.markdown("<div class='sensor-grid'>", unsafe_allow_html=True)

        # BODY TEMP
        temp = latest.get('body_temp', 0)
        temp_status = "CRITICAL" if temp > 38.5 else ("WARNING" if temp > 38.0 else "NORMAL")
        temp_class = {
            "NORMAL": "status-pill-normal",
            "WARNING": "status-pill-warning",
            "CRITICAL": "status-pill-critical"
        }[temp_status]
        st.markdown(f"""
        <div class="sensor-card">
          <div class="sensor-header">
            <span>Body Temperature</span>
            <span class="sensor-chip"><i class="fa-solid fa-temperature-half"></i>&nbsp;DS18B20</span>
          </div>
          <div class="sensor-value-main">{temp:.1f}°C</div>
          <div class="sensor-subvalue">Normal: 36.5 – 37.5°C</div>
          <span class="status-pill {temp_class}">
            <span class="dot-green"></span> {temp_status}
          </span>
          <div class="sensor-caption" style="margin-top:0.4rem;">
            Continuous thermal monitoring to detect heat stress and early signs of fatigue.
          </div>
        </div>
        """, unsafe_allow_html=True)

        # HEART + SPO2
        hr = latest.get('heart_rate', 0)
        spo2 = latest.get('spo2', 0)
        hr_status = "CRITICAL" if hr > 110 else ("WARNING" if hr > 100 else "NORMAL")
        spo2_status = "CRITICAL" if spo2 < 90 else ("WARNING" if spo2 < 95 else "NORMAL")
        vital_status = "CRITICAL" if (hr_status == "CRITICAL" or spo2_status == "CRITICAL") else hr_status
        vital_class = {
            "NORMAL": "status-pill-normal",
            "WARNING": "status-pill-warning",
            "CRITICAL": "status-pill-critical"
        }[vital_status]

        st.markdown(f"""
        <div class="sensor-card">
          <div class="sensor-header">
            <span>Cardio & SpO₂</span>
            <span class="sensor-chip"><i class="fa-solid fa-heart-pulse"></i>&nbsp;Pulse Oximeter</span>
          </div>
          <div class="sensor-value-main">{hr} BPM</div>
          <div class="sensor-subvalue">SpO₂: {spo2}%</div>
          <span class="status-pill {vital_class}">
            <span class="dot-green"></span> {vital_status}
          </span>
          <div class="sensor-caption" style="margin-top:0.4rem;">
            HR normal: 60–100 BPM · SpO₂ >95% recommended for safe operational duty.
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Accelerometer summary (biometric context)
        accel_x = latest.get('accel_x', 0)
        accel_y = latest.get('accel_y', 0)
        accel_z = latest.get('accel_z', 0)
        fall_detected = latest.get('fall_detected', False)
        fall_text = "FALL DETECTED" if fall_detected else "STABLE"
        fall_class = "status-pill-critical" if fall_detected else "status-pill-normal"

        st.markdown(f"""
        <div class="sensor-card">
          <div class="sensor-header">
            <span>Posture & Motion</span>
            <span class="sensor-chip"><i class="fa-solid fa-person-falling"></i>&nbsp;MPU6050</span>
          </div>
          <div class="sensor-subvalue">Accel X: {accel_x:.3f} g</div>
          <div class="sensor-subvalue">Accel Y: {accel_y:.3f} g</div>
          <div class="sensor-subvalue">Accel Z: {accel_z:.3f} g</div>
          <span class="status-pill {fall_class}" style="margin-top:0.2rem;">
            {fall_text}
          </span>
          <div class="sensor-caption" style="margin-top:0.4rem;">
            Micro-movements indicate worker posture stability and potential slips or falls.
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Risk breakdown card (health only)
        st.markdown(f"""
        <div class="sensor-card">
          <div class="sensor-header">
            <span>Health Risk Breakdown</span>
            <span class="sensor-chip"><i class="fa-solid fa-shield-heart"></i>&nbsp;Analytics Engine</span>
          </div>
          <div class="sensor-subvalue">
            Weighted health load derived from HR, body temperature, and SpO₂ thresholds.
          </div>
          <div style="margin-top:0.4rem;">
            <div style="font-size:0.78rem;display:flex;justify-content:space-between;">
              <span>Current score</span><span><strong>{phys_risk}</strong>/100</span>
            </div>
            <div class="risk-bar">
              <div class="risk-bar-fill" style="width:{phys_risk}%;"></div>
            </div>
          </div>
          <div class="sensor-caption" style="margin-top:0.4rem;">
            Lower scores indicate comfortable physiological load; higher scores require intervention.
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("No biometric data received yet. Start the simulation to populate this section.")

# --------------------------------------------------
# TAB 3: ENVIRONMENT & FALL
# --------------------------------------------------
with tab_environment:
    st.markdown("""
    <div class="section-header" style="margin-top:1.5rem;">
      <div class="section-title-text">Environmental Envelope</div>
      <div class="section-line"></div>
      <div class="section-tag"><i class="fa-solid fa-cloud"></i>&nbsp;Gas · Radiation · Motion</div>
    </div>
    """, unsafe_allow_html=True)

    if latest:
        st.markdown("<div class='sensor-grid'>", unsafe_allow_html=True)

        # Radiation
        rad_cpm = latest.get('radiation_cpm', 0)
        rad_uSv = latest.get('radiation_uSvh', 0)
        rad_status = "CRITICAL" if rad_uSv > 1.0 else ("WARNING" if rad_uSv > 0.5 else "NORMAL")
        rad_class = {
            "NORMAL": "status-pill-normal",
            "WARNING": "status-pill-warning",
            "CRITICAL": "status-pill-critical"
        }[rad_status]

        st.markdown(f"""
        <div class="sensor-card">
          <div class="sensor-header">
            <span>Radiation Exposure</span>
            <span class="sensor-chip"><i class="fa-solid fa-radiation"></i>&nbsp;Geiger Tube</span>
          </div>
          <div class="sensor-value-main">{rad_uSv:.3f} µSv/h</div>
          <div class="sensor-subvalue">Counts per minute (CPM): {rad_cpm:.0f}</div>
          <span class="status-pill {rad_class}">
            {rad_status}
          </span>
          <div class="sensor-caption" style="margin-top:0.4rem;">
            Safety envelope maintained when exposure remains &lt; 1.0 µSv/h for shift duration.
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Gas + fall (environment hazard)
        gas = latest.get('gas_ppm', 0)
        fall = latest.get('fall_detected', False)
        gas_status = "CRITICAL" if gas > 500 else ("WARNING" if gas > 300 else "NORMAL")
        fall_status = "CRITICAL" if fall else "NORMAL"
        env_status = "CRITICAL" if gas_status == "CRITICAL" or fall_status == "CRITICAL" else gas_status
        env_class = {
            "NORMAL": "status-pill-normal",
            "WARNING": "status-pill-warning",
            "CRITICAL": "status-pill-critical"
        }[env_status]

        st.markdown(f"""
        <div class="sensor-card">
          <div class="sensor-header">
            <span>Hazard Surface</span>
            <span class="sensor-chip"><i class="fa-solid fa-cloud-bolt"></i>&nbsp;MQ-2 · MPU6050</span>
          </div>
          <div class="sensor-value-main">{gas:.0f} PPM</div>
          <div class="sensor-subvalue">Fall: {"DETECTED" if fall else "None"} </div>
          <span class="status-pill {env_class}">
            {env_status}
          </span>
          <div class="sensor-caption" style="margin-top:0.4rem;">
            Gas safe: &lt; 300 ppm · Any sharp motion spike triggers fall and impact analysis.
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Environmental risk score
        st.markdown(f"""
        <div class="sensor-card">
          <div class="sensor-header">
            <span>Environmental Risk Index</span>
            <span class="sensor-chip"><i class="fa-solid fa-satellite-dish"></i>&nbsp;Edge Analytics</span>
          </div>
          <div class="sensor-subvalue">
            Combines gas, radiation, and motion signals into a single actionable index.
          </div>
          <div style="margin-top:0.35rem;">
            <div style="font-size:0.78rem;display:flex;justify-content:space-between;">
              <span>Score</span><span><strong>{env_risk}</strong>/100</span>
            </div>
            <div class="risk-bar">
              <div class="risk-bar-fill" style="width:{env_risk}%;"></div>
            </div>
          </div>
          <div class="sensor-caption" style="margin-top:0.4rem;">
            Values above 60 require immediate inspection of the worker’s surroundings.
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Environmental mini-history
        if st.session_state.sensor_data:
            df_env = pd.DataFrame(st.session_state.sensor_data).tail(50)
            df_env_plot = df_env.copy()
            df_env_plot["index"] = range(len(df_env_plot))
            df_env_plot.set_index("index", inplace=True)

            st.markdown("""
            <div class="sensor-card">
              <div class="sensor-header">
                <span>Micro-History (last 50 points)</span>
                <span class="sensor-chip"><i class="fa-solid fa-chart-line"></i>&nbsp;Trends</span>
              </div>
              <div class="sensor-subvalue">
                Short window view of gas and radiation to catch early drifts.
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.area_chart(df_env_plot[["gas_ppm", "radiation_uSvh"]], use_container_width=True)
        else:
            st.info("Waiting for enough environmental data to show micro-history window.")

        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("No environment data received yet. Start simulation to see hazard metrics.")

# --------------------------------------------------
# TAB 4: SYSTEM LOGS & RAW DATA
# --------------------------------------------------
with tab_system:
    st.markdown("""
    <div class="section-header" style="margin-top:1.5rem;">
      <div class="section-title-text">Logs & Telemetry Tables</div>
      <div class="section-line"></div>
      <div class="section-tag"><i class="fa-solid fa-terminal"></i>&nbsp;Raw Channel</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Alert History Log**")
        if st.session_state.alerts:
            alerts_df = pd.DataFrame(st.session_state.alerts)
            st.dataframe(alerts_df, use_container_width=True, height=380)
        else:
            st.info("No alerts recorded in this session.")

    with col2:
        st.markdown("**Safety Statistics Summary**")
        if st.session_state.sensor_data:
            df = pd.DataFrame(st.session_state.sensor_data)

            avg_temp = df['body_temp'].mean()
            max_temp = df['body_temp'].max()

            avg_hr = df['heart_rate'].mean()
            max_hr = df['heart_rate'].max()

            max_radiation = df['radiation_uSvh'].max()
            avg_radiation = df['radiation_uSvh'].mean()

            max_gas = df['gas_ppm'].max()
            avg_gas = df['gas_ppm'].mean()

            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("AVG BODY TEMP", f"{avg_temp:.1f}°C")
                st.metric("MAX BODY TEMP", f"{max_temp:.1f}°C")
                st.metric("AVG HEART RATE", f"{avg_hr:.0f} BPM")
                st.metric("MAX HEART RATE", f"{max_hr:.0f} BPM")

            with col_b:
                st.metric("MAX RADIATION", f"{max_radiation:.3f} µSv/h")
                st.metric("AVG RADIATION", f"{avg_radiation:.3f} µSv/h")
                st.metric("MAX GAS LEVEL", f"{max_gas:.0f} PPM")
                st.metric("AVG GAS LEVEL", f"{avg_gas:.0f} PPM")
        else:
            st.info("Insufficient data for statistical summary.")

        st.markdown("---")
        st.markdown("**Raw Sensor Table**")
        if st.session_state.sensor_data:
            raw_df = pd.DataFrame(st.session_state.sensor_data).tail(200)
            st.dataframe(raw_df, use_container_width=True, height=280)
        else:
            st.info("No raw rows captured for this session.")

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("<div class='footer-line'></div>", unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="footer-meta">
      <span><i class="fa-regular fa-clock"></i>&nbsp;System Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} · Refresh Rate: 2s</span>
      <span><i class="fa-solid fa-link"></i>&nbsp;Simulator: <a href="https://wokwi.com/projects/447224581770989569" target="_blank">Open Wokwi worker node</a></span>
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# AUTO REFRESH LOOP
# --------------------------------------------------
time.sleep(2)
st.rerun()
