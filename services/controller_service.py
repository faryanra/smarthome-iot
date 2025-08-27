import os, sys, time, json, requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import paho.mqtt.client as mqtt
from tools.MyInfluxDBclient import MyInfluxClient
influx = MyInfluxClient()

CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'config', 'server_config.json')
with open(CONFIG_FILE) as f:
    CONFIG = json.load(f)

CATALOG = CONFIG.get("catalog_url", "http://127.0.0.1:8081")
BROKER = CONFIG.get("broker", {"host": "test.mosquitto.org", "port": 1883})
ALERT_TOPIC = BROKER.get("alert_topic", "smarthome/alerts")

NOTIF_URL = CONFIG.get("telegram", {}).get("notification_url", "http://127.0.0.1:1505/notify")

TOPIC_BY_ID = {}
THRESH_BY_ID = {}
LAST_ALERTS = {}

def fetch_sensors():
    try:
        r = requests.get(f"{CATALOG}/sensors", timeout=3)
        js = r.json()
        if js.get("ok"):
            return [s["deviceID"] for s in js["sensors"]]
    except Exception as e:
        print("[ERROR] fetch_sensors:", e)
    return []

def fetch_config(sensor_id):
    try:
        r = requests.get(f"{CATALOG}/config/{sensor_id}", timeout=3)
        return r.json()
    except Exception as e:
        print("[ERROR] fetch_config:", e)
        return {}

def fetch_thresholds():
    try:
        r = requests.get(f"{CATALOG}/thresholds", timeout=3)
        js = r.json()
        if js.get("ok"):
            for k, v in js["thresholds"].items():
                THRESH_BY_ID[k] = v
            print("[THRESH] refreshed:", len(THRESH_BY_ID), "entries")
    except Exception as e:
        print("[ERROR] fetch_thresholds:", e)

def publish_alert(sensor_id, value, ts=None):
    payload = {"sensorId": sensor_id, "value": value}
    if ts:
        payload["ts"] = ts

    try:
        client.publish(ALERT_TOPIC, json.dumps(payload))
        print(f"📡 published MQTT alert → {sensor_id}")
    except Exception as e:
        print(f"[ERROR] MQTT publish failed for {sensor_id}: {e}")

    try:
        r = requests.post(NOTIF_URL, json=payload, timeout=3)
        print(f"📤 forwarded to NotificationService → {sensor_id} | status={r.status_code}")
    except Exception as e:
        print(f"[ERROR] forward to NotificationService failed → {e}")

def on_connect(client, userdata, flags, rc):
    print("[MQTT] Connected" if rc == 0 else f"[MQTT] Connect error: {rc}")
    client.subscribe("smarthome/#")
    print("[MQTT] Subscribed to smarthome/#")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        if "bn" in data and "e" in data:
            sensor_id = data["bn"].rstrip("/").split("/")[-1]
            entry = data["e"][0]
            value = entry["v"]
            ts = entry["t"]

            base_msg = f"{sensor_id} = {value:.2f}"

            if sensor_id not in LAST_ALERTS or LAST_ALERTS[sensor_id] != value:
                influx.write(sensor_id, value, ts)

            print(f"📩 incoming sensor_id: {sensor_id} | known: {sensor_id in THRESH_BY_ID}")
            th = THRESH_BY_ID.get(sensor_id)
            if th is None:
                print(f"⚪ {base_msg} (no threshold set)")
                return

            if value > th:
                if LAST_ALERTS.get(sensor_id) == value:
                    return  
                print(f"🚨 {base_msg} > {th} | ts: {ts}")
                publish_alert(sensor_id, value, ts)
                LAST_ALERTS[sensor_id] = value
            else:
                print(f"✅ {base_msg} ok")

        elif "sensorId" in data and "value" in data:
            sensor_id = data["sensorId"]
            value = data["value"]
            ts = data.get("ts", int(time.time()))
            print(f"⚠️ ALERT (received on MQTT) | Sensor: {sensor_id} | Value: {value} | Time: {ts}")

        else:
            pass

    except Exception as e:
        print(f"[ERROR] on_message: {e}")

client = mqtt.Client(client_id="controller", protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER["host"], BROKER["port"])
client.loop_start()

if __name__ == "__main__":
    print("[CTRL] booting...")
    sensors = fetch_sensors()
    for sid in sensors:
        cfg = fetch_config(sid)
        if "topic" in cfg:
            TOPIC_BY_ID[sid] = cfg["topic"]
        if "threshold" in cfg:
            THRESH_BY_ID[sid] = cfg["threshold"]
    fetch_thresholds()

    try:
        while True:
            time.sleep(2)
            fetch_thresholds()
    except KeyboardInterrupt:
        print("[CTRL] shutting down...")
        client.loop_stop()
