from abc import ABC, abstractmethod


class IDynamicInjection(ABC):
    @abstractmethod
    def perform_fuse_override(self, socket: int=None, die: str=None, fuse_override_iteration: int=None) -> int:
        pass
