from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

MemoryState = Dict[str, Any]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_default_state() -> MemoryState:
    """Estrutura base da memoria de longo prazo da Iuno."""
    return {
        "user_profile": {
            "name": None,
            "age": None,
            "location": None,
        },
        "preferences": {
            "formality": "casual",  # "casual" | "formal"
            "language": "pt-BR",
        },
        "projects": [],
        "long_term_facts": [],
    }


def ensure_default_state(state: Optional[MemoryState]) -> MemoryState:
    """Garante que o objeto de memoria tenha todos os campos necessarios."""
    if not state or not isinstance(state, dict):
        return create_default_state()

    defaults = create_default_state()

    for key, default_value in defaults.items():
        if key not in state:
            state[key] = default_value
            continue

        if isinstance(default_value, dict):
            for subkey, subdefault in default_value.items():
                state[key].setdefault(subkey, subdefault)

    state.setdefault("projects", [])
    state.setdefault("long_term_facts", [])

    return state


def add_long_term_fact(
    state: MemoryState,
    text: str,
    importance: int = 3,
) -> None:
    """Adiciona um fato na memoria de longo prazo."""
    importance = max(1, min(int(importance), 5))

    fact = {
        "text": text,
        "importance": importance,
        "created_at": _utc_now_iso(),
        "last_accessed": None,
    }

    state.setdefault("long_term_facts", [])
    state["long_term_facts"].append(fact)


def touch_long_term_facts(facts: Iterable[Dict[str, Any]]) -> None:
    """Atualiza o last_accessed dos fatos consultados."""
    now = _utc_now_iso()
    for fact in facts:
        fact["last_accessed"] = now
