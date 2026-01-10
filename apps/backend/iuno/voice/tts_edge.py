from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Optional

import edge_tts
from playsound import playsound

from iuno.voice.base import TextToSpeech, VoiceError


class EdgeTTS(TextToSpeech):
    """TTS usando edge-tts (Microsoft Edge/Neural).

    Gera audio via servico da Microsoft e toca localmente com playsound.
    """

    def __init__(
        self,
        rate: Optional[int] = None,
        volume: Optional[float] = None,
        voice: Optional[str] = None,
    ) -> None:
        self._rate = rate
        self._volume = volume
        self._voice = voice or "pt-BR-FranciscaNeural"

    def _format_rate(self) -> str:
        if self._rate is None:
            return "+0%"
        return f"{self._rate:+d}%"

    def _format_volume(self) -> str:
        if self._volume is None:
            return "+0%"
        percent = int(round(float(self._volume) * 100))
        return f"{percent:+d}%"

    async def _synthesize(self, text: str, output_path: Path) -> None:
        communicate = edge_tts.Communicate(
            text=text,
            voice=self._voice,
            rate=self._format_rate(),
            volume=self._format_volume(),
        )
        await communicate.save(str(output_path))

    def speak(self, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp_path = Path(tmp.name)
        tmp.close()

        try:
            asyncio.run(self._synthesize(text, tmp_path))
            playsound(str(tmp_path))
        except Exception as exc:  # pragma: no cover
            raise VoiceError(f"Falha no TTS (edge-tts): {exc}") from exc
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
