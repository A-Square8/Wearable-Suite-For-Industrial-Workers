import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
from datetime import datetime
import time
from queue import Queue


st.set_page_config(
    page_title="Industrial Worker Safety Monitor",
    layout="wide",
    initial_sidebar_state="collapsed"
)


st.markdown("""
<style>
    /* Main theme - Clean dark background */
    .stApp {
        background: #0a0e27;
        color: #e4e4e7;
    }
    
    /* Header styling */
    .main-header {
        background: #111827;
        padding: 2rem 2.5rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
    }
    
    .main-title {
        color: #f1f5f9;
        font-size: 2.2rem;
        font-weight: 600;
        margin: 0;
        letter-spacing: 0.5px;
    }
    
    .simulation-notice {
        background: #1e293b;
        color: #cbd5e1;
        padding: 0.875rem 1.5rem;
        border-radius: 6px;
        margin-top: 1.25rem;
        font-size: 0.925rem;
        border-left: 3px solid #3b82f6;
    }
    
    .simulation-notice a {
        color: #60a5fa;
        text-decoration: none;
        font-weight: 500;
    }
    
    .simulation-notice a:hover {
        color: #93c5fd;
        text-decoration: underline;
    }
    
    /* Metric styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 600;
        color: #f1f5f9;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        font-weight: 500;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Alert styling - Minimal colors */
    .alert-critical {
        background: #1e293b;
        border: 1px solid #ef4444;
        border-left: 4px solid #ef4444;
        padding: 1rem 1.5rem;
        border-radius: 6px;
        margin: 1rem 0;
        color: #fecaca;
        font-weight: 500;
    }
    
    .alert-warning {
        background: #1e293b;
        border: 1px solid #475569;
        border-left: 3px solid #64748b;
        padding: 0.875rem 1.25rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        color: #cbd5e1;
        font-size: 0.9rem;
    }
    
    /* Section headers */
    .section-header {
        color: #f1f5f9;
        font-size: 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin: 2rem 0 1.25rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #334155;
    }
    
    /* Sensor cards - Clean minimal design */
    .sensor-card {
        background: #111827;
        padding: 1.75rem;
        border-radius: 8px;
        border: 1px solid #1e293b;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
        margin-bottom: 1rem;
        height: 100%;
    }
    
    .sensor-title {
        color: #94a3b8;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.75rem;
    }
    
    .sensor-value {
        color: #f1f5f9;
        font-size: 2.25rem;
        font-weight: 600;
        margin: 0.75rem 0;
        font-family: 'Courier New', monospace;
    }
    
    .sensor-subvalue {
        color: #94a3b8;
        font-size: 1.1rem;
        margin: 0.5rem 0;
        font-family: 'Courier New', monospace;
    }
    
    .sensor-status {
        font-size: 0.8rem;
        padding: 0.4rem 0.9rem;
        border-radius: 4px;
        display: inline-block;
        font-weight: 600;
        margin-top: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-normal {
        background: #1e293b;
        color: #94a3b8;
        border: 1px solid #334155;
    }
    
    .status-warning {
        background: #1e293b;
        color: #fbbf24;
        border: 1px solid #fbbf24;
    }
    
    .status-critical {
        background: #1e293b;
        color: #ef4444;
        border: 1px solid #ef4444;
    }
    
    .status-online {
        background: #1e293b;
        color: #10b981;
        border: 1px solid #10b981;
    }
    
    .status-offline {
        background: #1e293b;
        color: #ef4444;
        border: 1px solid #ef4444;
    }
    
    .caption-text {
        color: #64748b;
        font-size: 0.8rem;
        margin-top: 0.5rem;
        line-height: 1.5;
    }
    
    /* Divider */
    hr {
        border: none;
        border-top: 1px solid #1e293b;
        margin: 2.5rem 0;
    }
    
    /* Table styling */
    .dataframe {
        font-size: 0.875rem;
        background: #111827;
    }
    
    /* Info box */
    .stAlert {
        background: #1e293b;
        border: 1px solid #334155;
        color: #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)


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


st.markdown("""
<div class="main-header">
    <h1 class="main-title">INDUSTRIAL WORKER SAFETY MONITORING SYSTEM</h1>
    <div class="simulation-notice">
        <strong>Simulation:</strong> Visit <a href="https://wokwi.com/projects/447224581770989569" target="_blank">https://wokwi.com/projects/447224581770989569</a> and run the simulation
    </div>
</div>
""", unsafe_allow_html=True)


col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    connection_status = "ONLINE" if st.session_state.mqtt_connected and st.session_state.latest else "OFFLINE"
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

if st.session_state.alerts:
    st.markdown('<div class="alert-critical">CRITICAL ALERTS DETECTED</div>', unsafe_allow_html=True)
    for alert in st.session_state.alerts[:5]:
        alert_msgs = [f"{k.replace('_alert', '').upper()}: {v}" for k, v in alert.items() if k != 'time']
        st.markdown(f'<div class="alert-warning">[{alert["time"]}] {" | ".join(alert_msgs)}</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)


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
            <div class="caption-text">Sensor: DS18B20 Digital</div>
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
            <div class="sensor-subvalue">SpO₂: {spo2}%</div>
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
            <div class="sensor-subvalue">CPM: {rad_cpm:.0f}</div>
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
            <div class="sensor-subvalue">Fall: {"DETECTED" if fall else "None"}</div>
            <span class="sensor-status {env_class}">{env_status}</span>
            <div class="caption-text">Gas Safe: <300 PPM</div>
            <div class="caption-text">Sensors: MQ-2, MPU6050</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    

    st.markdown('<h2 class="section-header">Accelerometer Data - Fall Detection System</h2>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        accel_x = latest.get('accel_x', 0)
        st.metric("ACCEL X-AXIS", f"{accel_x:.3f} g")
    
    with col2:
        accel_y = latest.get('accel_y', 0)
        st.metric("ACCEL Y-AXIS", f"{accel_y:.3f} g")
    
    with col3:
        accel_z = latest.get('accel_z', 0)
        st.metric("ACCEL Z-AXIS", f"{accel_z:.3f} g")
    
    with col4:
        fall_detected = latest.get('fall_detected', False)
        fall_text = "FALL DETECTED" if fall_detected else "STABLE"
        st.metric("FALL STATUS", fall_text)

else:
    st.markdown('<div class="alert-warning">No sensor data available. Please ensure the simulation is running.</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)


col1, col2 = st.columns(2)

with col1:
    st.markdown('<h2 class="section-header">Alert History Log</h2>', unsafe_allow_html=True)
    if st.session_state.alerts:
        alerts_df = pd.DataFrame(st.session_state.alerts)
        st.dataframe(alerts_df, use_container_width=True, height=350)
    else:
        st.info("No alerts recorded")

with col2:
    st.markdown('<h2 class="section-header">Safety Statistics Summary</h2>', unsafe_allow_html=True)
    if st.session_state.sensor_data and len(st.session_state.sensor_data) > 0:
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
        st.info("Insufficient data for statistics")


st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(f'<div class="caption-text">System Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Refresh Rate: 2s | MQTT Broker: broker.emqx.io | Status: {"Connected" if st.session_state.mqtt_connected else "Disconnected"}</div>', unsafe_allow_html=True)


time.sleep(2)
st.rerun()
