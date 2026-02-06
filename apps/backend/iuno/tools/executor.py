from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from iuno.tools.base import ToolCall, ToolError, ToolResult
from iuno.tools.policy import ToolPolicy
from iuno.tools.registry import ToolRegistry


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_log(path: Optional[str], payload: Dict[str, Any]) -> None:
    if not path:
        return
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def execute_tool(
    call: ToolCall,
    registry: ToolRegistry,
    policy: ToolPolicy,
    log_path: Optional[str] = None,
) -> ToolResult:
    if not policy.is_allowed(call.name):
        result = ToolResult(ok=False, error="Ferramenta nao permitida pelo allowlist.")
        _write_log(
            log_path,
            {
                "timestamp": _timestamp(),
                "tool": call.name,
                "args": call.args,
                "ok": False,
                "error": result.error,
            },
        )
        return result

    if policy.require_approval and not policy.auto_approve:
        if policy.interactive:
            approval = input(f"[TOOL] Aprovar execucao de '{call.name}'? (s/N) ").strip().lower()
            if approval not in {"s", "sim", "y", "yes"}:
                result = ToolResult(ok=False, error="Execucao negada pelo usuario.")
                _write_log(
                    log_path,
                    {
                        "timestamp": _timestamp(),
                        "tool": call.name,
                        "args": call.args,
                        "ok": False,
                        "error": result.error,
                    },
                )
                return result
        else:
            result = ToolResult(ok=False, error="Execucao requer aprovacao.")
            _write_log(
                log_path,
                {
                    "timestamp": _timestamp(),
                    "tool": call.name,
                    "args": call.args,
                    "ok": False,
                    "error": result.error,
                },
            )
            return result

    tool = registry.get(call.name)
    if not tool:
        result = ToolResult(ok=False, error="Ferramenta nao encontrada.")
        _write_log(
            log_path,
            {
                "timestamp": _timestamp(),
                "tool": call.name,
                "args": call.args,
                "ok": False,
                "error": result.error,
            },
        )
        return result

    try:
        result = tool.handler(call.args)
    except ToolError as exc:
        result = ToolResult(ok=False, error=str(exc))
    except Exception as exc:
        result = ToolResult(ok=False, error=f"Falha inesperada: {exc}")

    _write_log(
        log_path,
        {
            "timestamp": _timestamp(),
            "tool": call.name,
            "args": call.args,
            "ok": result.ok,
            "output": result.output,
            "error": result.error,
            "metadata": result.metadata,
        },
    )
    return result


def tool_result_to_message(tool_name: str, result: ToolResult) -> str:
    payload = {
        "tool": tool_name,
        "ok": result.ok,
        "output": result.output,
        "error": result.error,
        "metadata": result.metadata,
    }
    return json.dumps(payload, ensure_ascii=False)


def tool_call_to_json(call: ToolCall) -> str:
    return json.dumps(asdict(call), ensure_ascii=False)
