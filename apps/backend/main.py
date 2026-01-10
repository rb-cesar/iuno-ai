"""CLI entrypoint for Iuno backend."""

from dotenv import load_dotenv

from iuno.core.orchestrator import Orchestrator
from iuno.llm.ollama_client import OllamaClient
from iuno.memory.json_memory import JsonMemory
from iuno.services.config import (
    build_recorder,
    build_stt,
    build_tts,
    build_voice_config,
    env_flag,
)

load_dotenv()


def main() -> None:
    # Troque o modelo por outro instalado no Ollama.
    llm_client = OllamaClient(model="gpt-oss:20b")
    json_store = JsonMemory()

    voice_cfg = build_voice_config()

    orchestrator = Orchestrator(
        llm_client,
        json_store,
        stream=env_flag("IUNO_STREAM", True),
        voice=voice_cfg,
        stt=build_stt(voice_cfg),
        tts=build_tts(voice_cfg),
        recorder=build_recorder(voice_cfg),
    )
    orchestrator.run_cli()


if __name__ == "__main__":
    main()
