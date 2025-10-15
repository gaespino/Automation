from abc import ABC, abstractmethod


class IBoot(ABC):
    @abstractmethod
    def go(self, **args) -> int:
        pass

