from abc import ABC, abstractmethod
from typing import List, Dict


class LLMClient(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        messages: lista de mensagens no formato:
            [
            {"role": "system"|"user"|"assistant", "content": "..."}
            ]
        Retorna apenas o texto de resposta do modelo.
        """
        raise NotImplementedError
