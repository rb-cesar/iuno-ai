import json
from typing import Iterable

import requests

from iuno.llm.base import LLMClient, MessageList


class OllamaClient(LLMClient):
    def __init__(self, model: str, base_url: str = "http://localhost:11434") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def _build_payload(self, messages: MessageList, stream: bool) -> dict:
        return {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }

    def chat(self, messages: MessageList) -> str:
        """Envia um chat para o Ollama e retorna o conteudo da resposta."""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json=self._build_payload(messages, stream=False),
            timeout=600,
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

    def chat_stream(self, messages: MessageList) -> Iterable[str]:
        """Faz streaming de resposta usando NDJSON retornado pelo Ollama."""
        with requests.post(
            f"{self.base_url}/api/chat",
            json=self._build_payload(messages, stream=True),
            timeout=600,
            stream=True,
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if data.get("done") is True:
                    break

                message = data.get("message") or {}
                chunk = message.get("content")
                if chunk:
                    yield chunk
