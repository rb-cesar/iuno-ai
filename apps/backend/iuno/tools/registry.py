from __future__ import annotations

from typing import Dict, Iterable, List

from iuno.tools.base import ToolSpec


class ToolRegistry:
    def __init__(self, tools: Iterable[ToolSpec]) -> None:
        self._tools: Dict[str, ToolSpec] = {tool.name: tool for tool in tools}

    def list_specs(self) -> List[dict]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "args_schema": tool.args_schema,
            }
            for tool in self._tools.values()
        ]

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def names(self) -> List[str]:
        return sorted(self._tools.keys())
