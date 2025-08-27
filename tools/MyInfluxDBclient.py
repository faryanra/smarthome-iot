from influxdb_client import InfluxDBClient
import time,json,os

class MyInfluxClient:
    def __init__(self):
        CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'config', 'server_config.json')
        with open(CONFIG_FILE) as f:
            CONFIG = json.load(f)

        influx_config = CONFIG.get("influxdb", {})
        self.token = influx_config.get("token", "")
        self.org = influx_config.get("org", "")
        self.bucket = influx_config.get("bucket", "")
        self.url = influx_config.get("url", "")

        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api()

    def write(self, sensor_id, value, ts=None):
        if ts is None:
            ts = int(time.time())
        point = {
            "measurement": "sensor_data",
            "tags": {"sensor": sensor_id},
            "fields": {"value": float(value)},
            "time": int(ts * 1e9)  

        }
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=[point])
            print(f"📥 [INFLUX] saved: {sensor_id} = {value} @ {ts}")
        except Exception as e:
            print(f"❌ [INFLUX ERROR] {e}")
