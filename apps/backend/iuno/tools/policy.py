from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class ToolPolicy:
    allowlist: List[str]
    require_approval: bool = True
    auto_approve: bool = False
    interactive: bool = False

    def is_allowed(self, tool_name: str) -> bool:
        return not self.allowlist or tool_name in self.allowlist


def parse_allowlist(raw: str | None) -> List[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def normalize_allowlist(allowlist: Iterable[str]) -> List[str]:
    return sorted({item.strip() for item in allowlist if item.strip()})
