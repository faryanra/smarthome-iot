# Endpoints:
#  GET /sensors?offset=&limit=
#  POST /sensors
#  PUT /sensors/{sensor_id}
#  DELETE /sensors/{sensor_id}
#  GET /config/{sensor_id}
#  GET /thresholds
#  GET /thresholds/{sensor_id}
#  PUT /thresholds/{sensor_id}  body: {"value": 28}

import cherrypy, json, os, threading

BASE = os.path.dirname(os.path.dirname(__file__))
CATALOG_FILE = os.path.join(BASE, "config", "catalog.json")
_lock = threading.Lock()

def _load():
    if not os.path.exists(CATALOG_FILE):
        with open(CATALOG_FILE, "w", encoding="utf-8") as f:
            json.dump({"project_name": "SmartHome", "project_owner": "Faryan",
                    "broker": {"host": "test.mosquitto.org", "port": 1883},
                    "device_list": []}, f, indent=2)
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(js):
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(js, f, indent=2)

class ProjectAPI(object):
    exposed = True
    def GET(self):
        cat = _load()
        return json.dumps({
            "ok": True,
            "project_name": cat.get("project_name"),
            "project_owner": cat.get("project_owner"),
            "broker": cat.get("broker", {})
        })

class SensorsAPI(object):
    exposed = True

    def GET(self, *path, **query):
        cat = _load()
        items = cat.get("device_list", [])
        try: off = int(query.get("offset", 0))
        except: off = 0
        try: lim = int(query.get("limit", len(items)))
        except: lim = len(items)
        return json.dumps({"ok": True, "count": len(items), "sensors": items[off:off+lim]})

    @cherrypy.tools.json_in()
    def POST(self, *_, **__):
        try:
            new_sensor = cherrypy.request.json
            cat = _load()

            cat["device_list"] = [
                d for d in cat.get("device_list", [])
                if d.get("deviceID") != new_sensor.get("deviceID")
            ]

            cat["device_list"].append(new_sensor)
            _save(cat)
            return json.dumps({"ok": True, "added": new_sensor})

        except Exception as e:
            return json.dumps({"ok": False, "err": str(e)})

    def DELETE(self, sensor_id=None, **_):
        with _lock:
            cat = _load()
            before = len(cat.get("device_list", []))
            cat["device_list"] = [d for d in cat.get("device_list", []) if d.get("deviceID") != sensor_id]
            if len(cat["device_list"]) < before:
                _save(cat)
                return json.dumps({"ok": True, "deleted": sensor_id})
        return json.dumps({"ok": False, "err": "not found"})

    @cherrypy.tools.json_in()
    def PUT(self, sensor_id=None, **_):
        body = cherrypy.request.json
        with _lock:
            cat = _load()
            for it in cat.get("device_list", []):
                if it.get("deviceID") == sensor_id:
                    it.update(body)   
                    _save(cat)
                    return json.dumps({"ok": True, "updated": it})
        return json.dumps({"ok": False, "err": "not found"})

class ConfigAPI(object):
    exposed = True
    def GET(self, sensor_id=None, **_):
        if not sensor_id:
            return json.dumps({"ok": False, "err": "missing sensor_id"})
        cat = _load()
        for it in cat.get("device_list", []):
            if it.get("deviceID")==sensor_id:
                return json.dumps({
                "ok": True,
                "deviceID": sensor_id,
                "topic": it["topic"],
                "threshold": it.get("threshold", None),
                "building": it.get("building", "-"),
                "floor": it.get("floor", "-"),
                "unit": it.get("unit", "-")
            })
        return json.dumps({"ok": False, "err": "not found"})

class ThresholdsAPI(object):
    exposed = True
    def GET(self, sensor_id=None, **_):
        cat = _load()
        if sensor_id:
            for it in cat.get("device_list", []):
                if it.get("deviceID")==sensor_id:
                    return json.dumps({"ok": True, "sensorId": sensor_id, "value": it.get("threshold", None)})
            return json.dumps({"ok": False, "err": "not found"})
        th = {it["deviceID"]: it.get("threshold", None) for it in cat.get("device_list", [])}
        return json.dumps({"ok": True, "thresholds": th})
    def PUT(self, sensor_id=None, **_):
        raw = cherrypy.request.body.read()
        try:
            body = json.loads(raw) if raw else {}
            newv = float(body.get("value"))
        except:
            return json.dumps({"ok": False, "err": "bad body"})
        with _lock:
            cat = _load()
            for it in cat.get("device_list", []):
                if it.get("deviceID")==sensor_id:
                    it["threshold"] = newv
                    _save(cat)
                    return json.dumps({"ok": True, "sensorId": sensor_id, "new": newv})
        return json.dumps({"ok": False, "err": "not found"})

class Root(object):
    exposed = True
    def __init__(self):
        self.sensors = SensorsAPI()
        self.config = ConfigAPI()
        self.thresholds = ThresholdsAPI()
        self.project = ProjectAPI()

def run(port=8081):
    conf = {'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}}
    root = Root()
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': int(port)
    })
    cherrypy.quickstart(root, '/', conf)

if __name__ == "__main__":
    run()