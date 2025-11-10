import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
from datetime import datetime
import time
from queue import Queue

# Page config MUST be first Streamlit command
st.set_page_config(
    page_title="Industrial Worker Safety Monitor",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional industrial styling
st.markdown("""
<style>
    /* Main theme */
    .stApp {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
        padding: 2rem;
        border-radius: 10px;
        border-left: 5px solid #3b82f6;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .main-title {
        color: #f8fafc;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .simulation-notice {
        background: #1e40af;
        color: #fff;
        padding: 0.75rem 1.25rem;
        border-radius: 6px;
        margin-top: 1rem;
        font-size: 0.95rem;
        border-left: 4px solid #60a5fa;
    }
    
    .simulation-notice a {
        color: #93c5fd;
        text-decoration: none;
        font-weight: 600;
    }
    
    /* Status cards */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.95rem;
        font-weight: 500;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Alert styling */
    .alert-critical {
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
        border-left: 5px solid #dc2626;
        padding: 1.25rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #fecaca;
        font-weight: 600;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #78350f 0%, #92400e 100%);
        border-left: 4px solid #f59e0b;
        padding: 1rem 1.25rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        color: #fde68a;
        font-size: 0.9rem;
    }
    
    /* Section headers */
    .section-header {
        color: #e2e8f0;
        font-size: 1.1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #334155;
    }
    
    /* Sensor cards */
    .sensor-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #475569;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        margin-bottom: 1rem;
    }
    
    .sensor-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    .sensor-value {
        color: #f1f5f9;
        font-size: 2rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    .sensor-status {
        font-size: 0.9rem;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        display: inline-block;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .status-normal {
        background: #065f46;
        color: #6ee7b7;
    }
    
    .status-warning {
        background: #92400e;
        color: #fcd34d;
    }
    
    .status-critical {
        background: #7f1d1d;
        color: #fca5a5;
    }
    
    .status-online {
        background: #065f46;
        color: #6ee7b7;
    }
    
    .status-offline {
        background: #7f1d1d;
        color: #fca5a5;
    }
    
    /* Data table styling */
    .dataframe {
        font-size: 0.9rem;
    }
    
    /* Divider */
    hr {
        border: none;
        border-top: 1px solid #334155;
        margin: 2rem 0;
    }
    
    /* Caption */
    .caption-text {
        color: #64748b;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize global queues
if 'global_queues_initialized' not in st.session_state:
    st.session_state.global_queues_initialized = True
    st.session_state.data_queue = Queue()
    st.session_state.alert_queue = Queue()

# Initialize session state
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = []
    st.session_state.alerts = []
    st.session_state.latest = {}
    st.session_state.mqtt_connected = False
    st.session_state.last_data_time = None

# Store queues as module-level variables
data_queue = st.session_state.data_queue
alert_queue = st.session_state.alert_queue

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

# Initialize MQTT client
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

# Process queued data
data_received = False
while not data_queue.empty():
    try:
        data = data_queue.get_nowait()
        data['timestamp'] = datetime.now().strftime("%H:%M:%S")
        st.session_state.sensor_data.append(data)
        st.session_state.latest = data
        st.session_state.last_data_time = datetime.now()
        data_received = True
        if len(st.session_state.sensor_data) > 100:
            st.session_state.sensor_data.pop(0)
    except:
        break

while not alert_queue.empty():
    try:
        data = alert_queue.get_nowait()
        data['time'] = datetime.now().strftime("%H:%M:%S")
        st.session_state.alerts.insert(0, data)
        if len(st.session_state.alerts) > 20:
            st.session_state.alerts.pop()
    except:
        break

# Header
st.markdown("""
<div class="main-header">
    <h1 class="main-title">INDUSTRIAL WORKER SAFETY MONITORING SYSTEM</h1>
    <div class="simulation-notice">
        <strong>Simulation:</strong> Visit <a href="https://wokwi.com/projects/447224581770989569" target="_blank">https://wokwi.com/projects/447224581770989569</a> and run the simulation
    </div>
</div>
""", unsafe_allow_html=True)

# System status bar
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    connection_status = "ONLINE" if st.session_state.mqtt_connected and st.session_state.latest else "OFFLINE"
    connection_class = "status-online" if connection_status == "ONLINE" else "status-offline"
    st.metric("SYSTEM STATUS", connection_status)

with col2:
    st.metric("ACTIVE ALERTS", len(st.session_state.alerts))

with col3:
    st.metric("DATA POINTS", len(st.session_state.sensor_data))

with col4:
    if st.session_state.last_data_time:
        elapsed = (datetime.now() - st.session_state.last_data_time).seconds
        st.metric("LAST UPDATE", f"{elapsed}s ago")
    else:
        st.metric("LAST UPDATE", "N/A")

with col5:
    if st.session_state.latest:
        temp = st.session_state.latest.get('body_temp', 0)
        hr = st.session_state.latest.get('heart_rate', 0)
        rad = st.session_state.latest.get('radiation_uSvh', 0)
        gas = st.session_state.latest.get('gas_ppm', 0)
        
        critical_count = sum([temp > 38.5, hr > 110, rad > 1.0, gas > 500])
        health_status = "CRITICAL" if critical_count > 0 else "NORMAL"
        st.metric("WORKER STATUS", health_status)
    else:
        st.metric("WORKER STATUS", "NO DATA")

# Critical alerts section
if st.session_state.alerts:
    st.markdown('<div class="alert-critical">⚠ CRITICAL ALERTS DETECTED</div>', unsafe_allow_html=True)
    for alert in st.session_state.alerts[:5]:
        alert_msgs = [f"{k.replace('_alert', '').upper()}: {v}" for k, v in alert.items() if k != 'time']
        st.markdown(f'<div class="alert-warning">[{alert["time"]}] {" | ".join(alert_msgs)}</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# Real-time sensor readings
latest = st.session_state.latest
if latest:
    st.markdown('<h2 class="section-header">Real-Time Biometric & Environmental Data</h2>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        temp = latest.get('body_temp', 0)
        temp_status = "CRITICAL" if temp > 38.5 else ("WARNING" if temp > 38.0 else "NORMAL")
        temp_class = f"status-{temp_status.lower()}"
        
        st.markdown(f"""
        <div class="sensor-card">
            <div class="sensor-title">BODY TEMPERATURE</div>
            <div class="sensor-value">{temp:.1f}°C</div>
            <span class="sensor-status {temp_class}">{temp_status}</span>
            <div class="caption-text">Normal Range: 36.5 - 37.5°C</div>
            <div class="caption-text">Sensor: DS18B20</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        hr = latest.get('heart_rate', 0)
        spo2 = latest.get('spo2', 0)
        hr_status = "CRITICAL" if hr > 110 else ("WARNING" if hr > 100 else "NORMAL")
        spo2_status = "CRITICAL" if spo2 < 90 else ("WARNING" if spo2 < 95 else "NORMAL")
        vital_status = "CRITICAL" if hr_status == "CRITICAL" or spo2_status == "CRITICAL" else hr_status
        vital_class = f"status-{vital_status.lower()}"
        
        st.markdown(f"""
        <div class="sensor-card">
            <div class="sensor-title">VITAL SIGNS</div>
            <div class="sensor-value">{hr} BPM</div>
            <div style="color: #94a3b8; font-size: 1.2rem; margin: 0.5rem 0;">SpO₂: {spo2}%</div>
            <span class="sensor-status {vital_class}">{vital_status}</span>
            <div class="caption-text">HR Normal: 60-100 BPM</div>
            <div class="caption-text">SpO₂ Normal: >95%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        rad_cpm = latest.get('radiation_cpm', 0)
        rad_uSv = latest.get('radiation_uSvh', 0)
        rad_status = "CRITICAL" if rad_uSv > 1.0 else ("WARNING" if rad_uSv > 0.5 else "NORMAL")
        rad_class = f"status-{rad_status.lower()}"
        
        st.markdown(f"""
        <div class="sensor-card">
            <div class="sensor-title">RADIATION EXPOSURE</div>
            <div class="sensor-value">{rad_uSv:.3f} µSv/h</div>
            <div style="color: #94a3b8; font-size: 1.2rem; margin: 0.5rem 0;">CPM: {rad_cpm:.0f}</div>
            <span class="sensor-status {rad_class}">{rad_status}</span>
            <div class="caption-text">Safe Limit: <1.0 µSv/h</div>
            <div class="caption-text">Sensor: Geiger Counter</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        gas = latest.get('gas_ppm', 0)
        fall = latest.get('fall_detected', False)
        gas_status = "CRITICAL" if gas > 500 else ("WARNING" if gas > 300 else "NORMAL")
        fall_status = "CRITICAL" if fall else "NORMAL"
        env_status = "CRITICAL" if gas_status == "CRITICAL" or fall_status == "CRITICAL" else gas_status
        env_class = f"status-{env_status.lower()}"
        
        st.markdown(f"""
        <div class="sensor-card">
            <div class="sensor-title">ENVIRONMENTAL HAZARDS</div>
            <div class="sensor-value">{gas:.0f} PPM</div>
            <div style="color: #94a3b8; font-size: 1.2rem; margin: 0.5rem 0;">Fall: {"DETECTED" if fall else "None"}</div>
            <span class="sensor-status {env_class}">{env_status}</span>
            <div class="caption-text">Gas Safe: <300 PPM</div>
            <div class="caption-text">Sensors: MQ-2, MPU6050</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Detailed motion data
    st.markdown('<h2 class="section-header">Accelerometer Data (Fall Detection System)</h2>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        accel_x = latest.get('accel_x', 0)
        st.metric("ACCEL X-AXIS", f"{accel_x:.2f} g")
    
    with col2:
        accel_y = latest.get('accel_y', 0)
        st.metric("ACCEL Y-AXIS", f"{accel_y:.2f} g")
    
    with col3:
        accel_z = latest.get('accel_z', 0)
        st.metric("ACCEL Z-AXIS", f"{accel_z:.2f} g")
    
    with col4:
        fall_detected = latest.get('fall_detected', False)
        fall_text = "FALL DETECTED" if fall_detected else "STABLE"
        st.metric("FALL STATUS", fall_text)

else:
    st.markdown('<div class="alert-warning">⚠ No sensor data available. Please ensure the simulation is running.</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# Statistics and history
col1, col2 = st.columns(2)

with col1:
    st.markdown('<h2 class="section-header">Alert History Log</h2>', unsafe_allow_html=True)
    if st.session_state.alerts:
        alerts_df = pd.DataFrame(st.session_state.alerts)
        st.dataframe(alerts_df, use_container_width=True, height=400)
    else:
        st.info("No alerts recorded")

with col2:
    st.markdown('<h2 class="section-header">Safety Statistics Summary</h2>', unsafe_allow_html=True)
    if st.session_state.sensor_data and len(st.session_state.sensor_data) > 0:
        df = pd.DataFrame(st.session_state.sensor_data)
        
        avg_temp = df['body_temp'].mean()
        max_temp = df['body_temp'].max()
        min_temp = df['body_temp'].min()
        
        avg_hr = df['heart_rate'].mean()
        max_hr = df['heart_rate'].max()
        
        max_radiation = df['radiation_uSvh'].max()
        avg_radiation = df['radiation_uSvh'].mean()
        
        max_gas = df['gas_ppm'].max()
        avg_gas = df['gas_ppm'].mean()
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Average Body Temp", f"{avg_temp:.1f}°C")
            st.metric("Max Body Temp", f"{max_temp:.1f}°C")
            st.metric("Average Heart Rate", f"{avg_hr:.0f} BPM")
            st.metric("Max Heart Rate", f"{max_hr:.0f} BPM")
        
        with col_b:
            st.metric("Max Radiation", f"{max_radiation:.3f} µSv/h")
            st.metric("Avg Radiation", f"{avg_radiation:.3f} µSv/h")
            st.metric("Max Gas Level", f"{max_gas:.0f} PPM")
            st.metric("Avg Gas Level", f"{avg_gas:.0f} PPM")
    else:
        st.info("Insufficient data for statistics")

# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(f'<div class="caption-text">System Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Data Refresh: Every 2 seconds | MQTT Broker: broker.emqx.io</div>', unsafe_allow_html=True)

# Auto-refresh
time.sleep(2)
st.rerun()