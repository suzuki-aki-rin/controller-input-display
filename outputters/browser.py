import asyncio
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from core.constants import NUMPAD, ARROW


app = FastAPI()
_queue: asyncio.Queue = asyncio.Queue()


def format_payload(hold: int, dirs: set[str], btns: set[str]) -> dict:
    numpad = NUMPAD.get(frozenset(dirs), "5")
    arrow = ARROW[numpad]
    return {
        "hold": hold,
        "arrow": arrow,
        "btns": sorted(btns),
    }


def make_browser_outputter():
    def on_update(hold: int, dirs: set[str], btns: set[str]):
        payload = format_payload(hold, dirs, btns)
        payload["type"] = "update"
        _queue.put_nowait(payload)

    def on_frame(hold: int, dirs: set[str], btns: set[str]):
        payload = format_payload(hold, dirs, btns)
        payload["type"] = "frame"
        _queue.put_nowait(payload)

    return on_update, on_frame


@app.get("/")
async def index():
    return FileResponse("outputters/index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            payload = await _queue.get()
            await websocket.send_text(json.dumps(payload))
    except WebSocketDisconnect:
        pass
