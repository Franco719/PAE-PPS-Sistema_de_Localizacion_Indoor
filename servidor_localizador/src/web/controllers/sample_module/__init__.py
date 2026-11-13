from flask import request, jsonify, Blueprint, render_template, redirect, url_for
#from src.core.filters.filter_factory import crear_filtro
#from src.core.database import db as pg_db
from src.core.database.redis_client import db as redis_db
from src.core.models.wifi_sample import WiFiSample
#from src.core.inference.modelo_red import ModeloNN
#from src.core.inference.gestor_modelos import GestorModelos
from src.web.schemas.sample_module import pre_sample_schema
from marshmallow import ValidationError
from src.core.filters.filter_manager import sample_filters
#import pandas as pd
#from servidor_localizador.src.core.task_entrenamiento import probar_celery


bp = Blueprint("modulo_muestreo", __name__, url_prefix="/modulo_muestreo")


@bp.route('/pre-muestreo', methods=['GET'])
def sample_view():
    """Get the pre-sample view by default to enter the room where the samples will be taken"""
    sample_filters.finish()
    redis_db.delete("Actual_Room")
    
    """gestor = GestorModelos()
    #gestor.entrenar()
    
    artefacto = gestor.cargar(1)
    print("Modelo cargado correctamente.")
    print("Claves del artefacto:", artefacto.keys())
    print("BSSID utilizados:", artefacto["bssids"])
    print("Método de filtrado:", artefacto["metodo_filtrado"])
    print("Configuración:", artefacto["configuracion"])
    
    resultado = gestor.probar_prediccion(1)

    print("Sala predicha:", resultado["sala_predicha"])
    print("Escaneo utilizado:", resultado["fecha_escaneo"])
    print("Método:", resultado["metodo_filtrado"])
    
    
    resultado = probar_celery.delay()
    
    print("ID de la tarea:", resultado.id)
    print("Estado inicial:", resultado.status)
    print("¿Terminó?:", resultado.ready())"""
    

    return render_template("sample.html")

@bp.route('/muestreo', methods=['POST'])
def start_sample():
    """Starts a sample session"""

    try:
        validated_data = pre_sample_schema.load(request.form)
    except ValidationError as err:
        return jsonify({
            "status": "error",
            "errors": err.messages
        }), 422

    room = validated_data["room_name"]
    #method = validated_data["filter_method"]
    nodo_id = validated_data["nodo_id"]
    window = validated_data.get("window")
    
    #filtro_muestreo.iniciar(metodo, ventana)

    if room:

        redis_db.set("Actual_Room", room, ex=300)
        redis_db.set("Nodo_ID", nodo_id, ex=300)
        #redis_db.set("Filter_Method", method, ex=300)

        if window is not None:
            redis_db.set("Window", window, ex=300)

        """filtro_actual = crear_filtro(
            metodo,
            ventana
        )"""
        sample_filters.start(nodo_id, room, window)

    return render_template(
        "sample.html",
        active_room=room
    )


@bp.route('/muestreo/redes_vivas', methods=['GET'])
def get_new_samples():
    """Get the latest 10 networks samples saved in the database for the room in sample session"""
    actual_room = redis_db.get("Actual_Room")
    nodo_id = redis_db.get("Nodo_ID")
    
    if not actual_room:

        return jsonify({
            "active": False,
            "samples": []
        })

    latest_samples = WiFiSample.query.filter_by(room=actual_room, nodo_id=nodo_id)\
                                        .order_by(WiFiSample.record_date.desc())\
                                        .limit(10).all()
                                        
    json_list = [{"ssid": sample.ssid, "rssi_raw": sample.rssi_raw, "bssid": sample.bssid} for sample in latest_samples]
    return jsonify({
        "active": True,
        "samples": json_list
    })


@bp.route('/muestreo/salir', methods=['POST'])
def exit_sample_session():
    """Stops the actual sample session when an unwanted exit of the page occurs"""
    redis_db.delete("Actual_Room")
    sample_filters.finish()
    return "", 204
