# telBot.py - Telepot SmartHome Bot (Simplified CRUD + Report)
import os, json, time, requests, telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup

# === Load config ===
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'server_config.json'))
with open(CONFIG_PATH) as f: CONFIG = json.load(f)

CATALOG_URL = CONFIG.get("catalog_url", "http://localhost:8081")
BOT_TOKEN = CONFIG["telegram"]["bot_token"]
INFLUX = CONFIG.get("influxdb", {})
INFLUX_URL = f"{INFLUX.get('url')}/api/v2/query"
INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET = INFLUX["token"], INFLUX["org"], INFLUX["bucket"]

bot = telepot.Bot(BOT_TOKEN)
STATE = {}

# === Menu ===
MENU = ReplyKeyboardMarkup(keyboard=[
    ["➕ Add Sensor", "✏ Edit Sensor"],
    ["📊 Report", "📡 Project Info"],
    ["ℹ️ Help"]
], resize_keyboard=True)

# === Catalog ops ===
def get_sensors(): 
    try: return requests.get(f"{CATALOG_URL}/sensors").json().get("sensors", [])
    except: return []

def add_or_update(cid, mode, data):
    device_id = data.get("deviceID") or f"{data['type'][:4]}_{data['building']}_{data['floor']}_{data['unit']}"
    topic = f"smarthome/{data['building']}/{data['floor']}/{data['unit']}/{data['type'][:4]}"
    payload = {"deviceID": device_id, **data, "topic": topic}
    url = f"{CATALOG_URL}/sensors" + (f"/{device_id}" if mode=="update" else "")
    r = requests.put(url, json=payload) if mode=="update" else requests.post(url, json=payload)
    ok = r.ok and r.json().get("ok")
    bot.sendMessage(cid, f"{'✅' if ok else '❌'} Sensor {device_id} {mode}d.")

def delete_sensor(cid, deviceID):
    r = requests.delete(f"{CATALOG_URL}/sensors/{deviceID}")
    ok = r.ok and r.json().get("ok")
    bot.sendMessage(cid, f"{'🗑 Deleted' if ok else '❌ Failed'} {deviceID}")

# === Bot handlers ===
def on_start(cid): STATE.pop(cid, None); bot.sendMessage(cid,"👋 Welcome!",reply_markup=MENU)
def on_help(cid): bot.sendMessage(cid,"➕ Add Sensor\n✏ Edit Sensor\n🗑 Delete Sensor\n📊 Report\n📡 Project Info",reply_markup=MENU)

def on_project(cid):
    try: d=requests.get(f"{CATALOG_URL}/project").json(); bot.sendMessage(cid,f"📡 {d['project_name']} by {d['project_owner']}")
    except: bot.sendMessage(cid,"❌ Failed project info")

def on_sensors(cid):
    sensors=get_sensors()
    if not sensors: return bot.sendMessage(cid,"⚠️ No sensors.")
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=s['deviceID'],callback_data=f"manage:{s['deviceID']}")]for s in sensors])
    bot.sendMessage(cid,"📋 Choose sensor:",reply_markup=kb)

def on_report(cid):
    try:
        q={"query":f'from(bucket:"{INFLUX_BUCKET}") |> range(start: -1h) |> filter(fn:(r)=>r._field=="value") |> last()'}
        h={"Authorization":f"Token {INFLUX_TOKEN}","Content-Type":"application/json","Accept":"application/csv"}
        r=requests.post(f"{INFLUX_URL}?org={INFLUX_ORG}",headers=h,json=q,timeout=10)
        vals=[]; idx_val=idx_sensor=None
        for line in r.text.splitlines():
            if line.startswith("#"): continue
            cols=line.split(",")
            if "sensor" in cols and "_value" in cols: idx_sensor,idx_val=cols.index("sensor"),cols.index("_value"); continue
            if idx_sensor!=None and len(cols)>max(idx_sensor,idx_val):
                s,v=cols[idx_sensor],cols[idx_val]
                emoji="🌡" if s.startswith("temp") else "⚡"; vals.append(f"{emoji} {s}={v}")
        bot.sendMessage(cid,"📊 Report:\n"+("\n".join(vals) if vals else "No data"))
    except Exception as e: bot.sendMessage(cid,f"⚠️ {e}")

# === Add flow ===
def ask_unit(cid,data): STATE[cid]={"mode":data["mode"],"data":data}; bot.sendMessage(cid,"🚪 Enter unit (e.g., U1):")
def continue_steps(cid, msg):
    st = STATE[cid]
    d = st["data"]

    if "building" not in d:
        d["building"] = msg
        bot.sendMessage(cid, "🏬 Enter floor (e.g., F1):")
    elif "floor" not in d:
        d["floor"] = msg
        bot.sendMessage(cid, "🚪 Enter unit (e.g., U1):")
    elif "unit" not in d:
        d["unit"] = msg
        d["threshold"] = 28.0 if d["type"] == "temperature" else 220.0
        add_or_update(cid, st["mode"], d)
        STATE.pop(cid, None)

# === Callbacks ===
def on_callback(msg):
    qid,cid,data=telepot.glance(msg,flavor="callback_query")
    if data.startswith("manage:"):
        dev=data.split(":")[1]
        kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✏ Edit",callback_data=f"update:{dev}")],
                                                 [InlineKeyboardButton(text="🗑 Delete",callback_data=f"delete:{dev}")]])
        bot.sendMessage(cid,f"Manage {dev}:",reply_markup=kb)
    elif data.startswith("update:"):
        STATE[cid]={"mode":"update","data":{"deviceID":data.split(":")[1],"type":"temperature"}}; bot.sendMessage(cid,"🏢 Enter building:")
    elif data.startswith("delete:"): delete_sensor(cid,data.split(":")[1])
    elif data.startswith("type:"): t=data.split(":")[1]; STATE[cid]={"mode":"add","data":{"type":t}}; bot.sendMessage(cid,"🏢 Enter building:")

# === Router ===
def handle(msg):
    ctype,chat,cid=telepot.glance(msg)
    if ctype!="text": return
    t=msg["text"]
    if t in ["/start","Start"]: on_start(cid)
    elif t in ["/help","ℹ️ Help"]: on_help(cid)
    elif t in ["📡 Project Info","/project"]: on_project(cid)
    elif t in ["✏ Edit Sensor","/sensors"]: on_sensors(cid)
    elif t in ["➕ Add Sensor","/addsensor"]:
        kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🌡 Temp",callback_data="type:temperature")],
                                                 [InlineKeyboardButton(text="⚡ Volt",callback_data="type:voltage")]])
        bot.sendMessage(cid,"Select type:",reply_markup=kb)
    elif t in ["📊 Report"]: on_report(cid)
    elif cid in STATE: continue_steps(cid,t)
    else: bot.sendMessage(cid,"❓ Unknown.")

# === Run ===
MessageLoop(bot,{'chat':handle,'callback_query':on_callback}).run_as_thread()
print("🤖 SmartHome Bot running...")
while True: time.sleep(10)
