import os

from iuno.core.orchestrator import Orchestrator
from iuno.llm.ollama_client import OllamaClient
from iuno.memory.json_memory import JsonMemory


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> None:
    # Aqui você pode trocar o modelo por outro instalado no Ollama
    llm_client = OllamaClient(model="gpt-oss:20b")
    json_store = JsonMemory()

    stream = _env_flag("IUNO_STREAM", True)

    orchestrator = Orchestrator(llm_client, json_store, stream=stream)
    orchestrator.run_cli()


if __name__ == "__main__":
    main()
