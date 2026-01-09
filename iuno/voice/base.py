from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


class VoiceError(RuntimeError):
    """Erro genérico da camada de voz."""


class SpeechToText(ABC):
    @abstractmethod
    def transcribe_file(self, path: str, language: str = "pt-BR") -> str:
        """Transcreve um arquivo de áudio (idealmente WAV) e retorna o texto."""
        raise NotImplementedError


class TextToSpeech(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:
        """Fala o texto em voz alta."""
        raise NotImplementedError


@dataclass(frozen=True)
class VoiceConfig:
    enable_voice_in: bool = False
    enable_voice_out: bool = False

    # input
    stt_language: str = "pt-BR"

    # output
    tts_rate: Optional[int] = None
    tts_volume: Optional[float] = None
    tts_voice: Optional[str] = None

