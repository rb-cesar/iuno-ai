from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Body, FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel

from iuno.services.config import env_str
from iuno.services.iuno_service import TTSResult, build_service
from iuno.voice.base import VoiceError

load_dotenv()

app = FastAPI(title="Iuno API")

_VERSION = env_str("IUNO_VERSION", "dev")


class TTSRequest(BaseModel):
    text: str
    format: Optional[str] = None


class ChatMessage(BaseModel):
    type: str
    content: Optional[str] = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": _VERSION}


@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)) -> dict:
    service = build_service()

    suffix = Path(file.filename or "audio").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        text = service.transcribe_file(str(tmp_path))
    except VoiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    return {"text": text}


@app.post("/tts")
async def text_to_speech(payload: TTSRequest = Body(...)) -> Response:
    service = build_service()
    try:
        result: TTSResult = await asyncio.to_thread(
            service.synthesize,
            payload.text,
            payload.format,
        )
    except VoiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return Response(
        content=result.audio,
        media_type=result.media_type,
        headers={"Content-Disposition": f'inline; filename="{result.filename}"'},
    )


@app.websocket("/chat")
async def chat_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    service = build_service()

    try:
        while True:
            data = await websocket.receive_json()
            try:
                message = ChatMessage(**data)
            except Exception:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Payload invalido.",
                    }
                )
                continue

            if message.type != "user_message":
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Tipo de mensagem invalido. Use 'user_message'.",
                    }
                )
                continue

            text = (message.content or "").strip()
            if not text:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Mensagem vazia.",
                    }
                )
                continue

            collected: list[str] = []
            for chunk in service.stream_chat(text):
                collected.append(chunk)
                await websocket.send_json(
                    {
                        "type": "assistant_chunk",
                        "content": chunk,
                    }
                )

            response_text = "".join(collected)
            await websocket.send_json(
                {
                    "type": "assistant_done",
                    "content": response_text,
                }
            )
    except WebSocketDisconnect:
        return
