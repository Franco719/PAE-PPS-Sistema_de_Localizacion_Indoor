from flask import request, jsonify, Blueprint, render_template, redirect, url_for
from src.web.services.nn_service import NNService


bp = Blueprint("modulo_prediccion", __name__, url_prefix="/modulo_prediccion")


@bp.route('/', methods=['GET'])
def prediction_view():
    
    return render_template("prediction.html")
    
    
@bp.route("/predecir_posicion", methods=["POST"])
def predict():

    nn_service = NNService()
    prediction_kalman = nn_service.predict_position(nodo_id=1, filter_method="Kalman")
    prediction_median = nn_service.predict_position(nodo_id=1, filter_method="Median")
    prediction_mean = nn_service.predict_position(nodo_id=1, filter_method="Mean")
    prediction_ninguno = nn_service.predict_position(nodo_id=1, filter_method="Ninguno")

    return render_template(
        "prediction.html",
        prediction_kalman=prediction_kalman,
        prediction_median=prediction_median,
        prediction_mean=prediction_mean,
        prediction_ninguno=prediction_ninguno
    )