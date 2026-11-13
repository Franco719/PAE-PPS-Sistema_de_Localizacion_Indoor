from src.web.api.esp32_receiver import bp as esp32_receiver
from src.web.controllers.sample_module import bp as muestreo
from src.web.controllers.train_module import bp as entrenamiento
from src.web.controllers.prediction_module import bp as prediccion


def register(app):
    app.register_blueprint(esp32_receiver)
    app.register_blueprint(muestreo)
    app.register_blueprint(entrenamiento)
    app.register_blueprint(prediccion)