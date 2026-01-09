from __future__ import annotations

from typing import Optional

from iuno.voice.base import TextToSpeech, VoiceError


class Pyttsx3TTS(TextToSpeech):
    """TTS offline via pyttsx3 (no Windows, normalmente usa SAPI5).

    Observação: em alguns ambientes no Windows, o pyttsx3 pode "travar" depois da
    primeira fala se o loop interno ficar em um estado inconsistente. Esta classe
    tenta ser resiliente limpando a fila e reinicializando o engine em caso de erro.
    """

    def __init__(
        self,
        rate: Optional[int] = None,
        volume: Optional[float] = None,
        voice: Optional[str] = None,
    ):
        self._rate = rate
        self._volume = volume
        self._voice = voice
        self._engine = None
        self._init_engine()

    def _init_engine(self) -> None:
        try:
            import pyttsx3
        except Exception as e:  # pragma: no cover
            raise VoiceError(
                "pyttsx3 não está instalado. Instale com: pip install pyttsx3"
            ) from e

        engine = pyttsx3.init()

        if self._rate is not None:
            engine.setProperty("rate", self._rate)
        if self._volume is not None:
            engine.setProperty("volume", float(self._volume))

        if self._voice:
            selected = None
            try:
                for v in engine.getProperty("voices"):
                    if v.id == self._voice or (getattr(v, "name", "") and self._voice.lower() in v.name.lower()):
                        selected = v.id
                        break
            except Exception:
                selected = None

            if selected:
                engine.setProperty("voice", selected)

        self._engine = engine

    def speak(self, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return

        if self._engine is None:  # pragma: no cover
            self._init_engine()

        # Limpa qualquer fala pendente anterior.
        try:
            self._engine.stop()
        except Exception:
            pass

        try:
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as e:
            # Tentativa de auto-cura: reinicia o engine e tenta mais uma vez.
            try:
                self._init_engine()
                self._engine.say(text)
                self._engine.runAndWait()
                return
            except Exception:
                raise VoiceError(f"Falha no TTS (pyttsx3): {e}") from e
        finally:
            # Garante que o engine não fica com fila pendente.
            try:
                self._engine.stop()
            except Exception:
                pass
