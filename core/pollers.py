import asyncio
import queue
from typing import Awaitable, Callable
from dataclasses import dataclass

from core.constants import FRAME_SEC
from core.gamepad import GamepadReader, GamepadPressedButtons

#  SECTION:=============================================================
#            Logger
#  =====================================================================
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


#  =====================================================================
#            Data
#  =====================================================================


@dataclass
class GamepadHoldedButtons(GamepadPressedButtons):
    hold_frame: int


#  =====================================================================
#            Helpers
#  =====================================================================


def copy_pressed_buttons(orig: GamepadPressedButtons) -> GamepadPressedButtons:
    return GamepadPressedButtons(dirs=orig.dirs.copy(), btns=orig.btns.copy())


def make_holded_buttons(
    holded_buttons: GamepadPressedButtons, hold_frame: int
) -> GamepadHoldedButtons:
    return GamepadHoldedButtons(
        dirs=holded_buttons.dirs.copy(),
        btns=holded_buttons.btns.copy(),
        hold_frame=hold_frame,
    )


async def send_holded_buttons_async(
    queue: asyncio.Queue, holded_buttons: GamepadHoldedButtons
):
    """sends holded buttons by asyncio.Queue. For FastAPI or something. assign to GamepadReader by using lambda.

    Usage:
        GamepadPoller(..., _hold_button_sender = lambda btns:send_holded_buttons_async(queue, btns)
    """
    await queue.put(holded_buttons)


async def send_holded_buttons_sync(
    queue: queue.Queue, holded_buttons: GamepadHoldedButtons
):
    """sends holded buttons by queue.Queue. For GUI app. assign to GamepadReader by using lambda.

    Usage:
        GamepadPoller(..., _hold_button_sender = lambda btns:send_holded_buttons_sync(queue, btns)
    """
    queue.put(holded_buttons)


#  =====================================================================
#            Classes
#  =====================================================================


class GamepadPoller:
    def __init__(
        self,
        gamepad: GamepadReader,
        hold_button_sender: Callable[[GamepadHoldedButtons], Awaitable[None]],
    ):
        self.gamepad = gamepad
        self.curr_pressed_buttons = gamepad.pressed_buttons
        self.prev_pressed_buttons = GamepadPressedButtons(dirs=set(), btns=set())

        self._hold_buttons_sender = hold_button_sender

    def _pressed_buttons_updated(self) -> bool:
        return self.curr_pressed_buttons != self.prev_pressed_buttons

    async def run(self):
        """starts loop where gamepad state is checked at 1/60 sec interval. if updated,
        the state and hold frame is sent to on_frame function.
        """
        logger.debug("poller.run() starts.")

        # initialize
        self.prev_pressed_buttons = copy_pressed_buttons(self.curr_pressed_buttons)

        next_tick = asyncio.get_event_loop().time()
        hold_frame: int = 1
        # to save state temporaly
        temp_prev_pressed_buttons: GamepadPressedButtons

        try:
            # start 1F(1/60 second) loop. The 1F is not very accurate, maybe.
            while True:
                # wait until
                next_tick += FRAME_SEC
                sleep = next_tick - asyncio.get_event_loop().time()
                if sleep > 0:
                    # sleep to make the loop is 1F
                    await asyncio.sleep(sleep)

                if self._pressed_buttons_updated():
                    # store current pressed button instantly.
                    temp_prev_pressed_buttons = copy_pressed_buttons(
                        self.curr_pressed_buttons
                    )

                    # send holded buttons that has pressed buttons and their hold frame to on_update
                    holded_buttons = make_holded_buttons(
                        self.prev_pressed_buttons, hold_frame
                    )

                    # send holded button to on_update assigned at class construction.
                    await self._hold_buttons_sender(holded_buttons)

                    # update prev_pressed_buttons with stored curr_pressed_button above and reset hold_frame
                    self.prev_pressed_buttons = temp_prev_pressed_buttons
                    hold_frame = 1
                else:
                    # increment hold_frame
                    hold_frame += 1
        except asyncio.CancelledError:
            logger.debug("GamepadPoller run() is cancelled.")
            raise


# async def poll_loop(
#     state: ControllerState,
#     on_update: Callable,
#     on_frame: Callable,
#     filelog: InputLogger | None = None,
#     enable_liveline: bool = False,
# ):
#     """
#     on_update is a callback when conroller input state is change.
#     on_frame is a callback called every frame.
#     """
#     prev_dirs: set[str] = set()
#     prev_btns: set[str] = set()
#     cur_dirs: set[str] = set()
#     cur_btns: set[str] = set()
#     hold = 0
#     next_tick = asyncio.get_event_loop().time()
#
#     logger.debug("poll_loop starts")
#
#     try:
#         while True:
#             next_tick += FRAME_SEC
#             sleep = next_tick - asyncio.get_event_loop().time()
#             if sleep > 0:
#                 await asyncio.sleep(sleep)
#
#             # elements for display. output is like: hold cur_dirs cur_btns(not formatted)
#             hold += 1
#             cur_dirs = set(state.dirs)
#             cur_btns = set(state.btns)
#
#             # if input is changed:
#             if cur_dirs != prev_dirs or cur_btns != prev_btns:
#                 # send previous input elements to on_update()
#                 on_update(hold - 1, prev_dirs, prev_btns)
#
#                 # file log
#                 if filelog:
#                     line = format_line(hold, prev_dirs, prev_btns)
#                     filelog.write(line)
#
#                 # update input elements
#                 hold = 1
#                 prev_dirs = cur_dirs
#                 prev_btns = cur_btns
#
#             # send current input elements to on_update()
#             if enable_liveline:
#                 on_frame(hold, cur_dirs, cur_btns)
#     except asyncio.CancelledError:
#         logger.debug("polling is cancelled.")
#         raise
#     finally:
#         # force live input to prevoius input
#         # If no on_update() here, live input just before task is cancelled is not logged.
#         if filelog:
#             line = format_line(hold, cur_dirs, cur_btns)
#             filelog.write(line)


async def main():
    #  =====================================================================
    #            Main Logger
    #  =====================================================================
    import logging
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    gamepad = GamepadReader.from_device_name("Microsoft")
    queue = asyncio.Queue()
    # poller = GamepadPoller(
    #     gamepad, lambda x: send_holded_buttons_async(queue=queue, holded_buttons=x)
    # )
    poller = GamepadPoller(gamepad, lambda x: send_holded_buttons_async(queue, x))

    async def read_queue():
        while True:
            btns = await queue.get()
            print(btns)

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(gamepad.async_read_buttons())
            tg.create_task(poller.run())
            tg.create_task(read_queue())
    except* asyncio.CancelledError:
        logger.error("cancellederror")
        raise asyncio.CancelledError


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("exit.")
