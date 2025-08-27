import cherrypy, time, json, requests, os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'config', 'server_config.json')
with open(CONFIG_FILE) as f:
    CONFIG = json.load(f)

TELEGRAM = CONFIG.get("telegram", {})


class NotifyAPI:
    exposed = True

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        body = cherrypy.request.json or {}
        sensor_id = body.get("sensorId")
        value = body.get("value")
        ts = body.get("ts", int(time.time()))

        msg = f"🚨 ALERT\nSensor: {sensor_id}\nValue: {value}\nTime: {ts}"

        bot_token = TELEGRAM.get("bot_token")
        chat_id = TELEGRAM.get("chat_id")
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        try:
            r = requests.post(url, json={"chat_id": chat_id, "text": msg}, timeout=5)
            print(f"📤 Telegram → {sensor_id} | Status={r.status_code}")
            return {"ok": True, "status": r.status_code}
        except Exception as e:
            print(f"[ERROR] Telegram failed → {e}")
            return {"ok": False, "error": str(e)}


class HealthAPI:
    exposed = True

    @cherrypy.tools.json_out()
    def GET(self):
        return {"ok": True, "service": "notification", "ts": int(time.time())}


if __name__ == "__main__":
    cherrypy.config.update({
        "server.socket_host": "0.0.0.0",
        "server.socket_port": 1505,
        "tools.encode.on": True,
        "tools.encode.encoding": "utf-8"
    })

    cherrypy.tree.mount(NotifyAPI(), "/notify", {"/": {"request.dispatch": cherrypy.dispatch.MethodDispatcher()}})
    cherrypy.tree.mount(HealthAPI(), "/health", {"/": {"request.dispatch": cherrypy.dispatch.MethodDispatcher()}})

    cherrypy.engine.start()
    cherrypy.engine.block()
