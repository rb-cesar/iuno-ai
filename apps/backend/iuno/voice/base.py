from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Optional

VoiceMode = Literal["file", "mic"]
TTSProvider = Literal["pyttsx3", "edge"]


class VoiceError(RuntimeError):
    """Erro generico da camada de voz."""


class SpeechToText(ABC):
    @abstractmethod
    def transcribe_file(self, path: str, language: str = "pt-BR") -> str:
        """Transcreve um arquivo de audio (idealmente WAV) e retorna o texto."""
        raise NotImplementedError


class TextToSpeech(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:
        """Fala o texto em voz alta."""
        raise NotImplementedError


class AudioRecorder(ABC):
    @abstractmethod
    def record_wav(self) -> str:
        """Grava audio e retorna o caminho de um arquivo WAV gerado."""
        raise NotImplementedError


@dataclass(frozen=True)
class VoiceConfig:
    enable_voice_in: bool = False
    enable_voice_out: bool = False

    # input
    stt_language: str = "pt-BR"
    voice_in_mode: VoiceMode = "file"

    # mic recording (apenas quando voice_in_mode == "mic")
    mic_sample_rate: int = 16000
    mic_channels: int = 1

    # onde salvar audios gravados (mic); se None, usa temp do sistema
    audio_dir: Optional[str] = None

    # se True, tenta apagar os WAV gravados assim que nao forem mais necessarios
    cleanup_audio_files: bool = True

    # output
    tts_rate: Optional[int] = None
    tts_volume: Optional[float] = None
    tts_voice: Optional[str] = None
    tts_provider: TTSProvider = "pyttsx3"
