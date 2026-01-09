from iuno.core.orchestrator import Orchestrator
from iuno.llm.base import LLMClient
from iuno.memory.memory_base import MemoryStore
from iuno.voice.base import VoiceConfig, SpeechToText, TextToSpeech


class _FakeMemory(MemoryStore):
    def __init__(self):
        self.saved = None

    def load(self):
        return {}

    def save(self, data):
        self.saved = data


class _FakeLLM(LLMClient):
    def chat(self, messages):
        return "ok"

    def chat_stream(self, messages):
        yield "o"
        yield "k"


class _FakeSTT(SpeechToText):
    def __init__(self, transcript: str):
        self.transcript = transcript
        self.calls = []

    def transcribe_file(self, path: str, language: str = "pt-BR") -> str:
        self.calls.append((path, language))
        return self.transcript


class _FakeTTS(TextToSpeech):
    def __init__(self):
        self.spoken = []

    def speak(self, text: str) -> None:
        self.spoken.append(text)


def test_voice_in_uses_stt_transcript(monkeypatch):
    inputs = iter([r"C:\tmp\audio.wav", "sair"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    stt = _FakeSTT("oi")
    voice = VoiceConfig(enable_voice_in=True, enable_voice_out=False, stt_language="pt-BR")

    orch = Orchestrator(_FakeLLM(), _FakeMemory(), stream=False, voice=voice, stt=stt, tts=None)
    orch.run_cli()

    # Deve ter chamado STT com o path
    assert stt.calls == [(r"C:\tmp\audio.wav", "pt-BR")]

    # A mensagem do usuário no histórico deve ser o transcript
    assert any(m["role"] == "user" and m["content"] == "oi" for m in orch.history)


def test_voice_out_calls_tts(monkeypatch):
    inputs = iter(["oi", "sair"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    tts = _FakeTTS()
    voice = VoiceConfig(enable_voice_in=False, enable_voice_out=True)

    orch = Orchestrator(_FakeLLM(), _FakeMemory(), stream=True, voice=voice, stt=None, tts=tts)
    orch.run_cli()

    # Deve falar a resposta final completa
    assert tts.spoken == ["ok"]

