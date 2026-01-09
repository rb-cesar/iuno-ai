from iuno.core.orchestrator import Orchestrator
from iuno.llm.ollama_client import OllamaClient
from iuno.memory.json_memory import JsonMemory


def main() -> None:
    # Aqui você pode trocar o modelo por outro instalado no Ollama
    llm_client = OllamaClient(model="gpt-oss:20b")
    json_store = JsonMemory()

    orchestrator = Orchestrator(llm_client, json_store)
    orchestrator.run_cli()


if __name__ == "__main__":
    main()
