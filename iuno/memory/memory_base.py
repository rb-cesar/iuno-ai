from abc import ABC, abstractmethod
from typing import Any, Dict


class MemoryStore(ABC):
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """Carrega o objeto de memória persistida."""
        raise NotImplementedError

    @abstractmethod
    def save(self, data: Dict[str, Any]) -> None:
        """Salva o objeto de memória persistida."""
        raise NotImplementedError
