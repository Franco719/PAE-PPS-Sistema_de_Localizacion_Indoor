from pathlib import Path
import joblib
import hashlib
from src.core.models.nn_training import Training #, TrainState
from dotenv import load_dotenv
import os
#from src.core.inference.nn_model import NNModel
#from src.core.database import db
#from src.core.models.wifi_sample import WiFiSample
import pandas as pd

load_dotenv()

class ModelManager:

    def __init__(self):
        models_path = os.environ.get("MODELS_PATH")

        if not models_path:
            raise ValueError("No está definida la variable MODELS_PATH.")

        self.models_directory = Path(models_path)
        self.models_directory.mkdir(parents=True, exist_ok=True)
        

    def save(self, training_id, model, label_encoder, bssids, filter_method, configuration):
        path = (
            self.models_directory
            / f"modelo_{training_id}.joblib"
        )
        
        if not path:
            raise ValueError("No está definida la variable MODELS_PATH.")

        artefact = {
            "model": model,
            "label_encoder": label_encoder,
            "bssids": list(bssids),
            "filter_method": filter_method,
            "configuration": configuration
        }

        joblib.dump(artefact, path)

        model_hash = self.calculate_hash(path)

        return {
            "path": str(path),
            "hash": model_hash
        }
    

    def get_nn(self, filter_method: str, training_id: int = None):
        
        if training_id:
            training = Training.get_training_by_id(training_id)
            
            if training is None:
                return {"success": False, "error": "No existe el entrenamiento en la base de datos."}
            
        else:
            try:
                training = Training.get_active_training(filter_method)
            except ValueError as e:
                return {"success": False, "error": e}


        if not training.model_path or not training.model_hash:
            return {"success": False, "error": "El entrenamiento no tiene un modelo registrado."}

        path = Path(training.model_path)

        if not path.is_file():
            return {"success": False, "error": "No se encontró el archivo del modelo."}

        actual_hash = self.calculate_hash(path)

        if actual_hash != training.model_hash:
            return {"success": False, "error": "El archivo del modelo fue alterado."}

        return {"success": True, "artefact": joblib.load(path)}
    
    
    def calculate_hash(self, ruta):
        sha256 = hashlib.sha256()

        with open(ruta, "rb") as file:
            for block in iter(lambda: file.read(8192), b""):
                sha256.update(block)

        return sha256.hexdigest()