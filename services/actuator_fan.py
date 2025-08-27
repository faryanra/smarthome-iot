import paho.mqtt.client as mqtt
import cherrypy, json, os, requests, time, threading

CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'config', 'server_config.json')
with open(CONFIG_FILE) as f:
    CONFIG = json.load(f)

CATALOG = CONFIG.get("catalog_url", "http://127.0.0.1:8081")
BROKER = CONFIG["broker"]
TOPIC = BROKER.get("alert_topic", "smarthome/alerts")
FAN_THRESHOLD = 28.0

registered = set()

def sync_actuators():
    global registered
    while True:
        try:
            sensors = requests.get(f"{CATALOG}/sensors", timeout=5).json().get("sensors", [])
            for s in sensors:
                if s.get("type") == "temperature":
                    act_id = "actuator_fan_" + s["deviceID"].split("temp_")[1]
                    if act_id not in registered:
                        my_info = {
                            "deviceID": act_id,
                            "type": "actuator",
                            "building": s["building"],
                            "floor": s["floor"],
                            "unit": s["unit"],
                            "topic": TOPIC,
                            "actions": ["fan_on", "fan_off"]
                        }
                        r = requests.post(f"{CATALOG}/sensors", json=my_info, timeout=5)
                        print(f"📡 Registered {act_id} →", r.status_code)
                        registered.add(act_id)
        except Exception as e:
            print("⚠️ Failed to sync fan actuators:", e)
        time.sleep(30)  # check every 30s


# --- MQTT Logic ---
def on_connect(c, u, f, rc):
    print("🌀 [FAN] connected", rc)
    c.subscribe(TOPIC)

def on_message(c, u, msg):
    try:
        d = json.loads(msg.payload.decode())
        sid, val = d.get("sensorId", ""), d.get("value", 0)
        if sid.startswith("temp_"):
            if val > FAN_THRESHOLD:
                print(f"🌀 FAN ON  → {sid} = {val}")
            else:
                print(f"🛑 FAN OFF → {sid} = {val}")
    except Exception as e:
        print("❌ [FAN] error:", e)

class HealthAPI:
    exposed = True
    @cherrypy.tools.json_out()
    def GET(self):
        return {"ok": True, "service": "fan", "ts": int(time.time())}


if __name__ == "__main__":
    t = threading.Thread(target=sync_actuators, daemon=True)
    t.start()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER["host"], BROKER["port"])
    client.loop_start()

    cherrypy.config.update({
        "server.socket_host": "0.0.0.0",
        "server.socket_port": 1506,
        "tools.encode.on": True,
        "tools.encode.encoding": "utf-8"
    })

    cherrypy.tree.mount(HealthAPI(), "/health", {"/": {"request.dispatch": cherrypy.dispatch.MethodDispatcher()}})
    cherrypy.engine.start()
    cherrypy.engine.block()
