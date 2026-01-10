from abc import ABC, abstractmethod
from typing import Dict, Iterable, List

Message = Dict[str, str]
MessageList = List[Message]


class LLMClient(ABC):
    @abstractmethod
    def chat(self, messages: MessageList) -> str:
        """Envia mensagens e retorna o texto da resposta."""
        raise NotImplementedError

    def chat_stream(self, messages: MessageList) -> Iterable[str]:
        """Versao em streaming do chat (fallback para chat())."""
        yield self.chat(messages)
