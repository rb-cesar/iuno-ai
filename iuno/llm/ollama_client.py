import json
import requests
from typing import List, Dict, Iterable
from iuno.llm.base import LLMClient


class OllamaClient(LLMClient):
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Envia um chat para o Ollama em http://localhost:11434/api/chat.
        Certifique-se de que o Ollama esteja rodando.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=600)
        response.raise_for_status()
        data = response.json()
        # API de chat do Ollama normalmente retorna:
        # {"message": {"role": "...", "content": "..."}, ...}
        return data["message"]["content"]

    def chat_stream(self, messages: List[Dict[str, str]]) -> Iterable[str]:
        """Faz streaming de resposta usando NDJSON retornado pelo Ollama.

        Cada linha costuma ser um JSON com campos como:
          {"message": {"content": "..."}, "done": false}
        e ao final:
          {"done": true, ...}
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }

        with requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
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
                    # Em casos raros pode vir uma linha parcial; ignoramos para manter robustez.
                    # Se preferir comportamento estrito, troque por: raise
                    continue

                if data.get("done") is True:
                    break

                message = data.get("message") or {}
                chunk = message.get("content")
                if chunk:
                    yield chunk

