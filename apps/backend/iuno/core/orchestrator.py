from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

from iuno.llm.base import LLMClient
from iuno.memory.memory_base import MemoryStore
from iuno.memory.state import add_long_term_fact, ensure_default_state, touch_long_term_facts
from iuno.persona.prompts import SYSTEM_PROMPT
from iuno.voice.base import AudioRecorder, SpeechToText, TextToSpeech, VoiceConfig

Message = Dict[str, str]
Fact = Dict[str, Any]

_EXIT_COMMANDS = {"sair", "exit", "quit"}
_NAME_PATTERNS = [
    re.compile(r"\bmeu nome (?:e|\u00e9) ([^.!\n]+)", re.IGNORECASE),
    re.compile(r"\bpode me chamar de ([^.!\n]+)", re.IGNORECASE),
]
_AGE_PATTERN = re.compile(r"\btenho\s+(\d{1,2})\s*anos\b", re.IGNORECASE)
_PROJECT_PATTERN = re.compile(
    r"\bestou\s+(?:estudando|trabalhando em|fazendo)\s+([^.,\n]+)",
    re.IGNORECASE,
)
_FORMAL_PATTERN = re.compile(r"\bmais formal\b", re.IGNORECASE)
_CASUAL_PATTERN = re.compile(r"\bmais casual\b|\bde boa\b", re.IGNORECASE)


