from __future__ import annotations

import time
import webbrowser
from pathlib import Path
from typing import Any, Dict

from iuno.tools.base import ToolError, ToolResult, ToolSpec


def _require_pyautogui():
    try:
        import pyautogui
    except Exception as exc:  # pragma: no cover
        raise ToolError(
            "pyautogui nao esta disponivel. Instale com: pip install pyautogui"
        ) from exc
    return pyautogui


def _require_mss():
    try:
        import mss
        import mss.tools
    except Exception as exc:  # pragma: no cover
        raise ToolError("mss nao esta disponivel. Instale com: pip install mss") from exc
    return mss


def open_url(args: Dict[str, Any]) -> ToolResult:
    url = (args.get("url") or "").strip()
    if not url:
        raise ToolError("URL obrigatoria.")
    opened = webbrowser.open(url)
    return ToolResult(ok=opened, output=f"URL aberta: {url}")


def type_text(args: Dict[str, Any]) -> ToolResult:
    text = args.get("text")
    if text is None:
        raise ToolError("Texto obrigatorio.")
    interval = float(args.get("interval") or 0.0)
    pyautogui = _require_pyautogui()
    pyautogui.write(str(text), interval=interval)
    return ToolResult(ok=True, output="Texto digitado.")


def hotkey(args: Dict[str, Any]) -> ToolResult:
    keys = args.get("keys")
    if not keys:
        raise ToolError("Lista de teclas obrigatoria.")
    if isinstance(keys, str):
        keys = [item.strip() for item in keys.split("+") if item.strip()]
    if not isinstance(keys, list):
        raise ToolError("Formato invalido para teclas.")
    pyautogui = _require_pyautogui()
    pyautogui.hotkey(*keys)
    return ToolResult(ok=True, output=f"Atalho executado: {'+'.join(keys)}")


def click(args: Dict[str, Any]) -> ToolResult:
    x = args.get("x")
    y = args.get("y")
    if x is None or y is None:
        raise ToolError("Coordenadas x e y obrigatorias.")
    button = args.get("button", "left")
    clicks = int(args.get("clicks") or 1)
    pyautogui = _require_pyautogui()
    pyautogui.click(x=int(x), y=int(y), button=button, clicks=clicks)
    return ToolResult(ok=True, output=f"Clique executado em ({x}, {y}).")


def capture_screen(args: Dict[str, Any]) -> ToolResult:
    output_dir = Path(args.get("output_dir") or "data/screens")
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = args.get("filename")
    if not filename:
        filename = f"screen_{int(time.time())}.png"
    path = output_dir / filename

    mss = _require_mss()
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        shot = sct.grab(monitor)
        mss.tools.to_png(shot.rgb, shot.size, output=str(path))

    return ToolResult(ok=True, output=str(path), metadata={"path": str(path)})


def default_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            name="open_url",
            description="Abre uma URL no navegador padrao.",
            args_schema={"url": "string"},
            handler=open_url,
        ),
        ToolSpec(
            name="type_text",
            description="Digita texto na janela ativa.",
            args_schema={"text": "string", "interval": "float (opcional)"},
            handler=type_text,
        ),
        ToolSpec(
            name="hotkey",
            description="Executa um atalho de teclado (ex: ['ctrl', 'l']).",
            args_schema={"keys": "lista de teclas ou string 'ctrl+l'"},
            handler=hotkey,
        ),
        ToolSpec(
            name="click",
            description="Clique em coordenadas absolutas.",
            args_schema={"x": "int", "y": "int", "button": "left/right", "clicks": "int"},
            handler=click,
        ),
        ToolSpec(
            name="capture_screen",
            description="Captura a tela inteira e salva PNG.",
            args_schema={"output_dir": "string (opcional)", "filename": "string (opcional)"},
            handler=capture_screen,
        ),
    ]
