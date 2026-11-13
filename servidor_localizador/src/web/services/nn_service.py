from src.core.inference.nn_model import NNModel
#from src.core.models.wifi_sample import WiFiSample
from src.core.models.nn_training import Training, TrainingState
import pandas as pd
from src.core.inference.models_manager import ModelManager
from src.core.training_task import execute_training
from src.core.database import redis_client
#from src.core.filters.filter_manager import prediction_filter
from datetime import datetime


class NNService:
    manager = ModelManager()

    def start_training(self, filter_method: str, Training_name: str):
        # Registrar la tarea y enviarla al ejecutor.
        training = Training.create_training(
            filter_method = filter_method,
            name = Training_name
        )
        
        execute_training.delay(training.id)
        # Devolver el identificador sin esperar el resultado.
        return training.id
    
    
    def training_nn(self, training_id: int):
        trainment = Training.get_training_by_id(training_id)
        
        if not trainment:
            errors = ["No se ha encontrado el entrenamiento en la Base de Datos"]
            trainment.abort_training(errors)
            return {
                "success": False,
                "training_id": training_id
            }
        
        model = NNModel()
        dataframe = model.create_dataframe(trainment.filter_method)
        
        if not dataframe["success"]:
            trainment.abort_training(dataframe["message"])
            return {
                "success": False,
                "training_id": training_id
            } 
        
        training_data = {
            "state": TrainingState(dataframe["state"]),
            "cant_samples_available": dataframe["cant_samples_available"],
            "cant_scans_generated": dataframe["cant_scans_generated"],
            "cant_bssids": dataframe["cant_characteristics"],
            "cant_rooms": dataframe["cant_rooms"],
        }
        
        trainment.update_training(**training_data)
        
        preparation = model.prepare_training()
        
        if not preparation["success"]:
            trainment.abort_training(preparation["message"])
            return {
                "success": False,
                "training_id": training_id
            }

        training = model.training()
        
        if not training["success"]:
            trainment.abort_training(training["message"]) 
            return {
                "success": False,
                "training_id": training_id
            }
        
        training_data = {
            "iterations": training["iterations"],
            "loss": training["loss"]
        }
        
        trainment.update_training(**training_data)
        
        assessment = model.assessment()
        
        if not assessment["success"]:
            trainment.abort_training(assessment["message"]) 
            return {
                "success": False,
                "training_id": training_id
            }
        
        training_data = {
            "accuracy": assessment["accuracy"],
        }
        
        trainment.update_training(**training_data)

        # Obtener los BSSID en el mismo orden que las características de entrada.
        bssids = list(model.x.columns)

        # Obtener la configuración utilizada por la red.
        configuration = model.model.get_params()

        # Guardar el modelo y calcular su hash.
        saved_result = self.manager.save(
            training_id=trainment.id,
            model=model.model,
            label_encoder=model.label_encoder,
            bssids=bssids,
            filter_method=trainment.filter_method,
            configuration=configuration
        )

        # Registrar la ubicación y el hash del archivo en PostgreSQL.
        training_data = {
            "model_path": saved_result["path"],
            "model_hash": saved_result["hash"],
            "state": TrainingState.FINISHED,
            "finish_date": datetime.now()
        }
        
        trainment.update_training(**training_data)
        
        return {
            "success": True,
            "training_id": training_id
        }
            
    
    def prepare_prediction_entrance(self, scan, bssids):

        networks = {
            network["bssid"]: network["rssi"]
            for network in scan
        }

        data = {
            bssid: networks.get(bssid, -100)
            for bssid in bssids
        }

        return pd.DataFrame([data], columns=bssids)
    
    
    def predict_position(self, nodo_id: int, filter_method: str, training_id: int = None):
        # 1. Cargar el artefacto guardado.
        manager = ModelManager()
        file_charge = manager.get_nn(filter_method, training_id)
        
        if file_charge["success"]:
            
            artefact = file_charge["artefact"]

            model = artefact["model"]
            label_encoder = artefact["label_encoder"]
            bssids = artefact["bssids"]
            filter_method = artefact["filter_method"]

            # 2. Recuperar el último escaneo.
            redis_records = redis_client.get_raw_reading(nodo_id)
            redis_networks = redis_records["networks"]
            
            if len(redis_networks) > 0:

                # 3. Preparar la entrada.
                #filtro = filtro_prediccion.iniciar(filter_method, nodo_id)
                
                samples = []
                
                for network in redis_networks:
                
                    #rssi_puro = red.get("rssi")

                    """rssi_filtrado = filtro.filtrar(
                        red.get("bssid"),
                        rssi_puro
                    )"""
                    
                    samples.append({
                        "bssid": network.get("bssid"),
                        "rssi": network.get("rssi")
                    })
                
                entrance_data = self.prepare_prediction_entrance(samples, bssids)

                # 4. Ejecutar la predicción.
                prediction = model.predict(entrance_data)

                # 5. Convertir la clase numérica en el nombre de la sala.
                room = label_encoder.inverse_transform(
                    prediction.astype(int)
                )[0]

                return {
                    "prediction_success": True,
                    "predicted_room": room,
                    "scan_date": datetime.fromisoformat(redis_records["scan_date"]),
                    "filter_method": filter_method
                }
            
            else:
                return {
                    "prediction_success": False,
                    "error": f"No hay registros de comunicacion del nodo con id {nodo_id}"
                }
        
        else:
            return {
                "prediction_success": False,
                "error": file_charge["error"]
            }