class Orchestrator:
    """Orquestrador principal da Iuno.

    - Cuida do historico de mensagens (memoria de curto prazo).
    - Integra LLM, memoria de longo prazo e (no futuro) voz.
    """

    def __init__(
        self,
        llm: LLMClient,
        memory: MemoryStore,
        stream: bool = True,
        voice: Optional[VoiceConfig] = None,
        stt: Optional[SpeechToText] = None,
        tts: Optional[TextToSpeech] = None,
        recorder: Optional[AudioRecorder] = None,
    ) -> None:
        self.llm = llm
        self.memory_store = memory
        self.stream = stream

        self.voice = voice or VoiceConfig()
        self.stt = stt
        self.tts = tts
        self.recorder = recorder

        raw_state = self.memory_store.load()
        self.state = ensure_default_state(raw_state)

        self.history: List[Message] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        # contador de turnos de conversa (user + iuno)
        self.turn_count = 0

        self._temp_audio_files: List[str] = []

    def _cleanup_temp_audio_files(self) -> None:
        if not getattr(self.voice, "cleanup_audio_files", False):
            return
        for path in list(self._temp_audio_files):
            try:
                os.remove(path)
            except OSError:
                pass
        self._temp_audio_files.clear()

    def _discard_temp_audio(self, path: str) -> None:
        try:
            os.remove(path)
        except OSError:
            pass
        try:
            self._temp_audio_files.remove(path)
        except ValueError:
            pass

    def _shutdown(self) -> None:
        self._cleanup_temp_audio_files()
        self.memory_store.save(self.state)

    def _add_message(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})

    def _is_exit_command(self, text: str) -> bool:
        return text.lower() in _EXIT_COMMANDS

    def _resolve_voice_in_mode(self) -> str:
        effective_voice_in_mode = self.voice.voice_in_mode
        if self.voice.enable_voice_in and effective_voice_in_mode == "mic" and not self.recorder:
            print(
                "[VOZ][AVISO] Modo microfone solicitado, mas o gravador nao esta configurado.\n"
                "[VOZ][AVISO] Vou usar o modo por arquivo WAV (IUNO_VOICE_IN_MODE=file).\n"
                "[VOZ][DICA] Para usar microfone direto, instale: pip install sounddevice\n"
            )
            effective_voice_in_mode = "file"
        return effective_voice_in_mode

    def _print_voice_in_instructions(self, voice_in_mode: str) -> None:
        if not self.voice.enable_voice_in:
            return

        if voice_in_mode == "mic":
            print("[VOZ] Entrada por microfone habilitada (push-to-talk via ENTER).\n")
        else:
            print("[VOZ] Entrada por voz habilitada. Informe o caminho de um arquivo WAV para transcrever.")
            print("[VOZ] Dica: voce pode arrastar/soltar o arquivo no terminal para colar o caminho.\n")

    def _prompt_user_input(self, voice_in_mode: str) -> str:
        if not self.voice.enable_voice_in:
            return input("Voce: ").strip()

        if voice_in_mode == "mic":
            cmd = input("(ENTER para gravar | 'sair'): ").strip()
            return cmd or "__MIC__"

        return input("Audio (WAV) ou 'sair': ").strip().strip('"')

    def _transcribe_voice_input(self, user_text: str, voice_in_mode: str) -> Optional[str]:
        if not self.voice.enable_voice_in:
            return user_text

        if not self.stt:
            print("[VOZ][ERRO] STT nao configurado.")
            return None

        created_temp_audio = False
        if voice_in_mode == "mic":
            if not self.recorder:
                print("[VOZ][ERRO] Gravador de microfone nao configurado.")
                return None
            try:
                audio_path = self.recorder.record_wav()
                created_temp_audio = True
                self._temp_audio_files.append(audio_path)
            except Exception as exc:
                print(f"[VOZ][ERRO] Falha ao gravar do microfone: {exc}")
                return None
        else:
            audio_path = user_text

        try:
            print("[VOZ] Transcrevendo audio...")
            transcript = self.stt.transcribe_file(audio_path, language=self.voice.stt_language)
        except Exception as exc:
            print(f"[VOZ][ERRO] Falha ao transcrever: {exc}")
            return None
        finally:
            if created_temp_audio and getattr(self.voice, "cleanup_audio_files", False):
                self._discard_temp_audio(audio_path)

        print(f"Voce (transcrito): {transcript}")
        return transcript

    def _update_memory_from_user_message(self, text: str) -> None:
        """Extrai fatos simples do texto do usuario e grava na memoria de longo prazo."""

        # Nome
        for pattern in _NAME_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue

            raw_name = match.group(1).strip(" .,!?:;\"'")
            if raw_name:
                name = raw_name.title()
                current_name = self.state["user_profile"].get("name")
                if current_name != name:
                    self.state["user_profile"]["name"] = name
                    add_long_term_fact(
                        self.state,
                        f"O usuario se chama {name}.",
                        importance=5,
                    )
                    print(f"[MEMORIA] Vou lembrar que seu nome e {name}.")
            break

        # Idade
        age_match = _AGE_PATTERN.search(text)
        if age_match:
            age = int(age_match.group(1))
            current_age = self.state["user_profile"].get("age")
            if current_age != age:
                self.state["user_profile"]["age"] = age
                add_long_term_fact(
                    self.state,
                    f"O usuario tem {age} anos.",
                    importance=4,
                )
                print(f"[MEMORIA] Vou lembrar que voce tem {age} anos.")

        # Projetos / estudos basicos
        project_match = _PROJECT_PATTERN.search(text)
        if project_match:
            project = project_match.group(1).strip(" .,!?:;\"'")
            if project:
                projects: List[str] = self.state.get("projects", [])
                if project not in projects:
                    projects.append(project)
                    self.state["projects"] = projects
                    add_long_term_fact(
                        self.state,
                        f"O usuario esta envolvido com o projeto/estudo: {project}.",
                        importance=3,
                    )
                    print(f"[MEMORIA] Vou lembrar que voce esta envolvido com: {project}.")

        # Preferencia de formalidade
        if _FORMAL_PATTERN.search(text):
            if self.state["preferences"].get("formality") != "formal":
                self.state["preferences"]["formality"] = "formal"
                add_long_term_fact(
                    self.state,
                    "O usuario prefere um tom mais formal nas respostas.",
                    importance=3,
                )
                print("[MEMORIA] Vou tentar falar de forma mais formal.")

        if _CASUAL_PATTERN.search(text):
            if self.state["preferences"].get("formality") != "casual":
                self.state["preferences"]["formality"] = "casual"
                add_long_term_fact(
                    self.state,
                    "O usuario prefere um tom mais casual nas respostas.",
                    importance=3,
                )
                print("[MEMORIA] Vou falar de forma mais casual.")

    def _select_relevant_facts(self, limit: int = 5) -> List[Fact]:
        facts: List[Fact] = list(self.state.get("long_term_facts", []))
        if not facts:
            return []

        def sort_key(fact: Fact) -> tuple:
            importance = int(fact.get("importance") or 0)
            last_accessed = fact.get("last_accessed")
            created_at = fact.get("created_at")
            return (-importance, last_accessed or "", created_at or "")

        facts.sort(key=sort_key)
        selected = facts[:limit]
        touch_long_term_facts(selected)
        return selected

    def _build_memory_context(self) -> Optional[str]:
        profile = self.state.get("user_profile", {})
        preferences = self.state.get("preferences", {})
        projects = self.state.get("projects", [])
        facts = self._select_relevant_facts()

        lines: List[str] = []
        name = profile.get("name")
        age = profile.get("age")
        location = profile.get("location")
        if name or age or location:
            lines.append("Perfil do usuario:")
            if name:
                lines.append(f"- Nome: {name}")
            if age:
                lines.append(f"- Idade: {age}")
            if location:
                lines.append(f"- Localizacao: {location}")

        formality = preferences.get("formality")
        language = preferences.get("language")
        if formality or language:
            lines.append("Preferencias:")
            if formality:
                lines.append(f"- Tom: {formality}")
            if language:
                lines.append(f"- Idioma: {language}")

        if projects:
            lines.append(f"Projetos atuais: {', '.join(projects)}")

        if facts:
            lines.append("Fatos relevantes:")
            for fact in facts:
                text = fact.get("text")
                if text:
                    lines.append(f"- {text}")

        if not lines:
            return None

        return "\n".join(lines)

    def _build_llm_messages(self) -> List[Message]:
        messages = list(self.history)
        memory_context = self._build_memory_context()
        if memory_context:
            messages.insert(1, {"role": "system", "content": memory_context})
        return messages

    def _call_model(self) -> Optional[str]:
        try:
            if self.stream:
                print("Iuno: ", end="", flush=True)
                chunks: List[str] = []
                for chunk in self.llm.chat_stream(self._build_llm_messages()):
                    chunks.append(chunk)
                    print(chunk, end="", flush=True)
                response = "".join(chunks)
                print("\n")
                return response

            response = self.llm.chat(self._build_llm_messages())
            print(f"Iuno: {response}\n")
            return response
        except KeyboardInterrupt:
            # Evita gravar uma resposta parcial no historico.
            print("\n\n[Interrompido]")
            self.memory_store.save(self.state)
            return None
        except Exception as exc:
            print(f"[ERRO ao chamar o modelo]: {exc}")
            return None

    def run_cli(self) -> None:
        """Loop de chat via terminal."""
        print("Iuno iniciada (modo texto). Digite 'sair' para encerrar.\n")

        effective_voice_in_mode = self._resolve_voice_in_mode()
        self._print_voice_in_instructions(effective_voice_in_mode)

        while True:
            try:
                user_text = self._prompt_user_input(effective_voice_in_mode)
            except (EOFError, KeyboardInterrupt):
                print("\n\nEncerrando...")
                self._shutdown()
                break

            if not user_text:
                continue

            if self._is_exit_command(user_text):
                print("Encerrando...")
                self._shutdown()
                break

            user_text = self._transcribe_voice_input(user_text, effective_voice_in_mode)
            if user_text is None:
                continue

            # Memoria de curto prazo
            self._add_message("user", user_text)

            # Memoria de longo prazo (A + B)
            self._update_memory_from_user_message(user_text)

            response = self._call_model()
            if response is None:
                continue

            self._add_message("assistant", response)
            self.turn_count += 1

            if self.voice.enable_voice_out and self.tts:
                try:
                    self.tts.speak(response)
                except Exception as exc:
                    print(f"[VOZ][ERRO] Falha no TTS: {exc}")

            # Persiste memoria de longo prazo
            self.memory_store.save(self.state)
