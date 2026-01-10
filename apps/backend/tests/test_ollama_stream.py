import json
from types import SimpleNamespace

import pytest

from iuno.llm.ollama_client import OllamaClient


class _FakeResponse:
    def __init__(self, lines):
        self._lines = lines

    def raise_for_status(self):
        return None

    def iter_lines(self, decode_unicode=True):
        for l in self._lines:
            yield l

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_chat_stream_parses_ndjson(monkeypatch):
    lines = [
        json.dumps({"message": {"content": "Hel"}, "done": False}),
        json.dumps({"message": {"content": "lo"}, "done": False}),
        json.dumps({"done": True}),
    ]

    def fake_post(*args, **kwargs):
        assert kwargs.get("stream") is True
        return _FakeResponse(lines)

    monkeypatch.setattr("requests.post", fake_post)

    client = OllamaClient(model="dummy", base_url="http://localhost:11434")
    out = list(client.chat_stream([{"role": "user", "content": "hi"}]))
    assert out == ["Hel", "lo"]

