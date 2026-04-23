import asyncio
import threading
from collections import deque
from queue import Queue
from pathlib import Path


import dearpygui.dearpygui as dpg

from core.config_loader import GuiConfig

from core.gamepad import GamepadReader
from core.pollers import GamepadPoller, GamepadHoldedButtons, send_holded_buttons_sync
from core.inputlog_saver import InputLogSaver

from core.common import FormattedHoldedButtons, format_holded_buttons

#  =====================================================================
#            Logger
#  =====================================================================
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class GUIOutputter:
    def __init__(
        self,
        device_name: str,
        history_size: int,
        config: GuiConfig,
        inputlog_path: Path | None = None,
    ) -> None:
        self.device_name = device_name
        self.history_size: int = history_size
        self.history: deque[FormattedHoldedButtons] = deque(maxlen=self.history_size)
        self.config: GuiConfig = config
        self.inputlog_path = inputlog_path
        self._queue: Queue[GamepadHoldedButtons] = Queue()

        # Use queue, thread-safe, for between threads: gui loop and run(event_reader and poll_loop)

    async def send_device_input_to_queue(self):
        gamepad = GamepadReader.from_device_name(self.device_name)
        poller = GamepadPoller(
            gamepad, lambda x: send_holded_buttons_sync(self._queue, x)
        )

        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(gamepad.async_read_buttons())
                tg.create_task(poller.run())
        except* asyncio.CancelledError:
            logger.info("tasks are cancelled")
            raise asyncio.CancelledError

    def read_and_draw(self, inputlog_saver: InputLogSaver | None = None) -> None:
        if not self._queue.empty():
            # get holded buttons from _queue
            holded_buttons: GamepadHoldedButtons = self._queue.get_nowait()

            f_holded_buttons = format_holded_buttons(holded_buttons)

            # store formatted holded buttons.
            self.history.appendleft(f_holded_buttons)
            # update all lines with updated self.history
            for i, entry in enumerate(self.history):
                dpg.set_value(f"hist_{i}_hold", f"{entry.hold_frame:>4}")
                dpg.set_value(f"hist_{i}_arrow", f" {entry.arrow} ")
                dpg.set_value(f"hist_{i}_btns", f"{entry.btns}")
            for i in range(len(self.history), self.history_size):
                dpg.set_value(f"hist_{i}_hold", "    ")
                dpg.set_value(f"hist_{i}_arrow", "   ")
                dpg.set_value(f"hist_{i}_btns", "")
            if inputlog_saver:
                inputlog_saver.input(holded_buttons)

    def create_window(self) -> None:
        dpg.create_context()

        with dpg.font_registry():
            with dpg.font(
                str(self.config.font_path), self.config.font_size
            ) as default_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                # add Unicode range that covers arrows (0x2190-0x21FF)
                dpg.add_font_range(0x2190, 0x21FF)

        dpg.bind_font(default_font)

        dpg.create_viewport(
            title="Input History", width=self.config.width, height=self.config.height
        )
        # add font before setup

        dpg.setup_dearpygui()

        with dpg.window(label="Input History", tag="main_window", no_close=True):
            dpg.add_text("connecting...", tag="status")
            dpg.add_separator()

            with dpg.group(horizontal=True, tag="live_group"):
                dpg.add_text("   0", tag="live_hold")
                dpg.add_text("·", tag="live_arrow")
                dpg.add_text("", tag="live_btns")

            dpg.add_separator()

            for i in range(self.history_size):
                with dpg.group(horizontal=True, tag=f"hist_{i}"):
                    dpg.add_text("    ", tag=f"hist_{i}_hold")
                    dpg.add_text("   ", tag=f"hist_{i}_arrow")
                    dpg.add_text("", tag=f"hist_{i}_btns")

        dpg.set_primary_window("main_window", True)
        dpg.show_viewport()

    def start(self) -> None:
        """
        starts gui
        """

        self.create_window()

        def async_thread() -> None:
            asyncio.run(self.send_device_input_to_queue())

        # loop in another thread: read device and send its input to queue. When GUI ends, this thread ends.
        t = threading.Thread(target=async_thread, daemon=True)
        t.start()

        # create inputlog saver, used in GUI loop
        inputlog_saver = (
            InputLogSaver(self.inputlog_path) if self.inputlog_path else None
        )

        # Change status label when the event_reader() and poll_loop starts to run
        dpg.set_value("status", f"{self.device_name}")

        #  -------- GUI loop ------------------------------------------------------------
        logger.debug("gui starts.")
        while dpg.is_dearpygui_running():
            self.read_and_draw(inputlog_saver=inputlog_saver)
            dpg.render_dearpygui_frame()

        # when gui ends, write inputlog to file
        if inputlog_saver:
            inputlog_saver.save_to_file()

        logger.debug("gui exited.")
        dpg.destroy_context()
