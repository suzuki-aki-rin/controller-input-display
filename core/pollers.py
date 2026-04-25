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
    _queue: asyncio.Queue, holded_buttons: GamepadHoldedButtons
):
    """sends holded buttons by asyncio.Queue. For FastAPI or something. assign to GamepadReader by using lambda.

    Usage:
        GamepadPoller(..., _send_hold_button_to_queue = lambda btns:send_holded_buttons_async(queue, btns)
    """
    await _queue.put(holded_buttons)


async def send_holded_buttons_sync(
    _queue: queue.Queue, holded_buttons: GamepadHoldedButtons
):
    """sends holded buttons by queue.Queue. For GUI app. assign to GamepadReader by using lambda.

    Usage:
        GamepadPoller(..., _send_hold_button_to_queue = lambda btns:send_holded_buttons_sync(queue, btns)
    """
    _queue.put(holded_buttons)


#  =====================================================================
#            Classes
#  =====================================================================


class GamepadPoller:
    """Polls gamepad input per 1/60sec

    use send_holded_buttons_async or ..._sync for _send_hold_button_to_queue
    ex. GamepadPoller(..., _send_hold_button_to_queue = lambda btns:send_holded_buttons_sync(queue, btns)
    """

    def __init__(
        self,
        gamepad: GamepadReader,
        _send_hold_button_to_queue: Callable[[GamepadHoldedButtons], Awaitable[None]],
    ):
        self.gamepad = gamepad
        self.curr_pressed_buttons = gamepad.pressed_buttons
        self.prev_pressed_buttons = GamepadPressedButtons(dirs=set(), btns=set())
        self.hold_frame: int = 0

        self._hold_buttons_sender = _send_hold_button_to_queue

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
        self.hold_frame: int = 1
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
                        self.prev_pressed_buttons, self.hold_frame
                    )

                    # send holded button to on_update assigned at class construction.
                    await self._hold_buttons_sender(holded_buttons)

                    # update prev_pressed_buttons with stored curr_pressed_button above and reset hold_frame
                    self.prev_pressed_buttons = temp_prev_pressed_buttons
                    self.hold_frame = 1
                else:
                    # increment hold_frame
                    self.hold_frame += 1
        except asyncio.CancelledError:
            logger.debug("GamepadPoller run() is cancelled.")
            raise

    async def run_with_reader(self):
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.gamepad.async_read_buttons())
                tg.create_task(self.run())
        except* asyncio.CancelledError:
            logger.info("Reader and Poller are canelled")
            raise asyncio.CancelledError
        except* OSError:
            # send the last holded buttons
            holded_buttons = make_holded_buttons(
                self.prev_pressed_buttons, self.hold_frame
            )
            await self._hold_buttons_sender(holded_buttons)
            # And send emtpy holdedbutton as stop signal
            await self._hold_buttons_sender(
                GamepadHoldedButtons(dirs=set(), btns=set(), hold_frame=0)
            )
            logger.error("Reader and Poller ends: device disconnected")
            raise OSError


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
            # tg.create_task(gamepad.async_read_buttons())
            # tg.create_task(poller.run())
            tg.create_task(poller.run_with_reader())
            tg.create_task(read_queue())
    except* asyncio.CancelledError:
        logger.error("cancellederror")
        raise asyncio.CancelledError
    except* OSError:
        logger.error("disconnected")
        raise OSError


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt. exit.")
    except OSError:
        logging.info("Disconnected. exit.")
