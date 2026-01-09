import re
import sys
from typing import List, Dict, Optional

from iuno.llm.base import LLMClient
from iuno.memory.memory_base import MemoryStore
from iuno.memory.state import ensure_default_state, add_long_term_fact
from iuno.persona.prompts import SYSTEM_PROMPT
from iuno.voice.base import SpeechToText, TextToSpeech, VoiceConfig, AudioRecorder


class Orchestrator:
    """
    Orquestrador principal da Iuno.
    - Cuida do histórico de mensagens (memória de curto prazo).
    - Integra LLM, memória de longo prazo e (no futuro) voz.
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
    ):
        self.llm = llm
        self.memory_store = memory
        self.stream = stream

        self.voice = voice or VoiceConfig()
        self.stt = stt
        self.tts = tts
        self.recorder = recorder

        raw_state = self.memory_store.load()
        self.state = ensure_default_state(raw_state)

        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        # contador de turnos de conversa (user + iuno)
        self.turn_count = 0

    # ---------- MÉTODOS INTERNOS DE HISTÓRICO ----------

    def _add_message(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})

    # ---------- MEMÓRIA AUTOMÁTICA (OPÇÃO A + B) ----------

    def _update_memory_from_user_message(
            self,
            text: str,
            assistant_reply: Optional[str] = None,
    ) -> None:
        """
        Extrai fatos simples do texto do usuário e grava na memória de longo prazo.
        Regras simples por regex:
        - Nome: "meu nome é X", "pode me chamar de X"
        - Idade: "tenho 24 anos"
        - Projeto/estudo: "estou estudando X", "estou trabalhando em X"
        - Preferência de formalidade: "pode falar de forma mais formal/casual"
        """

        # Nome
        name_patterns = [
            re.compile(r"\bmeu nome é ([^.!\n]+)", re.IGNORECASE),
            re.compile(r"\bpode me chamar de ([^.!\n]+)", re.IGNORECASE),
        ]
        for pat in name_patterns:
            match = pat.search(text)
            if match:
                raw_name = match.group(1).strip(" .,!?:;\"'")
                if raw_name:
                    name = raw_name.title()
                    current_name = self.state["user_profile"].get("name")
                    if current_name != name:
                        self.state["user_profile"]["name"] = name
                        add_long_term_fact(
                            self.state,
                            f"O usuário se chama {name}.",
                            importance=5,
                        )
                        print(f"[MEMÓRIA] Vou lembrar que seu nome é {name}.")
                break

        # Idade
        age_pattern = re.compile(r"\btenho\s+(\d{1,2})\s*anos\b", re.IGNORECASE)
        age_match = age_pattern.search(text)
        if age_match:
            age = int(age_match.group(1))
            current_age = self.state["user_profile"].get("age")
            if current_age != age:
                self.state["user_profile"]["age"] = age
                add_long_term_fact(
                    self.state,
                    f"O usuário tem {age} anos.",
                    importance=4,
                )
                print(f"[MEMÓRIA] Vou lembrar que você tem {age} anos.")

        # Projetos / estudos básicos
        project_pattern = re.compile(
            r"\bestou\s+(?:estudando|trabalhando em|fazendo)\s+([^.,\n]+)",
            re.IGNORECASE,
        )
        proj_match = project_pattern.search(text)
        if proj_match:
            project = proj_match.group(1).strip(" .,!?:;\"'")
            if project:
                projects: List[str] = self.state.get("projects", [])
                if project not in projects:
                    projects.append(project)
                    self.state["projects"] = projects
                    add_long_term_fact(
                        self.state,
                        f"O usuário está envolvido com o projeto/estudo: {project}.",
                        importance=3,
                    )
                    print(f"[MEMÓRIA] Vou lembrar que você está envolvido com: {project}.")

        # Preferência de formalidade
        if re.search(r"\bmais formal\b", text, re.IGNORECASE):
            if self.state["preferences"].get("formality") != "formal":
                self.state["preferences"]["formality"] = "formal"
                add_long_term_fact(
                    self.state,
                    "O usuário prefere um tom mais formal nas respostas.",
                    importance=3,
                )
                print("[MEMÓRIA] Vou tentar falar de forma mais formal.")

        if re.search(r"\bmais casual\b|\bde boa\b", text, re.IGNORECASE):
            if self.state["preferences"].get("formality") != "casual":
                self.state["preferences"]["formality"] = "casual"
                add_long_term_fact(
                    self.state,
                    "O usuário prefere um tom mais casual nas respostas.",
                    importance=3,
                )
                print("[MEMÓRIA] Vou falar de forma mais casual.")

        # Aqui você pode acrescentar outras regras (cidade, horário de estudo, etc.)

    # ---------- LOOP PRINCIPAL (CLI) ----------

    def run_cli(self) -> None:
        """Loop de chat via terminal."""
        print("Iuno iniciada (modo texto). Digite 'sair' para encerrar.\n")
        if self.voice.enable_voice_in:
            if self.voice.voice_in_mode == "mic":
                print("[VOZ] Entrada por microfone habilitada (push-to-talk via ENTER).\n")
            else:
                print("[VOZ] Entrada por voz habilitada. Informe o caminho de um arquivo WAV para transcrever.")
                print("[VOZ] Dica: você pode arrastar/soltar o arquivo no terminal para colar o caminho.\n")

        while True:
            try:
                if self.voice.enable_voice_in:
                    if self.voice.voice_in_mode == "mic":
                        cmd = input("(ENTER para gravar | 'sair'): ").strip()
                        if not cmd:
                            user_text = "__MIC__"
                        else:
                            user_text = cmd
                    else:
                        user_audio_path = input("Áudio (WAV) ou 'sair': ").strip().strip('"')
                        if not user_audio_path:
                            continue
                        user_text = user_audio_path
                else:
                    user_text = input("Você: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nEncerrando...")
                self.memory_store.save(self.state)
                break

            if not user_text:
                continue

            if user_text.lower() in {"sair", "exit", "quit"}:
                print("Encerrando...")
                self.memory_store.save(self.state)
                break

            # Se estiver em modo voz, primeiro obtém/transcreve o áudio.
            if self.voice.enable_voice_in:
                if not self.stt:
                    print("[VOZ][ERRO] STT não configurado.")
                    continue

                audio_path = None
                if self.voice.voice_in_mode == "mic":
                    if not self.recorder:
                        print("[VOZ][ERRO] Gravador de microfone não configurado.")
                        continue
                    try:
                        audio_path = self.recorder.record_wav()
                    except Exception as e:
                        print(f"[VOZ][ERRO] Falha ao gravar do microfone: {e}")
                        continue
                else:
                    audio_path = user_text

                try:
                    transcript = self.stt.transcribe_file(audio_path, language=self.voice.stt_language)
                except Exception as e:
                    print(f"[VOZ][ERRO] Falha ao transcrever: {e}")
                    continue

                user_text = transcript
                print(f"Você (transcrito): {user_text}")

            # Memória de curto prazo
            self._add_message("user", user_text)

            # Memória de longo prazo (A + B)
            self._update_memory_from_user_message(user_text)

            try:
                if self.stream:
                    print("Iuno: ", end="", flush=True)
                    chunks: List[str] = []
                    for chunk in self.llm.chat_stream(self.history):
                        chunks.append(chunk)
                        print(chunk, end="", flush=True)
                    response = "".join(chunks)
                    print("\n")
                else:
                    response = self.llm.chat(self.history)
                    print(f"Iuno: {response}\n")
            except KeyboardInterrupt:
                # Evita gravar uma resposta parcial no histórico.
                print("\n\n[Interrompido]")
                self.memory_store.save(self.state)
                continue
            except Exception as e:
                print(f"[ERRO ao chamar o modelo]: {e}")
                continue

            self._add_message("assistant", response)
            self.turn_count += 1

            if self.voice.enable_voice_out and self.tts:
                try:
                    self.tts.speak(response)
                except Exception as e:
                    print(f"[VOZ][ERRO] Falha no TTS: {e}")

            # Persiste memória de longo prazo
            self.memory_store.save(self.state)
