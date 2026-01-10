import os
from pathlib import Path
from typing import Iterable, Optional

# Carrega variaveis do arquivo .env (se existir).
try:  # pragma: no cover
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # Se python-dotenv nao estiver instalado, seguimos apenas com o ambiente do sistema.
    pass

from iuno.core.orchestrator import Orchestrator
from iuno.llm.ollama_client import OllamaClient
from iuno.memory.json_memory import JsonMemory
from iuno.voice.base import AudioRecorder, SpeechToText, TextToSpeech, VoiceConfig

_TRUE_VALUES = {"1", "true", "yes", "y", "on"}
_VOICE_IN_MODES = {"file", "mic"}
_TTS_PROVIDERS = {"pyttsx3", "edge"}


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUE_VALUES 


def _env_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip()
    return value if value else default


def _env_optional_str(name: str) -> Optional[str]:
    raw = os.getenv(name)
    if raw is None:
        return None
    value = raw.strip()
    return value if value else None


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _env_optional_int(name: str) -> Optional[int]:
    raw = os.getenv(name)
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _env_optional_float(name: str) -> Optional[float]:
    raw = os.getenv(name)
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _env_choice(name: str, default: str, choices: Iterable[str]) -> str:
    value = _env_str(name, default).lower()
    return value if value in choices else default


def _project_root() -> Path:
    return Path(__file__).resolve().parent


def _resolve_audio_dir() -> str:
    default_audio_dir = _project_root() / "data" / "audio"
    return _env_str("IUNO_AUDIO_DIR", str(default_audio_dir))


def _build_voice_config() -> VoiceConfig:
    voice_in_mode = _env_choice("IUNO_VOICE_IN_MODE", "file", _VOICE_IN_MODES)
    tts_provider = _env_choice("IUNO_TTS_PROVIDER", "pyttsx3", _TTS_PROVIDERS)

    return VoiceConfig(
        enable_voice_in=_env_flag("IUNO_VOICE_IN", False),
        enable_voice_out=_env_flag("IUNO_VOICE_OUT", False),
        stt_language=_env_str("IUNO_STT_LANG", "pt-BR"),
        voice_in_mode=voice_in_mode,
        mic_sample_rate=_env_int("IUNO_MIC_SAMPLE_RATE", 16000),
        mic_channels=_env_int("IUNO_MIC_CHANNELS", 1),
        audio_dir=_resolve_audio_dir(),
        cleanup_audio_files=_env_flag("IUNO_CLEANUP_AUDIO_FILES", True),
        tts_rate=_env_optional_int("IUNO_TTS_RATE"),
        tts_volume=_env_optional_float("IUNO_TTS_VOLUME"),
        tts_voice=_env_optional_str("IUNO_TTS_VOICE"),
        tts_provider=tts_provider,
    )


def _build_stt(voice_cfg: VoiceConfig) -> Optional[SpeechToText]:
    if not voice_cfg.enable_voice_in:
        return None

    from iuno.voice.stt_speech_recognition import SpeechRecognitionSTT

    return SpeechRecognitionSTT()


def _build_recorder(voice_cfg: VoiceConfig) -> Optional[AudioRecorder]:
    if not voice_cfg.enable_voice_in or voice_cfg.voice_in_mode != "mic":
        return None

    try:
        from iuno.voice.mic_sounddevice import SoundDeviceRecorder
    except Exception:
        return None

    try:
        return SoundDeviceRecorder(
            sample_rate=voice_cfg.mic_sample_rate,
            channels=voice_cfg.mic_channels,
            output_dir=voice_cfg.audio_dir,
        )
    except Exception:
        return None


def _build_tts(voice_cfg: VoiceConfig) -> Optional[TextToSpeech]:
    if not voice_cfg.enable_voice_out:
        return None

    if voice_cfg.tts_provider == "edge":
        from iuno.voice.tts_edge import EdgeTTS

        return EdgeTTS(
            rate=voice_cfg.tts_rate,
            volume=voice_cfg.tts_volume,
            voice=voice_cfg.tts_voice,
        )

    # Thread dedicada para evitar travamentos do pyttsx3 apos a primeira fala.
    try:
        from iuno.voice.tts_threaded import ThreadedPyttsx3TTS

        return ThreadedPyttsx3TTS(
            rate=voice_cfg.tts_rate,
            volume=voice_cfg.tts_volume,
            voice=voice_cfg.tts_voice,
        )
    except Exception:
        from iuno.voice.tts_pyttsx3 import Pyttsx3TTS

        return Pyttsx3TTS(
            rate=voice_cfg.tts_rate,
            volume=voice_cfg.tts_volume,
            voice=voice_cfg.tts_voice,
        )


def main() -> None:
    # Troque o modelo por outro instalado no Ollama.
    llm_client = OllamaClient(model="gpt-oss:20b")
    json_store = JsonMemory()

    voice_cfg = _build_voice_config()

    orchestrator = Orchestrator(
        llm_client,
        json_store,
        stream=_env_flag("IUNO_STREAM", True),
        voice=voice_cfg,
        stt=_build_stt(voice_cfg),
        tts=_build_tts(voice_cfg),
        recorder=_build_recorder(voice_cfg),
    )
    orchestrator.run_cli()


if __name__ == "__main__":
    main()
