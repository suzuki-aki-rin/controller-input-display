import queue
import asyncio
import threading
from collections import deque

import dearpygui.dearpygui as dpg

from core.constants import NUMPAD, ARROW, GUI_FONT
from core.runner import run
from config import HISTORY_SIZE


_queue: queue.Queue = queue.Queue()


def format_entry(hold: int, dirs: set[str], btns: set[str]) -> dict:
    numpad = NUMPAD.get(frozenset(dirs), "5")
    return {
        "hold": hold,
        "arrow": ARROW[numpad],
        "btns": sorted(btns),
    }


def make_gui_outputter():
    def on_update(hold: int, dirs: set[str], btns: set[str]):
        _queue.put({"type": "update", **format_entry(hold, dirs, btns)})

    def on_frame(hold: int, dirs: set[str], btns: set[str]):
        _queue.put({"type": "frame", **format_entry(hold, dirs, btns)})

    return on_update, on_frame


def gui_loop(args):
    history: deque[dict] = deque(maxlen=HISTORY_SIZE)

    dpg.create_context()

    with dpg.font_registry():
        with dpg.font(str(GUI_FONT), 32) as default_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            # add Unicode range that covers arrows (0x2190-0x21FF)
            dpg.add_font_range(0x2190, 0x21FF)

    dpg.bind_font(default_font)

    dpg.create_viewport(title="Input History", width=360, height=500)
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

        for i in range(HISTORY_SIZE):
            with dpg.group(horizontal=True, tag=f"hist_{i}"):
                dpg.add_text("    ", tag=f"hist_{i}_hold")
                dpg.add_text("   ", tag=f"hist_{i}_arrow")
                dpg.add_text("", tag=f"hist_{i}_btns")

    dpg.set_primary_window("main_window", True)
    dpg.show_viewport()

    on_update, on_frame = make_gui_outputter()

    def asyncio_thread():
        asyncio.run(run(args, on_frame=on_frame, on_update=on_update))

    t = threading.Thread(target=asyncio_thread, daemon=True)
    t.start()

    dpg.set_value("status", f"device: {args.device_name or 'xbox/microsoft'}")

    while dpg.is_dearpygui_running():
        while not _queue.empty():
            msg = _queue.get_nowait()

            if msg["type"] == "frame":
                dpg.set_value("live_hold", f"{msg['hold']:>4}")
                dpg.set_value("live_arrow", msg["arrow"])
                dpg.set_value("live_btns", " ".join(sorted(msg["btns"])))

            elif msg["type"] == "update":
                history.appendleft(msg)
                for i, entry in enumerate(history):
                    dpg.set_value(f"hist_{i}_hold", f"{entry['hold']:>4}")
                    dpg.set_value(f"hist_{i}_arrow", f"  {entry['arrow']}  ")
                    dpg.set_value(f"hist_{i}_btns", " ".join(entry["btns"]))
                for i in range(len(history), HISTORY_SIZE):
                    dpg.set_value(f"hist_{i}_hold", "    ")
                    dpg.set_value(f"hist_{i}_arrow", "   ")
                    dpg.set_value(f"hist_{i}_btns", "")

        dpg.render_dearpygui_frame()

    dpg.destroy_context()
