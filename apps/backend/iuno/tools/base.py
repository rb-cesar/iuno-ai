from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


class ToolError(RuntimeError):
    """Erro generico da camada de ferramentas."""


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    output: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    args_schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], ToolResult]
