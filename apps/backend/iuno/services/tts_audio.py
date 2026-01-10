from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional, Tuple

import edge_tts
import pyttsx3

from iuno.voice.base import VoiceError


def _format_rate(rate: Optional[int]) -> str:
    if rate is None:
        return "+0%"
    return f"{rate:+d}%"


def _format_volume(volume: Optional[float]) -> str:
    if volume is None:
        return "+0%"
    percent = int(round(float(volume) * 100))
    return f"{percent:+d}%"


def _select_voice(engine: pyttsx3.Engine, voice: Optional[str]) -> None:
    if not voice:
        return
    selected = None
    for entry in engine.getProperty("voices"):
        if entry.id == voice or (
            getattr(entry, "name", "") and voice.lower() in entry.name.lower()
        ):
            selected = entry.id
            break
    if selected:
        engine.setProperty("voice", selected)


def synthesize_pyttsx3(
    text: str,
    rate: Optional[int],
    volume: Optional[float],
    voice: Optional[str],
) -> Tuple[bytes, str, str]:
    engine = pyttsx3.init()
    if rate is not None:
        engine.setProperty("rate", rate)
    if volume is not None:
        engine.setProperty("volume", float(volume))
    _select_voice(engine, voice)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        output_path = Path(tmp.name)

    try:
        engine.save_to_file(text, str(output_path))
        engine.runAndWait()
        audio_bytes = output_path.read_bytes()
    except Exception as exc:  # pragma: no cover
        raise VoiceError(f"Falha no TTS (pyttsx3): {exc}") from exc
    finally:
        try:
            output_path.unlink(missing_ok=True)
        except Exception:
            pass

    return audio_bytes, "audio/wav", "speech.wav"


def synthesize_edge(
    text: str,
    rate: Optional[int],
    volume: Optional[float],
    voice: Optional[str],
) -> Tuple[bytes, str, str]:
    output_path = Path(tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name)

    async def _render() -> None:
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice or "pt-BR-FranciscaNeural",
            rate=_format_rate(rate),
            volume=_format_volume(volume),
        )
        await communicate.save(str(output_path))

    try:
        import asyncio

        asyncio.run(_render())
        audio_bytes = output_path.read_bytes()
    except Exception as exc:  # pragma: no cover
        raise VoiceError(f"Falha no TTS (edge-tts): {exc}") from exc
    finally:
        try:
            output_path.unlink(missing_ok=True)
        except Exception:
            pass

    return audio_bytes, "audio/mpeg", "speech.mp3"
