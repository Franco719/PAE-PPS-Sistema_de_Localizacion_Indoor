from src.core.filters.filter_strategy import RSSIFilter
from src.core.models.kalman_state import KalmanState


class KalmanFilter(RSSIFilter):

    def __init__(self, nodo_id: int, room: str):
        self.nodo = nodo_id
        self.room = room
        self.filters = {}
        self.finished = False


    def filter(self, bssid, rssi):
        self.finished = False

        if bssid not in self.filters:
            state = KalmanState.get_state(bssid, self.nodo, self.room)
            
            print(f"Nodo: {self.nodo}")
            print(f"BSSID: {bssid}")
            print(f"Sala: {self.room}")
            print(f"Estado recuperado: {state}")
            
            self.filters[bssid] = Kalman1D(state)

        return self.filters[bssid].update(rssi)


    def get_value(self, bssid):

        filter = self.filters.get(bssid)

        if filter is None:
            return None

        return filter.estado.x


    def update(self, networks):

        for network in networks:
            self.filter(network.bssid, network.rssi)


    def get_method_name(self):
        return "Kalman"
    
    
    def finish(self):
        if self.finished:
            return

        for bssid, filter in self.filters.items():
            filter.save(self.nodo, bssid, self.room)

        self.finished = True


class Kalman1D:

    def __init__(self, state=None):
        if state is None:
            self.x = None
            self.p = 1.0
            self.q = 0.01
            self.r = 1.0
        else:
            self.x = state.x
            self.p = state.p
            self.q = state.q
            self.r = state.r


    def update(self, measurement):

        if self.x is None:
            self.x = measurement
            return self.x

        # Prediction
        self.p += self.q

        # Kalman gain
        k = self.p / (
            self.p + self.r
        )

        # Correction
        self.x += k * (
            measurement - self.x
        )

        # New uncertainty
        self.p = (
            1 - k
        ) * self.p

        return self.x
    
    
    def save(self, nodo_id: int, bssid: str, room: str):
        KalmanState.save_state(
            nodo_id=nodo_id,
            bssid=bssid,
            room=room,
            x=self.x,
            p=self.p,
            q=self.q,
            r=self.r
        )