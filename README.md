# Iuno AI (CLI) — Guia de Uso

Assistente em modo texto com memória simples e suporte a **respostas em tempo real (streaming)** via Ollama, com opções de **voz**:

- **STT (Speech-to-Text)**: transcrição de áudio → texto
- **TTS (Text-to-Speech)**: falar as respostas em voz alta

## Requisitos

- Python **3.11+**
- [Ollama](https://ollama.com/) instalado e rodando localmente
- Um modelo disponível no Ollama (ex.: `gpt-oss:20b`, `llama3`, etc.)

> Este projeto usa a API do Ollama em `http://localhost:11434`.

## Instalação

Crie/ative seu ambiente virtual (recomendado) e instale as dependências:

```powershell
cd C:\Dev\iuno-ai
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

## Configuração rápida (variáveis de ambiente)

| Variável | Padrão | O que faz |
|---|---:|---|
| `IUNO_STREAM` | `true` | Ativa/desativa streaming da resposta no terminal |
| `IUNO_VOICE_IN` | `false` | Ativa entrada por voz (STT) |
| `IUNO_VOICE_OUT` | `false` | Ativa saída por voz (TTS) |
| `IUNO_STT_LANG` | `pt-BR` | Idioma do STT (ex.: `en-US`) |
| `IUNO_TTS_RATE` | vazio | Velocidade do TTS (ex.: `180`) |
| `IUNO_TTS_VOLUME` | vazio | Volume do TTS (0.0 a 1.0) |
| `IUNO_TTS_VOICE` | vazio | Nome/id parcial da voz (depende do Windows) |

## Preparando o Ollama

1. Inicie o Ollama (normalmente ele já fica rodando em background após instalar).
2. Garanta que o modelo configurado no código exista.

O modelo padrão está em `main.py`:

- `OllamaClient(model="gpt-oss:20b")`

Se você não tiver esse modelo, troque por um que você tenha instalado.

## Executando (modo texto)

```powershell
py main.py
```

Você verá algo como:

- `Iuno iniciada (modo texto). Digite 'sair' para encerrar.`

Digite sua mensagem após `Você:`.

Para sair:
- `sair` (ou `exit` / `quit`)

## Streaming (resposta em tempo real)

Por padrão, o streaming fica **ligado**. Nesse modo, a Iuno imprime a resposta conforme ela chega do Ollama.

### Desligar streaming

```powershell
$env:IUNO_STREAM="false"
py main.py
```

### Ligar streaming explicitamente

```powershell
$env:IUNO_STREAM="true"
py main.py
```

## Voz (STT e TTS)

### TTS (falar as respostas)

O TTS atual é **offline** e usa `pyttsx3` (no Windows tipicamente via SAPI5).

```powershell
$env:IUNO_VOICE_OUT="true"
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

### STT (entrada por voz)

O STT atual foi implementado no modo mais robusto para Windows: **transcrição de um arquivo WAV**.

Quando está habilitado, em vez de digitar a mensagem, você informa o caminho de um `.wav`.

```powershell
$env:IUNO_VOICE_IN="true"
py main.py
```

Você verá o prompt:

- `Áudio (WAV) ou 'sair':`

Dicas:
- Você pode **arrastar e soltar** o arquivo no terminal para colar o caminho.
- Idioma padrão: `pt-BR`. Para mudar:

```powershell
$env:IUNO_VOICE_IN="true"
$env:IUNO_STT_LANG="en-US"
py main.py
```

#### Privacidade / Internet

O STT atual usa a biblioteca `SpeechRecognition` com o serviço **Google Web Speech**, então **requer internet** e o áudio é enviado para transcrição.

Se você precisar de STT 100% offline, dá pra evoluir o projeto para usar um modelo local (ex.: Whisper via `faster-whisper`).

#### Como gerar um WAV rapidamente

Algumas opções:
- Use um gravador qualquer e exporte para WAV (PCM é o mais seguro).
- Se você já tem um arquivo em outro formato (mp3/m4a), converta para wav.

> Se você quiser, eu posso adicionar um modo de **microfone (push-to-talk)** para gravar direto do terminal e gerar o WAV automaticamente.

### STT + TTS juntos

```powershell
$env:IUNO_VOICE_IN="true"
$env:IUNO_VOICE_OUT="true"
py main.py
```

## Memória

A Iuno mantém um estado simples (perfil do usuário, preferências e fatos) e persiste via `JsonMemory`.

- O arquivo de estado local costuma ser `memory.json`.
- Por padrão, este repositório está com `memory.json` ignorado no Git (ver `.gitignore`).

Durante a conversa, ela tenta extrair fatos básicos (por regex), por exemplo:
- `meu nome é ...`
- `tenho 24 anos`
- `estou estudando ...`
- preferência por tom mais formal/casual

## Solução de Problemas

### Erro ao chamar o modelo / conexão

Se aparecer algo como erro de conexão:
- Verifique se o Ollama está rodando
- Confirme se a API está acessível em `http://localhost:11434`
- Confira se o modelo configurado em `main.py` existe no Ollama

### Streaming não aparece “ao vivo”

- Confirme que `IUNO_STREAM` não está definido como `false`
- Alguns terminais podem bufferizar saída; este projeto usa `flush=True` para reduzir isso

### TTS não fala

- Confirme `IUNO_VOICE_OUT=true`
- Garanta que o Windows está com um dispositivo de saída de áudio ativo
- Se estiver em um ambiente sem áudio (RDP/VM), o TTS pode não tocar

### STT não transcreve

- Confirme `IUNO_VOICE_IN=true`
- Use um WAV suportado (PCM é o mais seguro)
- O STT atual requer internet (serviço Google Web Speech)

## Rodando testes

```powershell
py -m pip install pytest
py -m pytest -q
```
