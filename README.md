# 🏠 SmartHome IoT Platform

A simplified **IoT SmartHome platform** developed for academic use at Politecnico di Torino.  
It integrates **REST (CherryPy)** and **MQTT (paho-mqtt)** in a microservices architecture, with sensors, actuators, Telegram notifications, and InfluxDB storage.

---

## 🚀 Features
- **Catalog Service (REST)** → single source of truth for devices & thresholds.  
- **Controller Service** → subscribes to sensors, checks thresholds, stores to InfluxDB, publishes alerts.  
- **Sensors (MQTT)** → simulated temperature & voltage sensors.  
- **Actuators (MQTT)** → fan (temperature) & cutoff (voltage), auto-registered in the catalog.  
- **Notification Service** → forwards alerts to Telegram.  
- **Telegram Bot (Telepot)** → manage sensors, thresholds, and request reports.  
- **Dashboard (HTML/Chart.js)** → visualize sensor data.  
- **Diagram.png** → architecture overview.

---

## 🌐 MQTT Brokers
The system works with multiple brokers (tested successfully):  
- `test.mosquitto.org`  
- `broker.hivemq.com`  
- `mqtt.eclipseprojects.io`

---

## 🔧 Requirements
- Python 3.10+  
- Virtual environment recommended:
```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

---

## ▶️ Run Instructions
Start all services at once:
```bash
python dev_runner.py
```

Or run individual services for debugging:
```bash
python catalog/catalog_service.py
python services/controller_service.py
python sensors/sensor_temp.py
python sensors/sensor_volt.py
python services/alerts_listener.py
python services/actuator_fan.py
python services/actuator_cutoff.py
python services/notification_service.py
python tools/telBot.py
```

---

## 📊 Data & Reporting
- All sensor data stored in **InfluxDB Cloud**.  
- Reports available via **Telegram Bot** or **Dashboard (Chart.js)**.

---

## 👤 Author
- Project Owner: **Faryan**  
- Master’s Degree: *Digital Skills for Sustainable Societal Transitions, Politecnico di Torino*  
- Professors: Special thanks to **Pietro Rando Mazzarino** and **Lorenzo Bottaccioli**  

---

📷 *See `Diagram.png` in the root folder for architecture overview.*