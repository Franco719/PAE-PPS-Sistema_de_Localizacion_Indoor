from src.core.database import db
from datetime import datetime
from enum import Enum

    
class TrainingState(Enum):
    WAITING = "waiting"
    EXECUTING = "executing"
    FINISHED = "finished"
    FAILED = "failed"


class Training(db.Model):
    __tablename__ = 'training'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=True)
    state = db.Column(db.Enum(TrainingState), default=TrainingState.WAITING)
    filter_method = db.Column(db.String(32), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.now)
    finish_date = db.Column(db.DateTime, nullable=True)
    cant_samples_availables = db.Column(db.Integer, nullable=True) # Cantidad de muestras tomadas de la base
    cant_scans_generated = db.Column(db.Integer, nullable=True) # Cantidad de escaneos (en un escaneo, se toman varias muestras)
    cant_bssids = db.Column(db.Integer, nullable=True)
    cant_rooms = db.Column(db.Integer, nullable=True)
    accuracy = db.Column(db.Float, nullable=True)
    loss = db.Column(db.Float, nullable=True)
    iterations = db.Column(db.Integer, nullable=True)
    model_path = db.Column(db.Text, nullable=True)
    errors = db.Column(db.Text, nullable=True)
    model_hash = db.Column(db.String(64), nullable=True) # Como al cargar joblib.load() se ejecuta código, creo un hash para al menos verificar que no haya sido modificado antes de cargarlo
    deleted = db.Column(db.Boolean, nullable=True, default=False)
    active = db.Column(db.Boolean, nullable=True, default=False)
    
    
    @classmethod
    def create_training (cls, **kwargs):
        new_training = cls(**kwargs)
        
        db.session.add(new_training)
        db.session.commit()
        
        return new_training

    @classmethod
    def get_training_by_id(cls, id: int):
        return cls.query.filter_by(id=id).first()
    
    @classmethod
    def get_trainings(cls):
        return cls.query.filter_by(deleted=False).all()
    
    @classmethod
    def get_active_training(cls, filter_method: str):
        training = cls.query.filter_by(deleted=False, active=True, filter_method=filter_method).all()
        
        if len(training) != 1:
            raise ValueError(f"Se encontraron {len(training)} modelos activos para el metodo {filter_method}, verifique el panel de modelos entrenados")
        
        return training.pop()
    
    @classmethod
    def delete_training(cls, id: str) -> bool:
        training = cls.get_training_by_id(id)

        if training:
            training.deleted = True
            db.session.commit()
            return True
        else:
            return False
    
    def abort_training(self, errors: list[str]):
        self.state = TrainingState.FAILED
        if self.errors:
            self.errors += f"{"".join(errors)}"
        else:
            self.errors = f"{"".join(errors)}"
        
        db.session.commit() 
        
    def save_execution(self):
        self.state = TrainingState.EXECUTING
        
        db.session.commit()
        
    def update_training(self, **kwargs):
        for attribute, value in kwargs.items():
            match attribute:
                case "state":
                    self.state = value
                case "finish_date":
                    self.finish_date = value
                case "cant_samples_available":
                    self.cant_samples_availables = value
                case "cant_scans_generated":
                    self.cant_scans_generated = value
                case "cant_bssids":
                    self.cant_bssids = value
                case "cant_rooms":
                    self.cant_rooms = value
                case "accuracy":
                    self.accuracy = value
                case "loss":
                    self.loss = value
                case "iterations":
                    self.iterations = value
                case "model_path":
                    self.model_path = value
                case "errors":
                    self.errors = value
                case "model_hash":
                    self.model_hash = value
                    
        db.session.commit()