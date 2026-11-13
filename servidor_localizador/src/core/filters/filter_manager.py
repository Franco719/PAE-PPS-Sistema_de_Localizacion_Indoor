from src.core.filters.filter_factory import create_filter
from threading import Lock
import threading

class FilterManager:

    def __init__(self):
        self.filters = []
        self.lock = Lock()

    def start(self, nodo_id: int, room: str = None , window=None):
        with self.lock:
            self.filters.append(create_filter("Kalman", nodo_id, room, window))
            self.filters.append(create_filter("Median", nodo_id, room, window))
            self.filters.append(create_filter("Mean", nodo_id, room, window))

    def filter(self, bssid: str, rssi_raw: int):
        with self.lock:
            results = {}
            for filter in self.filters:
                rssi_filtered = filter.filter(bssid, rssi_raw)
                filter_method = filter.get_method_name()
                results[filter_method] = rssi_filtered
                
            return results

    def finish(self):
        with self.lock:
            for filter in self.filters:
                if filter is None:
                    return

                filter.finish()

            self.filters = []
            


sample_filters = FilterManager()
#prediction_filter = FilterManager()