import pandas as pd
#from pandas import DataFrame
from src.core.models.wifi_sample import WiFiSample
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report
#from src.core.filters.filter_manager import kalman_sample_filter


class NNModel:

    CANT_SAMPLES_REQUIRED = 100
    
    FILTER_COLUMNS = {
        "Kalman": "rssi_kalman_filtered",
        "Median": "rssi_median_filtered",
        "Mean": "rssi_mean_filtered",
        "Ninguno": "rssi_raw"
    } 

    def __init__(self):
        self.df = None
        self.x = None
        self.y = None
        self.x_train = None
        self.x_test = None
        self.y_train = None
        self.y_test = None
        self.label_encoder = None
        self.model = None

    def create_dataframe(self, filter_method):
        filter_column = self.FILTER_COLUMNS.get(filter_method)

        if filter_column is None:
            return {
                "success": False,
                "stage": "data_preparation",
                "state": "invalid_filter",
                "message": f"Método de filtrado no válido: {filter_method}."
            }

        samples = WiFiSample.get_samples_order_by_time()

        cant_samples = len(samples)

        if cant_samples < self.CANT_SAMPLES_REQUIRED:
            return {
                "success": False,
                "stage": "data_preparation",
                "state": "insufficient_data",
                "message": [
                    f"Se necesitan al menos {self.CANT_SAMPLES_REQUIRED} muestras. Se encontraron {cant_samples}."
                ],
                "cant_samples_availables": cant_samples,
                "cant_samples_required": self.CANT_SAMPLES_REQUIRED
            }

        self.df = pd.DataFrame([
            {
                "room": sample.room,
                "record_date": sample.record_date,
                "bssid": sample.bssid,
                "rssi_filtered": getattr(sample, filter_column)
            }
            for sample in samples
            if getattr(sample, filter_column) is not None
        ])

        self.df["scan_date"] = (self.df["record_date"].dt.floor("s"))

        self.df = self.df.pivot_table(
            index=["scan_date", "room"],
            columns="bssid",
            values="rssi_filtered",
            aggfunc="mean"
        ).reset_index()

        self.df = self.df.fillna(-100)

        # Información resumida para el servicio.
        rooms = self.df["room"].str.strip()

        self.y = rooms

        return {
            "success": True,
            "stage": "data_preparation",
            "state": "finished",
            "message": "DataFrame preparado correctmente.",
            "cant_samples_available": cant_samples,
            "cant_scans_generated": len(self.df),
            "cant_characteristics": len(
                self.df.drop(columns=["scan_date", "room"]).columns
            ),
            "cant_rooms": int(rooms.nunique()),
            "rooms": sorted(rooms.unique().tolist())
        }

    def prepare_training(self):
        """prepare and check the dataframe for the train"""
        if self.df is None:
            return {
                "success": False,
                "stage": "train_preparation",
                "state": "error",
                "message": "Primero debe prepararse el DataFrame."
            }

        self.x = self.df.drop(
            columns=["scan_date", "room"]
        )

        self.y = self.df["room"].str.strip()

        # Verificar que cada clase tenga suficientes muestras para dividir los datos de manera estratificada.
        distribution = self.y.value_counts()

        insufficient_classes = distribution[distribution < 2]

        if not insufficient_classes.empty:
            return {
                "success": False,
                "stage": "train_preparation",
                "state": "insufficient_data",
                "message": (
                    "Cada sala necesita al menos dos muestras para realizar la división estratificada."
                ),
                "insufficient_rooms": {
                    room: int(cant)
                    for room, cant in insufficient_classes.items()
                }
            }

        self.x_train, self.x_test, self.y_train, self.y_test = (
            train_test_split(
                self.x,
                self.y,
                test_size=0.2,
                random_state=42,
                stratify=self.y
            )
        )

        self.label_encoder = LabelEncoder()

        self.y_train = self.label_encoder.fit_transform(
            self.y_train
        )

        self.y_test = self.label_encoder.transform(
            self.y_test
        )

        return {
            "success": True,
            "stage": "train_preparation",
            "state": "finished",
            "message": "Datos de train preparados.",
            "total_samples": len(self.x),
            "train_samples": len(self.x_train),
            "test_samples": len(self.x_test),
            "cant_characteristics": self.x_train.shape[1],
            "cant_classes": len(self.label_encoder.classes_),
            "classes": self.label_encoder.classes_.tolist(),
            "distribution_classes": {
                room: int(cant)
                for room, cant in distribution.items()
            }
        }

    def training(self):
        """Train the network with the prepared dataframe"""
        if self.x_train is None or self.y_train is None:
            return {
                "success": False,
                "stage": "train",
                "state": "error",
                "message": (
                    "Primero deben prepararse los datos de train."
                )
            }

        self.model = MLPClassifier(
            hidden_layer_sizes=(32, 16),
            activation="relu",
            solver="adam",
            max_iter=1000,
            random_state=42
        )

        self.model.fit(self.x_train, self.y_train)

        return {
            "success": True,
            "stage": "train",
            "state": "finished",
            "message": "Modelo entrenado correctmente.",
            "iterations": int(self.model.n_iter_),
            "loss": float(self.model.loss_),
            "converged": bool(
                self.model.n_iter_ < self.model.max_iter
            )
        }

    def assessment(self):
        """Evaluate the precission of the nn trained"""
        if self.model is None:
            return {
                "success": False,
                "stage": "assessment",
                "state": "error",
                "message": "Primero debe entrenarse el modelo."
            }

        self.predictions = self.model.predict(self.x_test)

        accuracy = accuracy_score(
            self.y_test,
            self.predictions
        )

        report = classification_report(
            self.y_test,
            self.predictions,
            labels=list(range(len(self.label_encoder.classes_))),
            target_names=self.label_encoder.classes_,
            output_dict=True,
            zero_division=0
        )

        detailed_predictions = []

        real_rooms = self.label_encoder.inverse_transform(
            self.y_test
        )

        predicted_rooms = self.label_encoder.inverse_transform(
            self.predictions
        )

        for real, predicted in zip(
            real_rooms,
            predicted_rooms
        ):
            detailed_predictions.append({
                "real": str(real),
                "predicted": str(predicted),
                "correct": bool(real == predicted)
            })

        return {
            "success": True,
            "stage": "assessment",
            "state": "finished",
            "message": "Evaluación finalizada.",
            "accuracy": float(accuracy),
            "classification_report": report,
            "predictions": detailed_predictions
        }