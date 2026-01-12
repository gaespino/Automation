from abc import ABC, abstractmethod

class ILog(ABC):
    @abstractmethod
    def log(self, msg: str): pass
