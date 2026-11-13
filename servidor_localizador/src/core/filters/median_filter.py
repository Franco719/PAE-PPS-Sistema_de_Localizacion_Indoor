from collections import deque
from statistics import median
from src.core.filters.filter_strategy import RSSIFilter


class MedianFilter(RSSIFilter):


    def __init__(self, nodo_id: int, window_size=5):
        self.nodo_id = nodo_id
        self.window_size = window_size
        self.bssid = {}
        self.finished = False


    def filter(self, bssid, rssi, state = None):
        self.finished = False
        
        if bssid not in self.bssid:
            self.bssid[bssid] = deque(maxlen=self.window_size)

        self.bssid[bssid].append(rssi)

        return median(self.bssid[bssid])
    

    def update(self, networks):

        for network in networks:

            if network.bssid not in self.bssid:
                self.bssid[network.bssid] = deque(
                    maxlen=self.window_size
                )

            self.bssid[network.bssid].append(network.rssi)


    def get_value(self, bssid: str):
        values = self.bssid.get(bssid)

        if not values:
            return None

        return median(values)


    def get_method_name(self):
        return "Median"
    
    
    def finish(self):
        if self.finished:
            return
        
        self.finished = True