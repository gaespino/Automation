from abc import ABC, abstractmethod


class IRecipe(ABC):
    @abstractmethod
    def set_fuses(self) -> int:
        pass

