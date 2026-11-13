from abc import ABC, abstractmethod

class RSSIFilter(ABC):
    
    @abstractmethod
    def filter(self, bssid: str, rssi: str, state = None):
        pass
    
    
    @abstractmethod
    def get_value(self, bssid: str):
        pass
    
    
    @abstractmethod
    def update(self, networks):
        pass
    
    
    @abstractmethod
    def get_method_name(self) -> str:
        pass
    
    
    @abstractmethod
    def finish(self):
        pass