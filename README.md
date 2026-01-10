# Iuno AI — Monorepo

Este repositório agora é um monorepo com:

- `apps/backend`: backend em Python (CLI/API).
- `apps/desktop`: app desktop (Electron + React/Vite/TS/Tailwind).

## Workspace (raiz)

Instale dependências do workspace e use os scripts de atalho:

```bash
npm install
```

```bash
# backend
npm run dev:backend

# desktop
npm run dev:desktop
npm run build:desktop
```

> Os scripts do backend apenas chamam `python apps/backend/main.py`.

## Backend (Python)

### Requisitos

- Python **3.11+**
- [Ollama](https://ollama.com/) instalado e rodando localmente
- Um modelo disponível no Ollama (ex.: `gpt-oss:20b`, `llama3`, etc.)

> Este projeto usa a API do Ollama em `http://localhost:11434`.

### Instalação

Crie/ative seu ambiente virtual (recomendado) e instale as dependências:

```powershell
cd apps/backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

### Configuração por arquivo `.env` (recomendado)

Você pode colocar suas configs num arquivo `.env` dentro de `apps/backend`.

1) Crie o `.env` a partir do exemplo:

```powershell
cd apps/backend
Copy-Item .env.example .env
```

2) Edite o arquivo `.env` e ajuste os valores (ex.: `IUNO_VOICE_OUT=true`).

3) Rode normalmente:

```powershell
py main.py
```

> O app carrega automaticamente o `.env` ao iniciar (via `python-dotenv`).

### Configuração rápida (variáveis de ambiente)

| Variável | Padrão | O que faz |
|---|---:|---|
| `IUNO_STREAM` | `true` | Ativa/desativa streaming da resposta no terminal |
| `IUNO_VOICE_IN` | `false` | Ativa entrada por voz (STT) |
| `IUNO_VOICE_IN_MODE` | `file` | `file`=WAV por caminho, `mic`=microfone direto |
| `IUNO_VOICE_OUT` | `false` | Ativa saída por voz (TTS) |
| `IUNO_STT_LANG` | `pt-BR` | Idioma do STT (ex.: `en-US`) |
| `IUNO_MIC_SAMPLE_RATE` | `16000` | Sample rate de gravação do mic |
| `IUNO_MIC_CHANNELS` | `1` | Canais do mic (1=mono) |
| `IUNO_AUDIO_DIR` | `data/audio` | Pasta para salvar WAVs gravados no modo mic |
| `IUNO_CLEANUP_AUDIO_FILES` | `true` | Apaga WAVs gravados automaticamente após transcrever/ao encerrar |
| `IUNO_TTS_RATE` | vazio | Velocidade do TTS (ex.: `180`) |
| `IUNO_TTS_VOLUME` | vazio | Volume do TTS (0.0 a 1.0) |
| `IUNO_TTS_VOICE` | vazio | Nome/id parcial da voz (depende do Windows) |
| `IUNO_TTS_PROVIDER` | `pyttsx3` | Provedor de TTS: `pyttsx3` (offline) ou `edge` (neural online) |

### Preparando o Ollama

1. Inicie o Ollama (normalmente ele já fica rodando em background após instalar).
2. Garanta que o modelo configurado no código exista.

O modelo padrão está em `apps/backend/main.py`:

- `OllamaClient(model="gpt-oss:20b")`

Se você não tiver esse modelo, troque por um que você tenha instalado.

### Executando (modo texto)

```powershell
cd apps/backend
py main.py
```

Você verá algo como:

- `Iuno iniciada (modo texto). Digite 'sair' para encerrar.`

Digite sua mensagem após `Você:`.

Para sair:
- `sair` (ou `exit` / `quit`)

### Streaming (resposta em tempo real)

Por padrão, o streaming fica **ligado**. Nesse modo, a Iuno imprime a resposta conforme ela chega do Ollama.

#### Desligar streaming

```powershell
$env:IUNO_STREAM="false"
py main.py
```

#### Ligar streaming explicitamente

```powershell
$env:IUNO_STREAM="true"
py main.py
```

## Voz (STT e TTS)

### TTS (falar as respostas)

O TTS pode ser **offline** com `pyttsx3` (no Windows tipicamente via SAPI5) ou **neural online** com `edge-tts`.

```powershell
# pelo .env: IUNO_VOICE_OUT=true
py main.py
```

Configurações opcionais:

```powershell
$env:IUNO_VOICE_OUT="true"
$env:IUNO_TTS_RATE="180"
$env:IUNO_TTS_VOLUME="0.9"
# $env:IUNO_TTS_VOICE="nome-parcial-ou-id"  # opcional
py main.py
```

#### Usando voz neural (mais natural)

Se quiser uma voz feminina natural e doce, use o provedor `edge` com a voz
`pt-BR-FranciscaNeural` (padrão quando `IUNO_TTS_PROVIDER=edge`):

```powershell
$env:IUNO_VOICE_OUT="true"
$env:IUNO_TTS_PROVIDER="edge"
$env:IUNO_TTS_VOICE="pt-BR-FranciscaNeural"
py main.py
```

### STT (entrada por voz)

O STT atual usa a biblioteca `SpeechRecognition` com o serviço **Google Web Speech**.

- Requer internet
- O áudio é enviado para transcrição

Você tem dois modos de entrada:

#### Modo 1: arquivo WAV (padrão)

```powershell
# pelo .env:
# IUNO_VOICE_IN=true
# IUNO_VOICE_IN_MODE=file
py main.py
```

Nessa opção você informa o caminho de um `.wav`.

#### Modo 2: microfone direto (push-to-talk)

Este modo grava do microfone e gera um WAV automaticamente.

- Por padrão ele grava em `data/audio/` **dentro do projeto**
- Por padrão ele **apaga o WAV** assim que transcrever (para não acumular arquivos)

Você pode controlar isso por `.env`:

- `IUNO_AUDIO_DIR` (caminho da pasta de saída)
- `IUNO_CLEANUP_AUDIO_FILES` (`true`/`false`)

1) Instale a dependência opcional:

```powershell
py -m pip install sounddevice
```

2) No `.env`, habilite:

- `IUNO_VOICE_IN=true`
- `IUNO_VOICE_IN_MODE=mic`

3) Rode:

```powershell
py main.py
```

No terminal:
- Pressione **ENTER** para começar a gravar
- Pressione **ENTER** novamente para parar

> Se o `sounddevice` não estiver instalado ou der erro de dispositivo, o modo microfone não vai funcionar. Nesse caso, use `IUNO_VOICE_IN_MODE=file` como fallback.

### STT + TTS juntos

```powershell
# no .env:
# IUNO_VOICE_IN=true
# IUNO_VOICE_IN_MODE=file
# IUNO_VOICE_OUT=true
py main.py
```

## Desktop (Electron + React/Vite/TS/Tailwind)

A base do app desktop fica em `apps/desktop`.

```bash
cd apps/desktop
```

