from __future__ import annotations

from typing import Optional

from iuno.voice.base import TextToSpeech, VoiceError


class Pyttsx3TTS(TextToSpeech):
    """TTS offline via pyttsx3 (no Windows, normalmente usa SAPI5)."""

    def __init__(
        self,
        rate: Optional[int] = None,
        volume: Optional[float] = None,
        voice: Optional[str] = None,
    ):
        try:
            import pyttsx3
        except Exception as e:  # pragma: no cover
            raise VoiceError(
                "pyttsx3 não está instalado. Instale com: pip install pyttsx3"
            ) from e

        self._engine = pyttsx3.init()

        if rate is not None:
            self._engine.setProperty("rate", rate)
        if volume is not None:
            # faixa típica: 0.0 .. 1.0
            self._engine.setProperty("volume", float(volume))
        if voice:
            # 'voice' pode ser id completo ou um substring do nome.
            selected = None
            try:
                for v in self._engine.getProperty("voices"):
                    if v.id == voice or (getattr(v, "name", "") and voice.lower() in v.name.lower()):
                        selected = v.id
                        break
            except Exception:
                selected = None

            if selected:
                self._engine.setProperty("voice", selected)

    def speak(self, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return

        self._engine.say(text)
        self._engine.runAndWait()

