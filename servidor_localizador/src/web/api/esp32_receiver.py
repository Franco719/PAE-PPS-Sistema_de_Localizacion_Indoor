from flask import request, jsonify, Blueprint, render_template, redirect, url_for
from src.core.database.redis_client import db as redis_db, save_raw_reading
from src.core.filters.filter_manager import sample_filters
from src.core.database import db
from src.core.models.wifi_sample import WiFiSample
from src.web.schemas.esp32_receiver import wifi_records_schema
from marshmallow import ValidationError
from dotenv import load_dotenv
import os
from datetime import datetime

bp = Blueprint("api", __name__, url_prefix="/api")
load_dotenv()

@bp.route('/localizar', methods=['POST'])
def get_esp32_data():
    """Receibes Wi-Fi data recolected and sended by the ESP32 Microcontroler, and save it in Redis (if it's not
    taken samples for training) or in the Database (if it's taken samples for training)"""
    
    receibed_token = request.headers.get("API-Key")
    if receibed_token != os.environ.get("SECRET_KEY"):
        print("¡Intento de acceso no autorizado bloqueado!")
        return jsonify({"status": "error", "message": "No autorizado"}), 401
    
    if not request.is_json:
        return jsonify({"status": "error", "message": "Se esperaba formato JSON"}), 400

    try:
        validated_data = wifi_records_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"status": "error", "errors": err.messages}), 422
    
    
    #filter_method = redis_db.get("Filter_Method")
    #if filter_method == ("Median" or "Mean"):
    #    window = redis_db.get("Window")
    
    nodo_id = validated_data["nodo_id"]
    redis_nodo_id = redis_db.get("Nodo_ID")
    room = redis_db.get("Actual_Room")
    
    #print(f"ESP32 sala: {room}")
    
    sample_nodo = False if not redis_nodo_id else int(redis_nodo_id) == int(nodo_id)
    
    if not sample_nodo:
        # Modo producción: Solo guarda la lectura instantánea de Redis para localizar sin una nueva lectura
        redis_record = {"networks": validated_data["networks"], "scan_date": datetime.now().isoformat()}
        save_raw_reading(nodo_id, redis_record)
        print(f"📡 [Nodo {nodo_id}] Guardadas {len(validated_data["networks"])} redes validadas en Redis.")
    
    else:
        # Modo entrenamiento: Recorre la lista validada e iserta en la Base de Datos
        print(f"📥 [ENTRENAMIENTO - {room}] Guardando ráfaga en Base de Datos Local.")
        
        for network in validated_data["networks"]:

            rssi_raw = network.get("rssi")

            new_sample = WiFiSample.create_sample(
                nodo_id=nodo_id,
                room=room,
                ssid=network.get("ssid"),
                bssid=network.get("bssid"),
                rssi_raw=rssi_raw
            )
            
            rssi_filtered = sample_filters.filter(network.get("bssid"), rssi_raw)
            new_sample.update_filtered_rssi(rssi_filtered)
            
        # El commit lo hago acá para no hacer uno por cada muestra guardada.
        db.session.commit()
    
    return jsonify({"status": "success", "message": "Lectura almacenada con éxito"}), 200