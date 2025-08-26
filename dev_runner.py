import os, subprocess, time,sys

ROOT = os.path.abspath(".")
os.environ["PYTHONPATH"] = ROOT

SERVICES = [
    ("catalog",     "catalog/catalog_service.py"),
    ("controller",  "services/controller_service.py"),
    ("sensor_temp", "sensors/sensor_temp.py"),
    ("sensor_volt", "sensors/sensor_volt.py"),
    ("telegram",    "services/notification_service.py"),  
    ("actuator_fan",    "services/actuator_fan.py"),  
    ("actuator_cutoff", "services/actuator_cutoff.py"), 
    ("telegram_bot", "tools/telBot.py"),
]

def start_service(name, script):
    print(f"→ starting {name} ...")
    return subprocess.Popen([sys.executable, script], env=os.environ)

def main():
    print("[RUNNER] Starting all services...")
    processes = []
    for name, path in SERVICES:
        p = start_service(name, path)
        processes.append((name, p))
        time.sleep(0.5)

    print("✅ All services started. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[RUNNER] Stopping...")
        for name, p in processes:
            print(f"⛔ stopping {name} ...")
            p.terminate()
        print("[RUNNER] All stopped.")

if __name__ == "__main__":
    main()
