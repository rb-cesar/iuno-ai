from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

from iuno.tools import ToolPolicy, ToolRegistry, default_tools
from iuno.tools.policy import normalize_allowlist, parse_allowlist
from iuno.voice.base import AudioRecorder, SpeechToText, TextToSpeech, VoiceConfig

_TRUE_VALUES = {"1", "true", "yes", "y", "on"}
_VOICE_IN_MODES = {"file", "mic"}
_TTS_PROVIDERS = {"pyttsx3", "edge"}


def env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUE_VALUES


def env_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip()
    return value if value else default


def env_optional_str(name: str) -> Optional[str]:
    raw = os.getenv(name)
    if raw is None:
        return None
    value = raw.strip()
    return value if value else None


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def env_optional_int(name: str) -> Optional[int]:
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


def env_optional_float(name: str) -> Optional[float]:
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


def env_choice(name: str, default: str, choices: Iterable[str]) -> str:
    value = env_str(name, default).lower()
    return value if value in choices else default


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_audio_dir() -> str:
    default_audio_dir = project_root() / "data" / "audio"
    return env_str("IUNO_AUDIO_DIR", str(default_audio_dir))


def resolve_action_log_path() -> str:
    return env_str("IUNO_ACTION_LOG", "action_log.jsonl")


def build_tool_registry() -> ToolRegistry:
    return ToolRegistry(default_tools())


def build_tool_policy(interactive: bool = False) -> ToolPolicy:
    allowlist = parse_allowlist(env_optional_str("IUNO_TOOLS_ALLOWLIST"))
    allowlist = normalize_allowlist(allowlist)
    return ToolPolicy(
        allowlist=allowlist,
        require_approval=env_flag("IUNO_TOOLS_REQUIRE_APPROVAL", True),
        auto_approve=env_flag("IUNO_TOOLS_AUTO_APPROVE", False),
        interactive=interactive,
    )


def build_voice_config() -> VoiceConfig:
    voice_in_mode = env_choice("IUNO_VOICE_IN_MODE", "file", _VOICE_IN_MODES)
    tts_provider = env_choice("IUNO_TTS_PROVIDER", "pyttsx3", _TTS_PROVIDERS)

    return VoiceConfig(
        enable_voice_in=env_flag("IUNO_VOICE_IN", False),
        enable_voice_out=env_flag("IUNO_VOICE_OUT", False),
        stt_language=env_str("IUNO_STT_LANG", "pt-BR"),
        voice_in_mode=voice_in_mode,
        mic_sample_rate=env_int("IUNO_MIC_SAMPLE_RATE", 16000),
        mic_channels=env_int("IUNO_MIC_CHANNELS", 1),
        audio_dir=resolve_audio_dir(),
        cleanup_audio_files=env_flag("IUNO_CLEANUP_AUDIO_FILES", True),
        tts_rate=env_optional_int("IUNO_TTS_RATE"),
        tts_volume=env_optional_float("IUNO_TTS_VOLUME"),
        tts_voice=env_optional_str("IUNO_TTS_VOICE"),
        tts_provider=tts_provider,
    )


def build_stt(voice_cfg: VoiceConfig) -> Optional[SpeechToText]:
    if not voice_cfg.enable_voice_in:
        return None

    from iuno.voice.stt_speech_recognition import SpeechRecognitionSTT

    return SpeechRecognitionSTT()


def build_recorder(voice_cfg: VoiceConfig) -> Optional[AudioRecorder]:
    if not voice_cfg.enable_voice_in or voice_cfg.voice_in_mode != "mic":
        return None

    import importlib.util

    if importlib.util.find_spec("sounddevice") is None:
        return None

    from iuno.voice.mic_sounddevice import SoundDeviceRecorder

    try:
        return SoundDeviceRecorder(
            sample_rate=voice_cfg.mic_sample_rate,
            channels=voice_cfg.mic_channels,
            output_dir=voice_cfg.audio_dir,
        )
    except Exception:
        return None


def build_tts(voice_cfg: VoiceConfig) -> Optional[TextToSpeech]:
    if not voice_cfg.enable_voice_out:
        return None

    if voice_cfg.tts_provider == "edge":
        from iuno.voice.tts_edge import EdgeTTS

        return EdgeTTS(
            rate=voice_cfg.tts_rate,
            volume=voice_cfg.tts_volume,
            voice=voice_cfg.tts_voice,
        )

    from iuno.voice.tts_threaded import ThreadedPyttsx3TTS

    return ThreadedPyttsx3TTS(
        rate=voice_cfg.tts_rate,
        volume=voice_cfg.tts_volume,
        voice=voice_cfg.tts_voice,
    )
