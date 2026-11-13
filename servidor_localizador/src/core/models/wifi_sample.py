from src.core.database import db
from datetime import datetime
import pandas as pd

class WiFiSample(db.Model):
    __tablename__ = 'wifi_sample'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nodo_id = db.Column(db.Integer, nullable=False)
    room = db.Column(db.String(50), nullable=False)
    bssid = db.Column(db.String(50), nullable=False)
    ssid = db.Column(db.String(32), nullable=False)
    rssi_raw = db.Column(db.Integer, nullable=False)
    rssi_kalman_filtered = db.Column(db.Integer, nullable=True)
    rssi_median_filtered = db.Column(db.Integer, nullable=True) 
    rssi_mean_filtered = db.Column(db.Integer, nullable=True)  
    record_date = db.Column(db.DateTime, default=datetime.now)
    #filter_method = db.Column(db.String(32), nullable=False)

    def __repr__(self):
        return f"<Muestra {self.room} - {self.ssid} | {self.bssid}: {self.rssi_raw}dBm>"
    
    @classmethod
    def create_sample (cls, **kwargs):
        new_sample = cls(**kwargs)
        
        db.session.add(new_sample)
        
        # No hago commit debido a que este metodo es usado por la API cuando crea muestras, y hacer varios commits
        # seguidos no es conveniente. Por lo tanto, en la API.
        
        return new_sample
    
    @classmethod
    def get_samples_order_by_time(cls):
        return cls.query.order_by(cls.record_date).all()
    
    def update_filtered_rssi(self, rssi_filtered: dict):
        
        for filter_method in rssi_filtered.keys(): 
            match filter_method:
                case "Kalman":
                    self.rssi_kalman_filtered = rssi_filtered[filter_method]
                case "Median":
                    self.rssi_median_filtered = rssi_filtered[filter_method]
                case "Mean":
                    self.rssi_mean_filtered = rssi_filtered[filter_method]
    
    @classmethod
    def get_last_scan(cls, filter_method):
        samples = cls.get_samples_order_by_time(
            filter_method
        )

        if not samples:
            raise ValueError("No hay muestras disponibles.")

        df = pd.DataFrame([
            {
                "record_date": sample.record_date,
                "bssid": sample.bssid,
                "rssi_filtered": sample.rssi_filtered
            }
            for sample in samples
        ])

        # Utilizamos el mismo criterio temporal que durante el entrenamiento.
        df["scan_date"] = pd.to_datetime(
            df["record_date"]
        ).dt.floor("s")

        # Identificamos el escaneo más reciente.
        last_scan_date = df["scan_date"].max()

        last_scan = df[
            df["scan_date"] == last_scan_date
        ]

        # Si hay varias mediciones para un mismo BSSID,
        # utilizamos su RSSI promedio.
        return (
            last_scan.groupby("bssid")["rssi_filtered"]
            .mean()
        )