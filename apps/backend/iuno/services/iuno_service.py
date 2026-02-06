from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from iuno.core.orchestrator import Orchestrator
from iuno.llm.ollama_client import OllamaClient
from iuno.memory.json_memory import JsonMemory
from iuno.services.config import (
    build_tool_policy,
    build_tool_registry,
    build_voice_config,
    env_flag,
    env_str,
    resolve_action_log_path,
)
from iuno.services.tts_audio import synthesize_edge, synthesize_pyttsx3
from iuno.voice.base import SpeechToText, VoiceError
from iuno.voice.stt_speech_recognition import SpeechRecognitionSTT


@dataclass(frozen=True)
class TTSResult:
    audio: bytes
    media_type: str
    filename: str


class IunoService:
    def __init__(
        self,
        model: str,
        base_url: str,
        memory_path: str,
        stream: bool,
        stt: Optional[SpeechToText] = None,
    ) -> None:
        self.voice_cfg = build_voice_config()
        self.stream = stream
        self.stt = stt or SpeechRecognitionSTT()
        self.tool_registry = build_tool_registry()
        self.tool_policy = build_tool_policy(interactive=False)
        self.tool_log_path = resolve_action_log_path()
        self.orchestrator = Orchestrator(
            OllamaClient(model=model, base_url=base_url),
            JsonMemory(file_path=memory_path),
            stream=stream,
            voice=self.voice_cfg,
            stt=self.stt,
            tts=None,
            recorder=None,
            tool_registry=self.tool_registry,
            tool_policy=self.tool_policy,
            tool_log_path=self.tool_log_path,
        )

    def chat(self, text: str) -> str:
        self._append_user_message(text)
        response = self.orchestrator.llm.chat(self.orchestrator._build_llm_messages())
        response = self.orchestrator.run_tool_loop(response, interactive=False)
        return self._finalize_response(response)

    def stream_chat(self, text: str) -> Iterable[str]:
        self._append_user_message(text)
        chunks: list[str] = []
        for chunk in self.orchestrator.llm.chat_stream(self.orchestrator._build_llm_messages()):
            chunks.append(chunk)
            yield chunk
        response = "".join(chunks)
        response = self.orchestrator.run_tool_loop(response, interactive=False)
        self._finalize_response(response)

    def transcribe_file(self, path: str) -> str:
        if not self.stt:
            raise VoiceError("STT nao configurado.")
        return self.stt.transcribe_file(path, language=self.voice_cfg.stt_language)

    def synthesize(self, text: str, audio_format: Optional[str] = None) -> TTSResult:
        text = (text or "").strip()
        if not text:
            raise VoiceError("Texto vazio para TTS.")

        provider = self.voice_cfg.tts_provider
        if audio_format is None:
            audio_format = "mp3" if provider == "edge" else "wav"
        audio_format = audio_format.lower()

        if provider == "edge":
            if audio_format != "mp3":
                raise VoiceError("Formato suportado para edge-tts: mp3.")
            audio, media_type, filename = synthesize_edge(
                text=text,
                rate=self.voice_cfg.tts_rate,
                volume=self.voice_cfg.tts_volume,
                voice=self.voice_cfg.tts_voice,
            )
            return TTSResult(audio=audio, media_type=media_type, filename=filename)

        if audio_format != "wav":
            raise VoiceError("Formato suportado para pyttsx3: wav.")

        audio, media_type, filename = synthesize_pyttsx3(
            text=text,
            rate=self.voice_cfg.tts_rate,
            volume=self.voice_cfg.tts_volume,
            voice=self.voice_cfg.tts_voice,
        )
        return TTSResult(audio=audio, media_type=media_type, filename=filename)

    def _append_user_message(self, text: str) -> None:
        self.orchestrator._add_message("user", text)
        self.orchestrator._update_memory_from_user_message(text)

    def _finalize_response(self, response: str) -> str:
        response = response or ""
        self.orchestrator._add_message("assistant", response)
        self.orchestrator.turn_count += 1
        self.orchestrator.memory_store.save(self.orchestrator.state)
        return response


def build_service() -> IunoService:
    return IunoService(
        model=env_str("IUNO_OLLAMA_MODEL", "gpt-oss:20b"),
        base_url=env_str("IUNO_OLLAMA_BASE_URL", "http://localhost:11434"),
        memory_path=env_str("IUNO_MEMORY_PATH", "memory.json"),
        stream=env_flag("IUNO_STREAM", True),
    )
