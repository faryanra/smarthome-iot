import requests, json

def get_json(url, timeout=3):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()

def put_json(url, body, timeout=3):
    h = {"Content-Type":"application/json"}
    r = requests.put(url, data=json.dumps(body), headers=h, timeout=timeout)
    try:
        return r.json()
    except:
        return {"ok": r.ok, "status": r.status_code}
