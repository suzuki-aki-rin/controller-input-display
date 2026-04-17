import asyncio
import json

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates

from core.constants import NUMPAD, ARROW

#  =====================================================================
#            Logger
#  =====================================================================
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


templates = Jinja2Templates(directory="outputters/templates")
app = FastAPI()

# for recieving and sending data
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
        logger.debug("Que is updated")

    def on_frame(hold: int, dirs: set[str], btns: set[str]):
        payload = format_payload(hold, dirs, btns)
        payload["type"] = "frame"
        _queue.put_nowait(payload)

    return on_update, on_frame


@app.get("/")
async def index(request: Request):
    # Send main loop variables, history_size and server url(changed to ws_url) to html template
    ws_url = str(request.base_url).replace("http", "ws", 1) + "ws"
    history_size = request.app.state.history_size

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"ws_url": ws_url, "history_size": history_size},
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.debug("websocket is connected")
    try:
        while True:
            payload = await _queue.get()
            logger.debug("server recieved new queue")
            await websocket.send_text(json.dumps(payload))
            logger.debug("input is sent to browser via websocket")
    except WebSocketDisconnect:
        logger.debug("websocket is disconnected")
