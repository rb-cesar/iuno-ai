import requests
from typing import List, Dict
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
            "stream": False,  # <- ESSA LINHA É A CHAVE
        }
        response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=600)
        response.raise_for_status()
        data = response.json()
        # API de chat do Ollama normalmente retorna:
        # {"message": {"role": "...", "content": "..."}, ...}
        return data["message"]["content"]
