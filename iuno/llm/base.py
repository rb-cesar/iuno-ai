from abc import ABC, abstractmethod
from typing import List, Dict, Iterable


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

    def chat_stream(self, messages: List[Dict[str, str]]) -> Iterable[str]:
        """Versão em streaming do chat.

        Deve gerar (yield) pedaços incrementais de texto conforme o modelo responde.

        Implementação padrão: faz fallback para `chat()` e retorna um único chunk.
        """
        yield self.chat(messages)
