from abc import ABC, abstractmethod
from typing import Any, Dict

MemoryData = Dict[str, Any]


class MemoryStore(ABC):
    @abstractmethod
    def load(self) -> MemoryData:
        """Carrega o objeto de memoria persistida."""
        raise NotImplementedError

    @abstractmethod
    def save(self, data: MemoryData) -> None:
        """Salva o objeto de memoria persistida."""
        raise NotImplementedError
