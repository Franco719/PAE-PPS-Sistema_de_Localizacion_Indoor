import redis
import json
from config import REDIS_HOST, REDIS_PORT

# decode_responses=True traduce automáticamente los bytes de Redis a texto (strings) de Python
db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def save_raw_reading(nodo_id: int, wifi_data: list):
    """Saves in Redis the latest JSON receibed from the ESP32"""
    key = f"nodo:{nodo_id}:raw"
    db.set(key, json.dumps(wifi_data))

def get_raw_reading(nodo_id: int) -> list:
    """Get from Redis the latest array saved of Wi-Fi networks"""
    key = f"nodo:{nodo_id}:raw"
    data = db.get(key)
    return json.loads(data) if data else []
