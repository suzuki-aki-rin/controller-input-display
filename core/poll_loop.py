import asyncio
from typing import Callable

from input_logger import InputLogger
from outputters.terminal import format_line
from constants import FRAME_SEC
from core.device import ControllerState

#  SECTION:=============================================================
#            Logger
#  =====================================================================
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


async def poll_loop(
    state: ControllerState,
    on_update: Callable,
    on_frame: Callable,
    filelog: InputLogger | None,
):
    """
    on_update is a callback when conroller input state is change.
    on_frame is a callback called every frame.
    """
    prev_dirs: set[str] = set()
    prev_btns: set[str] = set()
    cur_dirs: set[str] = set()
    cur_btns: set[str] = set()
    hold = 0
    next_tick = asyncio.get_event_loop().time()

    logger.debug("poll_loop starts")

    try:
        while True:
            next_tick += FRAME_SEC
            sleep = next_tick - asyncio.get_event_loop().time()
            if sleep > 0:
                await asyncio.sleep(sleep)

            # elements for display. output is like: hold cur_dirs cur_btns(not formatted)
            hold += 1
            cur_dirs = set(state.dirs)
            cur_btns = set(state.btns)

            # if input is changed:
            if cur_dirs != prev_dirs or cur_btns != prev_btns:
                # send previous input elements to on_update()
                on_update(hold - 1, prev_dirs, prev_btns)

                # file log
                if filelog:
                    line = format_line(hold, prev_dirs, prev_btns)
                    filelog.write(line)

                # update input elements
                hold = 1
                prev_dirs = cur_dirs
                prev_btns = cur_btns

            # send current input elements to on_update()
            on_frame(hold, cur_dirs, cur_btns)
    except asyncio.CancelledError:
        logger.debug("polling is cancelled.")
    finally:
        # force live input to prevoius input
        # If no on_update() here, live input just before task is cancelled is not logged.
        if filelog:
            line = format_line(hold, cur_dirs, cur_btns)
            filelog.write(line)
