import asyncio
import json

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from core.gamepad import GamepadReader
from core.gamepad_manager import GamepadManager
from core.pollers import GamepadPoller, GamepadHoldedButtons, send_holded_buttons_async
from core.inputlog_saver import InputLogSaver
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


def get_gamepad_manager(num: int) -> GamepadManager:
    if num == 1:
        return app.state.pad1_mgr
    if num == 2:
        return app.state.pad2_mgr
    else:
        raise ValueError("bad number: %s. use 1 or 2" % num)


def get_queue(num: int) -> asyncio.Queue:
    if num == 1:
        return app.state.queue
    if num == 2:
        return app.state.queue_2p
    else:
        raise ValueError("bad number: %s. use 1 or 2" % num)


# custom exception to cancel taskgroup
class MyWebSocketDisconnected(Exception):
    pass


#  =====================================================================
#            Variables
#  =====================================================================


# Queue where update events are put; WebSockets will watch it
queue = asyncio.Queue()
queue_2p = asyncio.Queue()
pressed_buttons = GamepadHoldedButtons(dirs=set(), btns=set(), hold_frame=0)
templates = Jinja2Templates(directory="outputters/templates")
inputlog_saver: InputLogSaver | None = None

#  =====================================================================
#            FastAPI, lifespan and instanciation
#  =====================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.state = pressed_buttons
    app.state.queue = queue
    app.state.queue_2p = queue_2p
    app.state.active_websockets = []  # ✅ track connected websockets

    # gamepad = GamepadReader.from_device_name(app.state.device)
    # poller = GamepadPoller(kgamepad, lambda x: send_holded_buttons_async(queue, x))
    pad1_gp_mgr = GamepadManager(app.state.device, queue)
    app.state.pad1_mgr = pad1_gp_mgr
    if app.state.device2:
        pad2_gp_mgr = GamepadManager(app.state.device2, queue_2p)
        app.state.pad2_mgr = pad2_gp_mgr

    # task = asyncio.create_task(gp_1p_manager.start())
    # task = asyncio.create_task(poller.run_with_reader())
    # task_1 = asyncio.create_task(gamepad.async_read_buttons())
    # task_2 = asyncio.create_task(poller.run())

    # try:
    yield
    # finally:  # ✅ finally always runs, even if cancelled
    logger.debug("lifespan finally block")
    # task.cancel()
    # task_1.cancel()
    # task_2.cancel()
    logger.debug("cleanup done")


app = FastAPI(lifespan=lifespan)

#  =====================================================================
#            Endpoints
#  =====================================================================


@app.get("/")
async def index():
    return RedirectResponse(url="/pad1")


@app.get("/pad{num}")
async def pad(request: Request, num: int):
    if num not in (1, 2):
        return f"bad pad number: {num}. input 1 or 2"
    # Send main loop variables, history_size and server url(changed to ws_url) to html template
    ws_url = str(request.base_url).replace("http", "ws", 1) + "ws/pad" + str(num)
    # ws_url = f"http://{app.state.host}:{app.state.port}/ws"
    logger.debug(ws_url)
    history_size = app.state.history_size

    gp_mgr = get_gamepad_manager(num)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "ws_url": ws_url,
            "history_size": history_size,
            "pad": "pad" + str(num),
            "dev_name": gp_mgr.device_name,
        },
    )


@app.post("/pad{num}/{button}")
async def start_pressed(num: int, button: str):
    gp_mgr = get_gamepad_manager(num)
    logger.debug(gp_mgr.device_name)

    if button == "stop":
        await gp_mgr.stop()
    elif button == "start":
        await gp_mgr.start()
    else:
        return {"message": "bad button"}


#  =====================================================================
#            websocket endpoint
#  =====================================================================


@app.websocket("/ws/pad{num}")
async def pad_ws(websocket: WebSocket, num: int):
    #  -------- task functions -----------------------------------------------------------

    async def wait_for_disconnect():
        # Save input history when websocket is disconnected
        while True:
            msg = await websocket.receive()
            if msg["type"] == "websocket.disconnect":
                logger.debug("websocket disconnected")
                if inputlog_saver:
                    inputlog_saver.save_to_file()
                    logger.info("input history is saved: %s", inputlog_saver.file_path)
            break
        raise MyWebSocketDisconnected

    async def get_queue_and_send_to_ws():
        _queue = get_queue(num)
        try:
            while True:
                holded_buttons = await _queue.get()

                # send gamepad state(running, cable connected) to browser
                if isinstance(holded_buttons, dict):
                    await websocket.send_text(json.dumps(holded_buttons))
                    continue

                # format GamepadHoldedButtons object into dict
                holded_buttons_dict = format_payload(holded_buttons)

                # send holded buttons state to browser
                await websocket.send_text(json.dumps(holded_buttons_dict))
                # save logs
                if inputlog_saver:
                    inputlog_saver.input(holded_buttons)
                # logger.debug("input is sent to browser via websocket")
        except asyncio.CancelledError:
            logger.debug("get_queue_and_send_to_ws in websocket endpoint is canceled")
            raise

        # except RuntimeError:
        #     logger.error("Maybe too frequent input. RuntimeError")

    #  -------- main -------------------------------------------------------------------

    # input log saver
    inputlog_saver = (
        InputLogSaver(app.state.inputlog_path) if app.state.inputlog_path else None
    )

    await websocket.accept()
    # app.state.active_websockets.append(websocket)  # ✅ register
    logger.debug("websocket is connected")

    gp_mgr = get_gamepad_manager(num)
    # nofify status before starts
    await gp_mgr.notify_status(
        is_running=gp_mgr.is_running, is_connected=gp_mgr.is_connected()
    )

    try:
        async with asyncio.TaskGroup() as tg:
            # when wait_for_disconnect ends, then raise MyWebSocketDisconnected
            tg.create_task(wait_for_disconnect())
            tg.create_task(get_queue_and_send_to_ws())

    except* MyWebSocketDisconnected:
        logger.debug("tasks in websocket are canceled")

    logger.debug("websocket closed")
