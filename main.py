import os

# Carrega variáveis do arquivo .env (se existir)
try:  # pragma: no cover
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # Se python-dotenv não estiver instalado, seguimos apenas com o ambiente do sistema.
    pass

from iuno.core.orchestrator import Orchestrator
from iuno.llm.ollama_client import OllamaClient
from iuno.memory.json_memory import JsonMemory
from iuno.voice.base import VoiceConfig


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

    voice_cfg = VoiceConfig(
        enable_voice_in=_env_flag("IUNO_VOICE_IN", False),
        enable_voice_out=_env_flag("IUNO_VOICE_OUT", False),
        stt_language=os.getenv("IUNO_STT_LANG", "pt-BR"),
        tts_rate=int(os.getenv("IUNO_TTS_RATE", "0")) or None,
        tts_volume=float(os.getenv("IUNO_TTS_VOLUME", "0")) or None,
        tts_voice=os.getenv("IUNO_TTS_VOICE") or None,
    )

    stt = None
    if voice_cfg.enable_voice_in:
        from iuno.voice.stt_speech_recognition import SpeechRecognitionSTT

        stt = SpeechRecognitionSTT()

    tts = None
    if voice_cfg.enable_voice_out:
        from iuno.voice.tts_pyttsx3 import Pyttsx3TTS

        tts = Pyttsx3TTS(rate=voice_cfg.tts_rate, volume=voice_cfg.tts_volume, voice=voice_cfg.tts_voice)

    orchestrator = Orchestrator(
        llm_client,
        json_store,
        stream=stream,
        voice=voice_cfg,
        stt=stt,
        tts=tts,
    )
    orchestrator.run_cli()


if __name__ == "__main__":
    main()
