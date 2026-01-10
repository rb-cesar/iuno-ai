from iuno.core.orchestrator import Orchestrator
from iuno.llm.base import LLMClient
from iuno.memory.memory_base import MemoryStore


class _FakeMemory(MemoryStore):
    def __init__(self):
        self.saved = None

    def load(self):
        return {}

    def save(self, state):
        self.saved = state


class _FakeLLM(LLMClient):
    def chat(self, messages):
        return "Hello"

    def chat_stream(self, messages):
        yield "Hel"
        yield "lo"


def test_orchestrator_accumulates_streamed_response(monkeypatch, capsys):
    # Simula uma interação: uma mensagem e depois sair
    inputs = iter(["oi", "sair"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    orch = Orchestrator(_FakeLLM(), _FakeMemory(), stream=True)
    orch.run_cli()

    # A última mensagem deve ser a resposta completa
    assert orch.history[-1]["role"] == "assistant"
    assert orch.history[-1]["content"] == "Hello"

    # Também garante que imprimiu em streaming (apareceu "Iuno: Hel" antes de completar)
    out = capsys.readouterr().out
    assert "Iuno:" in out
    assert "Hello" in out

