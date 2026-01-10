from __future__ import annotations

from iuno.voice.base import SpeechToText, VoiceError


class SpeechRecognitionSTT(SpeechToText):
    """STT simples usando a biblioteca `speech_recognition`.

    Implementacao: transcreve audio via servico Google Web Speech.
    - Pros: facil e funciona em Windows.
    - Contras: requer internet.

    Baseada em arquivo para ser mais robusta (microfone costuma exigir
    dependencias adicionais no Windows).
    """

    def __init__(self) -> None:
        try:
            import speech_recognition as sr
        except Exception as exc:  # pragma: no cover
            raise VoiceError(
                "speechrecognition nao esta instalado. Instale com: pip install SpeechRecognition"
            ) from exc

        self._sr = sr
        self._recognizer = sr.Recognizer()

    def transcribe_file(self, path: str, language: str = "pt-BR") -> str:
        sr = self._sr
        try:
            with sr.AudioFile(path) as source:
                audio = self._recognizer.record(source)
            text = self._recognizer.recognize_google(audio, language=language)
            return text.strip()
        except sr.UnknownValueError as exc:
            raise VoiceError("Nao consegui entender o audio.") from exc
        except sr.RequestError as exc:
            raise VoiceError(f"Falha no servico de STT: {exc}") from exc
        except FileNotFoundError as exc:
            raise VoiceError(f"Arquivo de audio nao encontrado: {path}") from exc
