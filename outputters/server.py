import asyncio
import json

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates

from core.gamepad import GamepadReader
from core.pollers import GamepadPoller, GamepadHoldedButtons, send_holded_buttons_async

from core.config_loader import AppConfig
from core.constants import NUMPAD, ARROW

#  =====================================================================
#            Logger
#  =====================================================================
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


#  =====================================================================
#            Helpers
#  =====================================================================
def format_payload(pressed_buttons: GamepadHoldedButtons) -> dict:
    numpad = NUMPAD.get(frozenset(pressed_buttons.dirs), "5")
    arrow = ARROW[numpad]
    return {
        "type": "update",
        "hold": pressed_buttons.hold_frame,
        "arrow": arrow,
        "btns": sorted(pressed_buttons.btns),
    }


# Queue where update events are put; WebSockets will watch it
queue = asyncio.Queue()
pressed_buttons = GamepadHoldedButtons(dirs=set(), btns=set(), hold_frame=0)
templates = Jinja2Templates(directory="outputters/templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.state = pressed_buttons
    app.state.queue = queue
    app.state.active_websockets = []  # ✅ track connected websockets

    gamepad = GamepadReader.from_device_name(app.state.device)
    poller = GamepadPoller(gamepad, lambda x: send_holded_buttons_async(queue, x))

    task_1 = asyncio.create_task(gamepad.async_read_buttons())
    task_2 = asyncio.create_task(poller.run())

    try:
        yield
    finally:  # ✅ finally always runs, even if cancelled
        logger.debug("lifespan finally block")
        # await app.state.queue.put(None)
        for ws in app.state.active_websockets:
            await ws.close()
        task_1.cancel()
        task_2.cancel()
        logger.debug("cleanup done")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def index(request: Request):
    # Send main loop variables, history_size and server url(changed to ws_url) to html template
    ws_url = str(request.base_url).replace("http", "ws", 1) + "ws"
    history_size = app.state.history_size

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"ws_url": ws_url, "history_size": history_size},
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    app.state.active_websockets.append(websocket)  # ✅ register

    logger.debug("websocket is connected")
    try:
        while True:
            try:
                payload = await app.state.queue.get()
            except asyncio.CancelledError:
                logger.debug("queue.get cancelled")
                break  # ✅ break loop, don't re-raise here
            payload = format_payload(payload)
            logger.debug("server recieved new queue")
            await websocket.send_text(json.dumps(payload))
            logger.debug("input is sent to browser via websocket")
    except WebSocketDisconnect:
        logger.debug("websocket is disconnected")
    finally:
        # try:
        app.state.active_websockets.remove(websocket)
        await websocket.close()  # ✅ guard against already-closed
        # except Exception:
        #     pass
        logger.debug("websocket closed")
