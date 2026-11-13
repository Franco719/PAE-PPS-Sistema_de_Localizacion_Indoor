from src.core.filters.filter_strategy import RSSIFilter
from src.core.filters.kalman_filter import KalmanFilter
from src.core.filters.median_filter import MedianFilter
from src.core.filters.mean_filter import MeanFilter


def create_filter(method, nodo_id: int, room: str, window=None):

    match method:
        
        case "Kalman":
            return KalmanFilter(nodo_id, room)

        case "Median":
            return MedianFilter(nodo_id, window)

        case "Mean":
            return MeanFilter(nodo_id, window)

        case _ :
            return WithoutFilter()

    raise ValueError(f"Método desconocido: {method}")


class WithoutFilter(RSSIFilter):

    def filter(self, bssid: str, rssi: int):
        return rssi


    def get_value(self, bssid: str):
        return None


    def update(self, redes):
        return None


    def get_method_name(self) -> str:
        return "Ninguno"
    
    
    def finish(self):
        pass