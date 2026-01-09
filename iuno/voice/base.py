from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Literal


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


class AudioRecorder(ABC):
    @abstractmethod
    def record_wav(self) -> str:
        """Grava áudio e retorna o caminho de um arquivo WAV gerado."""
        raise NotImplementedError


@dataclass(frozen=True)
class VoiceConfig:
    enable_voice_in: bool = False
    enable_voice_out: bool = False

    # input
    stt_language: str = "pt-BR"
    voice_in_mode: Literal["file", "mic"] = "file"

    # mic recording (apenas quando voice_in_mode == "mic")
    mic_sample_rate: int = 16000
    mic_channels: int = 1

    # onde salvar áudios gravados (mic); se None, usa temp do sistema
    audio_dir: Optional[str] = None

    # se True, tenta apagar os WAV gravados assim que não forem mais necessários
    cleanup_audio_files: bool = True

    # output
    tts_rate: Optional[int] = None
    tts_volume: Optional[float] = None
    tts_voice: Optional[str] = None

