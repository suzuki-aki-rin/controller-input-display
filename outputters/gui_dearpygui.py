import queue
import asyncio
import threading
from collections import deque
from pathlib import Path


import dearpygui.dearpygui as dpg

from core.config_loader import GuiConfig
from core.constants import NUMPAD, ARROW
from core.runner import run


def format_entry(hold: int, dirs: set[str], btns: set[str]) -> dict:
    numpad = NUMPAD.get(frozenset(dirs), "5")
    return {
        "hold": hold,
        "arrow": ARROW[numpad],
        "btns": sorted(btns),
    }


class GUIOutputter:
    def __init__(self, device_name: str, history_size: int, config: GuiConfig) -> None:
        self.device_name = device_name
        self.history_size: int = history_size
        self.history: deque[dict] = deque(maxlen=self.history_size)
        self.config: GuiConfig = config

        # Use queue, thread-safe, for between threads: gui loop and run(event_reader and poll_loop)
        self._queue: queue.Queue = queue.Queue()

    def on_update(self, hold: int, dirs: set[str], btns: set[str]) -> None:
        self._queue.put({"type": "update", **format_entry(hold, dirs, btns)})

    def on_frame(self, hold: int, dirs: set[str], btns: set[str]) -> None:
        self._queue.put({"type": "frame", **format_entry(hold, dirs, btns)})

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

    def start(self, logfile: Path | None = None) -> None:
        """
        starts gui
        """

        self.create_window()

        #  -------- run event_reader() and poll_loop in another loop --------------------
        def asyncio_thread():
            asyncio.run(
                run(
                    device_name=self.device_name,
                    on_frame=self.on_frame,
                    on_update=self.on_update,
                    logfile=logfile,
                )
            )

        t = threading.Thread(target=asyncio_thread, daemon=True)
        t.start()

        # Change status label when the event_reader() and poll_loop starts to run
        dpg.set_value("status", f"{self.device_name}")

        #  -------- GUI loop ------------------------------------------------------------

        while dpg.is_dearpygui_running():
            while not self._queue.empty():
                msg = self._queue.get_nowait()

                if msg["type"] == "frame":
                    dpg.set_value("live_hold", f"{msg['hold']:>4}")
                    dpg.set_value("live_arrow", msg["arrow"])
                    dpg.set_value("live_btns", " ".join(sorted(msg["btns"])))

                elif msg["type"] == "update":
                    self.history.appendleft(msg)
                    for i, entry in enumerate(self.history):
                        dpg.set_value(f"hist_{i}_hold", f"{entry['hold']:>4}")
                        dpg.set_value(f"hist_{i}_arrow", f"  {entry['arrow']}  ")
                        dpg.set_value(f"hist_{i}_btns", " ".join(entry["btns"]))
                    for i in range(len(self.history), self.history_size):
                        dpg.set_value(f"hist_{i}_hold", "    ")
                        dpg.set_value(f"hist_{i}_arrow", "   ")
                        dpg.set_value(f"hist_{i}_btns", "")

            dpg.render_dearpygui_frame()

        dpg.destroy_context()
