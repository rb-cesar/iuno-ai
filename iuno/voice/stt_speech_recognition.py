from __future__ import annotations

from iuno.voice.base import SpeechToText, VoiceError


class SpeechRecognitionSTT(SpeechToText):
    """STT simples usando a biblioteca `speech_recognition`.

    Implementação: transcreve áudio via serviço Google Web Speech.
    - Prós: fácil e funciona em Windows.
    - Contras: requer internet.

    É deliberadamente baseada em arquivo para ser mais robusta (microfone costuma
    exigir dependências adicionais no Windows).
    """

    def __init__(self):
        try:
            import speech_recognition as sr
        except Exception as e:  # pragma: no cover
            raise VoiceError(
                "speechrecognition não está instalado. Instale com: pip install SpeechRecognition"
            ) from e

        self._sr = sr
        self._recognizer = sr.Recognizer()

    def transcribe_file(self, path: str, language: str = "pt-BR") -> str:
        sr = self._sr
        try:
            with sr.AudioFile(path) as source:
                audio = self._recognizer.record(source)
            text = self._recognizer.recognize_google(audio, language=language)
            return text.strip()
        except sr.UnknownValueError as e:
            raise VoiceError("Não consegui entender o áudio.") from e
        except sr.RequestError as e:
            raise VoiceError(f"Falha no serviço de STT: {e}") from e
        except FileNotFoundError as e:
            raise VoiceError(f"Arquivo de áudio não encontrado: {path}") from e

