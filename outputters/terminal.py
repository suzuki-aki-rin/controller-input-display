import asyncio
from collections import deque
from pathlib import Path

from core.constants import NUMPAD, ARROW
from core.gamepad import GamepadReader
from core.pollers import GamepadPoller, send_holded_buttons_async, GamepadHoldedButtons
from core.inputlog_saver import InputLogSaver


#  =====================================================================
#            Logger
#  =====================================================================
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def format_line(pressed_btns: GamepadHoldedButtons) -> str:
    numpad = NUMPAD.get(frozenset(pressed_btns.dirs), "5")
    arrow = ARROW[numpad]
    btns_str = "+".join(sorted(pressed_btns.btns)) if pressed_btns.btns else ""
    return f"{pressed_btns.hold_frame:>4} : {arrow}  {btns_str}".rstrip()


class TerminalOutputter:
    """
    Outputs input history to terminal
    """

    def __init__(
        self, device_name: str, history_size: int, inputlog_path: Path | None = None
    ) -> None:
        self.device_name = device_name
        self.history_size = history_size
        self.inputlog_path = inputlog_path
        self.history: deque[str] = deque(maxlen=self.history_size)
        # self.enable_liveline = enable_liveline

    def reserve_display(self) -> None:
        """Print blank lines once at startup to reserve the display block."""
        for _ in range(self.history_size + 1):
            print()

    def redraw(self) -> None:
        print(f"\033[{self.history_size + 1}A", end="")
        print("\rinput history")
        for line in self.history:
            print(f"\r{line:<20}")
        blank_count = self.history_size - len(self.history)
        for _ in range(blank_count):
            print(f"\r{'':<20}")

    async def run(self) -> None:
        logger.debug("terminal outputter starts")
        queue: asyncio.Queue[GamepadHoldedButtons] = asyncio.Queue()
        gamepad = GamepadReader.from_device_name(self.device_name)
        poller = GamepadPoller(gamepad, lambda x: send_holded_buttons_async(queue, x))
        inputlog_saver = (
            InputLogSaver(self.inputlog_path) if self.inputlog_path else None
        )

        # Before input display, fill display space with blank lines
        self.reserve_display()

        async def read_and_draw() -> None:
            try:
                while True:
                    pressed_buttons: GamepadHoldedButtons = await queue.get()
                    line = format_line(pressed_buttons)
                    self.history.appendleft(line)
                    if inputlog_saver:
                        inputlog_saver.input(pressed_buttons)
                    self.redraw()
            except asyncio.CancelledError:
                logger.info("terminal output is cancelled")
                raise

        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(gamepad.async_read_buttons())
                tg.create_task(poller.run())
                tg.create_task(read_and_draw())
        except* asyncio.CancelledError:
            logger.info("tasks are cancelled")
            raise asyncio.CancelledError
        except* OSError:
            logger.error("Device is disconnected")
            raise OSError
        finally:
            # save input history to file when terminal outputter is cancelled
            if inputlog_saver:
                inputlog_saver.save_to_file()
