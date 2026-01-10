import json
from pathlib import Path
from typing import Any, Dict

from iuno.memory.memory_base import MemoryStore


class JsonMemory(MemoryStore):
    def __init__(self, file_path: str = "memory.json") -> None:
        self.file_path = Path(file_path)

    def load(self) -> Dict[str, Any]:
        if not self.file_path.exists():
            return {}
        try:
            with self.file_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except (json.JSONDecodeError, OSError):
            return {}

    def save(self, data: Dict[str, Any]) -> None:
        with self.file_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=4)
