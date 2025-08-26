import json, time
import paho.mqtt.client as mqtt

def make_client(cid="sm_client"):
    c = mqtt.Client(client_id=cid, clean_session=True, protocol=mqtt.MQTTv311)
    return c

def connect_and_start(c, host, port):
    c.connect(host, int(port), keepalive=60)
    c.loop_start()

def stop_and_disconnect(c):
    try:
        c.loop_stop()
    finally:
        try: c.disconnect()
        except: pass

def quick_pub(host, port, topic, payload_dict, qos=1, retain=False):
    c = make_client("pub_"+str(time.time()))
    connect_and_start(c, host, port)
    c.publish(topic, json.dumps(payload_dict), qos=qos, retain=retain)
    time.sleep(0.2)
    stop_and_disconnect(c)
