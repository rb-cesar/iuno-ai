# Iuno AI (CLI) — Guia de Uso

Assistente em modo texto com memória simples e suporte a **respostas em tempo real (streaming)** via Ollama.

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

## Preparando o Ollama

1. Inicie o Ollama (normalmente ele já fica rodando em background após instalar).
2. Garanta que o modelo configurado no código exista.

O modelo padrão está em `main.py`:

- `OllamaClient(model="gpt-oss:20b")`

Se você não tiver esse modelo, troque por um que você tenha instalado.

## Executando

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

Use a variável de ambiente `IUNO_STREAM=false`.

```powershell
$env:IUNO_STREAM="false"
py main.py
```

### Ligar streaming explicitamente

```powershell
$env:IUNO_STREAM="true"
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

## Rodando testes

Este repositório inclui testes unitários para o streaming.

```powershell
py -m pip install pytest
py -m pytest -q
```

