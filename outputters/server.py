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


app_config = AppConfig()
device_name = app_config.device_name
history_size = app_config.history_size

# Queue where update events are put; WebSockets will watch it
queue = asyncio.Queue()
pressed_buttons = GamepadHoldedButtons(dirs=set(), btns=set(), hold_frame=0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.history_size = history_size
    app.state.state = pressed_buttons
    app.state.queue = queue

    gamepad = GamepadReader.from_device_name(device_name)
    poller = GamepadPoller(gamepad, lambda x: send_holded_buttons_async(queue, x))

    task1 = asyncio.create_task(gamepad.async_read_buttons())
    task2 = asyncio.create_task(poller.run())
    # logger.error("cancellederror")
    # raise asyncio.CancelledError

    logger.debug("before yield")
    yield

    task1.cancel()
    task2.cancel()
    await asyncio.gather(task1, task2, return_exceptions=True)


templates = Jinja2Templates(directory="outputters/templates")
app = FastAPI(lifespan=lifespan)


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
            payload = format_payload(payload)
            logger.debug("server recieved new queue")
            await websocket.send_text(json.dumps(payload))
            logger.debug("input is sent to browser via websocket")
    except WebSocketDisconnect:
        logger.debug("websocket is disconnected")
    except asyncio.CancelledError:
        logger.debug("KeyboardInterrupt : websocket is disconnected")
        raise
    finally:
        await websocket.close()
        logger.debug("websocket is closed. websocket task is finished/canceled.")
