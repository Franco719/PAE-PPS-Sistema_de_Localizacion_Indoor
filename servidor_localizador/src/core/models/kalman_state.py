from src.core.database import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func


class KalmanState(db.Model):
    __tablename__ = 'kalman_state'

    #id = db.Column(db.Integer, primary_key=True)
    nodo_id = db.Column(db.Integer, nullable=False, primary_key=True)
    bssid = db.Column(db.String(50), nullable=False, primary_key=True)
    room = db.Column(db.String(50), nullable=False, primary_key=True)

    x = db.Column(db.Float, nullable=False)
    p = db.Column(db.Float, nullable=False)

    q = db.Column(db.Float, nullable=False)
    r = db.Column(db.Float, nullable=False)

    update_date = db.Column(
        db.DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )
    
    
    @classmethod
    def save_state(cls, nodo_id, bssid, room,  x, p, q, r):
        # Valores por defecto y prueba (eventualmente se pueden modificar a modo de prueba para la validacion del filtro): 
            # "x" es la estimacion actual del RSSI, como no hay ninguna cuando se crea, es None
            # "p" es la incertidumbre inicial de la estimacion, y se considera baja
            # "q" es la razon de cambio del RSSI, o ruido provocado en el proceso de filtrado, y se considera bajo 
            # "r" es el ruido de la medicion, y se considera que tiene un ruido considerable

        sentence = insert(cls).values(
            nodo_id=nodo_id,
            bssid=bssid,
            room=room,
            x=x,
            p=p,
            q=q,
            r=r
        )

        sentence = sentence.on_conflict_do_update(
            index_elements=["nodo_id", "bssid", "room"],
            set_={
                "x": sentence.excluded.x,
                "p": sentence.excluded.p,
                "q": sentence.excluded.q,
                "r": sentence.excluded.r,
                "update_date": func.now()
            }
        )

        try:
            db.session.execute(sentence)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print(f"Se hizo rollback: {e}")
            #raise
    
    @classmethod
    def get_state(cls, bssid: str, nodo_id: int, room: str):
        return cls.query.filter_by(
            nodo_id=nodo_id,
            bssid=bssid,
            room=room
        ).first()