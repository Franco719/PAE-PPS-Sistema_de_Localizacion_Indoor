from collections import deque
from src.core.filters.filter_strategy import RSSIFilter


class MeanFilter(RSSIFilter):

    def __init__(self, nodo_id: int, window_size=5):
        self.nodo = nodo_id
        self.window_size = window_size
        self.bssid = {}
        self.finished = False


    def update(self, networks):
        for network in networks:
            self.filter(
                network.bssid,
                network.rssi
            )


    def filter(self, bssid, rssi , state = None):
        
        self.finished = False

        if bssid not in self.bssid:
            self.bssid[bssid] = deque(
                maxlen=self.window_size
            )

        self.bssid[bssid].append(rssi)

        return sum(self.bssid[bssid]) / len(self.bssid[bssid])


    def get_value(self, bssid):

        values = self.bssid.get(bssid)

        if not values:
            return None

        return sum(values) / len(values)


    def get_method_name(self):
        return "Mean"
    
    
    def finish(self):
        if self.finished:
            return
        
        self.finished = True