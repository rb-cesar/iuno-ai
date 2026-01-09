from __future__ import annotations

import queue
import threading
from typing import Optional

from iuno.voice.base import TextToSpeech, VoiceError


class ThreadedPyttsx3TTS(TextToSpeech):
    """TTS via pyttsx3 rodando num thread dedicado.

    Isso tende a ser mais confiável no Windows quando o loop da aplicação faz
    muita I/O no terminal (input/print/streaming) e o pyttsx3/SAPI5 acaba
    travando após a primeira fala.

    A API continua simples: `speak(text)` enfileira e retorna rapidamente.
    """

    def __init__(
        self,
        rate: Optional[int] = None,
        volume: Optional[float] = None,
        voice: Optional[str] = None,
        daemon: bool = True,
    ):
        self._rate = rate
        self._volume = volume
        self._voice = voice

        self._q: "queue.Queue[Optional[str]]" = queue.Queue()
        self._ready = threading.Event()
        self._err: Optional[BaseException] = None

        self._thread = threading.Thread(target=self._run, name="iuno-tts", daemon=daemon)
        self._thread.start()

        # Aguarda inicialização do engine para falhar rápido se não tiver pyttsx3.
        self._ready.wait(timeout=5)
        if self._err is not None:
            raise VoiceError(f"Falha ao inicializar TTS: {self._err}")

    def _run(self) -> None:  # pragma: no cover (thread)
        try:
            import pyttsx3

            engine = pyttsx3.init()

            if self._rate is not None:
                engine.setProperty("rate", self._rate)
            if self._volume is not None:
                engine.setProperty("volume", float(self._volume))

            if self._voice:
                selected = None
                try:
                    for v in engine.getProperty("voices"):
                        if v.id == self._voice or (
                            getattr(v, "name", "") and self._voice.lower() in v.name.lower()
                        ):
                            selected = v.id
                            break
                except Exception:
                    selected = None

                if selected:
                    engine.setProperty("voice", selected)

            self._ready.set()

            while True:
                text = self._q.get()
                if text is None:
                    break

                text = text.strip()
                if not text:
                    continue

                try:
                    engine.stop()
                except Exception:
                    pass

                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception:
                    # auto-cura: reinicializa engine e tenta uma vez
                    try:
                        engine = pyttsx3.init()
                        engine.say(text)
                        engine.runAndWait()
                    except Exception:
                        pass
                finally:
                    try:
                        engine.stop()
                    except Exception:
                        pass
        except BaseException as e:
            self._err = e
            self._ready.set()

    def speak(self, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return

        if self._err is not None:
            raise VoiceError(f"TTS indisponível: {self._err}")

        self._q.put(text)

    def close(self) -> None:
        """Finaliza o thread de TTS (opcional)."""
        self._q.put(None)

