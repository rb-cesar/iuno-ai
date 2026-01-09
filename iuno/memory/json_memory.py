import json
# from abc import ABC
from pathlib import Path
from typing import Any, Dict
from iuno.memory.memory_base import MemoryStore


class JsonMemory(MemoryStore):
    def __init__(self, file_path: str = 'memory.json'):
        self.file_path = Path(file_path)

    def load(self) -> Dict[str, Any]:
        if not self.file_path.exists():
            return {}
        try:
            with self.file_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.decoder.JSONDecodeError:
            return {}

    def save(self, data: Dict[str, Any]) -> None:
        with self.file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
