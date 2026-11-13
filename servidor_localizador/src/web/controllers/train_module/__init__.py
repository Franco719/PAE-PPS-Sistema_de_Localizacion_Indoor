from flask import current_app, flash
from flask import request, jsonify, Blueprint, render_template, redirect, url_for
from src.core.database.redis_client import db as redis_db
#from src.core.filters.filter_manager import prediction_filter
from src.core.inference.models_manager import ModelManager
from src.web.services.nn_service import NNService
from src.core.models.nn_training import Training
from src.web.schemas.training_module import pre_training_schema, change_name_schema
from marshmallow import ValidationError


bp = Blueprint("modulo_entrenamiento", __name__, url_prefix="/modulo_entrenamiento")


@bp.route('/entrenamiento', methods=['GET'])
def training_view():
    """Gets the pre-training view for default to train a nn by a selected filter method"""
    
    trainings = Training.get_trainings()

    return render_template("training.html", trainings=trainings)


@bp.route('/entrenar', methods=['POST'])
def training():
    try:
        validated_data = pre_training_schema.load(request.form)
    except ValidationError as err:
        for messages in err.messages.values():
            for message in messages:
                flash(message, "error")

        return redirect(url_for("modulo_entrenamiento.training_view"))

    method = validated_data["filter_method"]
    name = validated_data["training_name"]

    try:
        NNService().start_training(method, name)
    except Exception:
        current_app.logger.exception(
            "No se pudo iniciar el entrenamiento."
        )
        flash("No se pudo iniciar el entrenamiento. Revisá los registros del servidor.", "error")
        return redirect(url_for("modulo_entrenamiento.training_view"))

    flash("El entrenamiento fue enviado a la cola de ejecución.", "success")

    return redirect(url_for("modulo_entrenamiento.training_view"))


@bp.route('/eliminar_entrenamiento/<training_id>', methods=['POST'])
def delete_training(training_id: int):
    
    training = Training.get_training_by_id(training_id)
    
    if training is None:
        flash("No se encontró el entrenamiento que intentás eliminar.", "error")
        return redirect(url_for("modulo_entrenamiento.training_view"))

    Training.delete_training(training_id)

    flash("El entrenamiento fue eliminado.", "success")

    return redirect(url_for("modulo_entrenamiento.training_view"))


@bp.route('/cambiar_nombre_entrenamiento/<training_id>', methods=['POST'])
def change_name(training_id: int):
    try:
        validated_data = change_name_schema.load(request.form)
    except ValidationError as err:
        for messages in err.messages.values():
            for message in messages:
                flash(message, "error")
        
        return redirect(url_for("modulo_entrenamiento.training_view"))

    training = Training.get_training_by_id(
        training_id
    )

    if training is None:
        flash("No se encontró el entrenamiento solicitado.", "error")
        return redirect(url_for("modulo_entrenamiento.training_view"))

    training.update_training(
        name=validated_data["new_name"]
    )

    flash("El nombre del entrenamiento se actualizó correctamente.", "success")

    return redirect(url_for("modulo_entrenamiento.training_view"))


@bp.route('/toggle_activacion_modelo/<training_id>', methods=['POST'])
def toggle_model_activation(training_id: int):
    training = Training.get_training_by_id(
        training_id
    )

    if training is None:
        flash("No se encontró el entrenamiento solicitado.", "error")
        return redirect(url_for("modulo_entrenamiento.training_view"))

    new_state = not training.active

    training.update_training(active=new_state)

    if new_state:
        flash("El modelo se activó correctamente.", "success")
    else:
        flash("El modelo se desactivó correctamente.", "success")
        
    return redirect(url_for("modulo_entrenamiento.training_view"))