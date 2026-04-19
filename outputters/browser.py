import asyncio
import json
from typing import Callable

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
import uvicorn

from core.constants import NUMPAD, ARROW
from core.config_loader import BrowserConfig

#  =====================================================================
#            Logger
#  =====================================================================
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


templates = Jinja2Templates(directory="outputters/templates")
app = FastAPI()


class BrowserOutputter:
    def __init__(
        self,
        app: FastAPI,
        history_size: int,
        config: BrowserConfig,
        log_level: str = "info",
    ) -> None:
        self.app = app
        # for recieving and sending data
        self.queue = asyncio.Queue()
        self.app.state.queue = self.queue
        self.app.state.history_size = history_size
        self.config = config
        self.log_level = log_level

    def format_payload(self, hold: int, dirs: set[str], btns: set[str]) -> dict:
        numpad = NUMPAD.get(frozenset(dirs), "5")
        arrow = ARROW[numpad]
        return {
            "hold": hold,
            "arrow": arrow,
            "btns": sorted(btns),
        }

    def make_on_update_and_on_frame(self) -> tuple[Callable, Callable]:
        def on_update(hold: int, dirs: set[str], btns: set[str]):
            payload = self.format_payload(hold, dirs, btns)
            payload["type"] = "update"
            self.queue.put_nowait(payload)
            logger.debug("Que is updated")

        def on_frame(hold: int, dirs: set[str], btns: set[str]):
            payload = self.format_payload(hold, dirs, btns)
            payload["type"] = "frame"
            self.queue.put_nowait(payload)

        return on_update, on_frame

    def create_server_task(self) -> Callable:
        config = uvicorn.Config(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level=self.log_level,
        )
        server = uvicorn.Server(config)
        return server.serve


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
            payload = await app.state.queue.get()
            logger.debug("server recieved new queue")
            await websocket.send_text(json.dumps(payload))
            logger.debug("input is sent to browser via websocket")
    except WebSocketDisconnect:
        logger.debug("websocket is disconnected")
    except KeyboardInterrupt:
        logger.debug("KeyboardInterrupt : websocket is disconnected")
        raise
