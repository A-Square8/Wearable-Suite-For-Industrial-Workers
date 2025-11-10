Industrial Worker Safety Monitoring System
Live Dashboard

https://wearable-suite-for-industrial-workers-mx4qgznc8pvbmsfej5dudx.streamlit.app/

Overview

The Industrial Worker Safety Monitoring System is a real-time IoT platform designed to ensure worker safety by continuously monitoring critical health and environmental parameters through a wearable ESP32-based device.

The system integrates sensors for temperature, humidity, heart rate, motion, gas, and radiation detection. Data is transmitted securely to a cloud-based Streamlit dashboard using MQTT for real-time visualization, alerting, and analytics.

Features

Multi-sensor integration: DS18B20 (body temperature), MQ-35 (gas), MPU6050 (motion/fall), MAX30102 (heart rate/SpO₂), and GQ GMC-320 Plus (radiation).

Real-time monitoring: Streams live sensor readings via MQTT (broker.emqx.io) to the dashboard every 2 seconds.

Smart hazard detection: On-device threshold evaluation triggers alerts for gas leaks, high temperature, radiation exposure, or worker falls.

Interactive dashboard: Streamlit-based monitoring interface with alert visualization, historical logs, and statistics.

Scalable and modular: Works on local setups, simulation (WokWi), or physical deployments.

System Architecture
+---------------------------+      MQTT Broker      +-----------------------------+
|      ESP32 Wearable       | ---> broker.emqx.io -->|  Streamlit Web Dashboard    |
|---------------------------|                       |-----------------------------|
| DS18B20  : Body Temp      |                       | Real-time Sensor Metrics     |
| MAX30102 : Heart/SpO₂     |                       | Alert Notifications          |
| MQ-35    : Gas Detection  |                       | Safety Statistics Summary    |
| MPU6050  : Motion/Fall    |                       | Data Visualization & Logs    |
| GMC-320+ : Radiation      |                       | Downloadable Data Reports    |
+---------------------------+                       +-----------------------------+

Technology Stack

Hardware: ESP32, DS18B20, MQ-35, MPU6050, MAX30102, GQ GMC-320 Plus
Software: Arduino IDE, WokWi Simulator
Protocols: MQTT, JSON, Wi-Fi (802.11)
Backend: Paho MQTT, Python
Frontend: Streamlit Dashboard (Dark Mode UI)

Repository Structure
Industrial-Worker-Safety/
│
├── esp32_firmware/
│   └── esp32_worker_safety.ino        # Embedded firmware with MQTT alerts
│
├── dashboard/
│   └── app.py                         # Streamlit dashboard for visualization
│
├── requirements.txt                   # Python dependencies
├── README.md                          # Documentation
└── LICENSE                            # Optional license

Setup and Installation
1. ESP32 Firmware

Open the .ino file in Arduino IDE or WokWi.

Configure Wi-Fi credentials and MQTT broker (default: broker.emqx.io, port 1883).

Upload to ESP32 or run simulation using WokWi
.

2. Python Dashboard

Clone this repository:

git clone https://github.com/A-Square8/Smart-Suit-for-Industrial-Workers.git
cd Smart-Suit-for-Industrial-Workers/dashboard


Install dependencies:

pip install -r requirements.txt


Run the Streamlit dashboard:

streamlit run app.py

How It Works

ESP32 collects sensor data (temperature, heart rate, gas, radiation, motion).

MQTT client publishes data to topic worker/safety/data.

Dashboard subscribes to both worker/safety/data and worker/safety/alert.

Hazard conditions trigger alerts, stored and visualized on the Streamlit dashboard.

Data analytics module computes averages, max/min, and summary statistics.

Alert Conditions
Parameter	Sensor	Condition for Alert
Body Temperature	DS18B20	> 38.5 °C
Gas Level	MQ-35	> 500 PPM
Heart Rate	MAX30102	> 110 BPM
Radiation Level	GQ GMC-320 Plus	> 1.0 µSv/h
Fall Detection	MPU6050	Sudden acceleration change
Example Output

Metrics Displayed:

Worker Status: Normal / Critical

Body Temperature, Heart Rate, Gas PPM, Radiation µSv/h

Alerts History Log

Statistical Summary (Average, Max)
