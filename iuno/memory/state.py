from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, List, Iterable

MemoryState = Dict[str, Any]


def create_default_state() -> MemoryState:
    """
    Estrutura base da memória de longo prazo da Iuno.
    """
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
        "projects": [],  # lista de strings
        "long_term_facts": [],  # lista de fatos (dict)
    }


def ensure_default_state(state: Optional[MemoryState]) -> MemoryState:
    """
    Garante que o objeto de memória tenha todos os campos necessários.
    Se o arquivo estiver vazio ou for inválido, cria uma memória nova.
    """
    if not state or not isinstance(state, dict):
        return create_default_state()

    default = create_default_state()

    # merge raso com defaults
    for key, default_value in default.items():
        if key not in state:
            state[key] = default_value
        else:
            if isinstance(default_value, dict):
                # merge de dicionários internos
                for subkey, subdefault in default_value.items():
                    state[key].setdefault(subkey, subdefault)

    # garante listas
    state.setdefault("projects", [])
    state.setdefault("long_term_facts", [])

    return state


def add_long_term_fact(
        state: MemoryState,
        text: str,
        importance: int = 3,
) -> None:
    """
    Adiciona um fato na memória de longo prazo.
    importance: 1 (baixa) a 5 (muito importante).
    """
    importance = max(1, min(int(importance), 5))

    fact = {
        "text": text,
        "importance": importance,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_accessed": None,
    }

    state.setdefault("long_term_facts", [])
    state["long_term_facts"].append(fact)


def touch_long_term_facts(facts: Iterable[Dict[str, Any]]) -> None:
    """Atualiza o last_accessed dos fatos consultados."""
    now = datetime.now(timezone.utc).isoformat()
    for fact in facts:
        fact["last_accessed"] = now
