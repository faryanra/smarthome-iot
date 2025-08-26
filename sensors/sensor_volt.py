
import time, json, random, requests, threading
import paho.mqtt.client as mqtt

with open("config/server_config.json") as f:
    config = json.load(f)

CATALOG = config["catalog_url"]
BROKER = config["broker"]

known_ids = set()

client = mqtt.Client()
client.connect(BROKER["host"], BROKER["port"])
client.loop_start()

def start_publishing(sensor):
    sensor_id = sensor["deviceID"]
    topic = sensor["topic"]
    while True:
        value = round(random.uniform(215, 230), 2)
        msg = {
            "bn": f"http://smarthome.local/{sensor_id}/",
            "e": [{
                "n": "voltage",
                "u": "V",
                "t": int(time.time()),
                "v": value
            }]
        }
        print("PUB-V", msg)
        client.publish(topic, json.dumps(msg), qos=1)
        time.sleep(4)

while True:
    try:
        r = requests.get(f"{CATALOG}/sensors")
        sensors_all = r.json().get("sensors", [])
        new_sensors = [s for s in sensors_all if s["type"] == "voltage" and s["deviceID"] not in known_ids]
        for sensor in new_sensors:
            known_ids.add(sensor["deviceID"])
            t = threading.Thread(target=start_publishing, args=(sensor,))
            t.daemon = True
            t.start()
            print(f"🆕 started publishing for {sensor['deviceID']}")
    except Exception as e:
        print("[ERR] polling catalog:", e)

    time.sleep(10)

