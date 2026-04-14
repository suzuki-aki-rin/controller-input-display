import argparse
import asyncio
from collections import deque

from constants import FRAME_SEC, HISTORY_SIZE, DEFAULT_DEVICE_NAME
from device import find_device, event_reader, ControllerState
from display import format_line, reserve_display, redraw
from logger import InputLogger

#  SECTION:=============================================================
#            Main Logger
#  =====================================================================
import logging

logging.basicConfig(
    # level=logging.INFO,
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def poll_loop(
    state: ControllerState, history: deque[str], log: InputLogger | None
):
    prev_dirs: set[str] = set()
    prev_btns: set[str] = set()
    hold = 0
    next_tick = asyncio.get_event_loop().time()

    logger.debug("poll_loop starts")

    try:
        while True:
            next_tick += FRAME_SEC
            sleep = next_tick - asyncio.get_event_loop().time()
            if sleep > 0:
                await asyncio.sleep(sleep)

            cur_dirs = set(state.dirs)
            cur_btns = set(state.btns)
            hold += 1

            if cur_dirs != prev_dirs or cur_btns != prev_btns:
                final_line = format_line(hold - 1, prev_dirs, prev_btns)
                if hold - 1 > 0:
                    history.appendleft(final_line)
                    if log:
                        log.write(final_line)

                hold = 1
                prev_dirs = cur_dirs
                prev_btns = cur_btns

            live_line = format_line(hold, cur_dirs, cur_btns)
            redraw(live_line, history)
    except asyncio.CancelledError:
        logger.debug("polling is cancelled.")


async def run(args):
    #  ---------- Detect device ----------------------------------------

    device = find_device(args.device_name)
    if not device:
        if args.device_name:
            logger.error("argument device: %s not found.", args.device_name)
        else:
            logger.error("default device: %s not found.", DEFAULT_DEVICE_NAME)
        raise SystemExit()

    logger.info("Logging: %s", device.name)

    log = None
    if args.logfile:
        log = InputLogger(args.logfile)
        logger.info("Log file: %s", args.logfile)

    #  -------- Poll device and display input history ----------------------------------

    state = ControllerState()
    history: deque[str] = deque(maxlen=HISTORY_SIZE)

    logger.info("Format:  frames : direction  buttons")
    # diplay input history. the newest input is at the top line. oldest is the bottom.
    reserve_display()

    # loop = asyncio.get_running_loop()
    # stop = loop.create_future()
    # # signal.SIGINT is ^C input. Add signal handler for ^C and its callback stop.set_result
    # loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

    try:
        async with asyncio.TaskGroup() as tg:
            # event_reader catches controller events
            tg.create_task(event_reader(device, state))
            # poll_loop read controller state per frame (1/60sec)
            tg.create_task(poll_loop(state, history, log))
    except* asyncio.CancelledError:
        # except* expands ExceptionGroup
        # ExceptionGroup happens, then all group tasks are cancelled
        # this raise asyncio.exceptions.CancelledError causes KeyboardInterrupt that asyncio.run() raises.
        # without this except*, it also causes KeyboardInterrupt that asyncio.run() raises.

        # logger.debug("task group(event_reader, poll_loop) is cancelled")
        raise asyncio.CancelledError
    finally:
        logger.debug("task group(event_reader, poll_loop) is cancelled or finished")
        if log:
            log.close()


#  SECTION:=============================================================
#            Main
#  =====================================================================
def main():
    #  -------- ArgumentParser -------------------------------------------------------------

    parser = argparse.ArgumentParser(prog="PROG", usage="%(prog)s [options]")
    parser.add_argument(
        "--logfile",
        help="logfile name. if none, logfile is not created.",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--device-name",
        help="device name. see evtest or something. if none, default device name is used.",
        type=str,
        default=None,
    )
    args = parser.parse_args()

    #  -------- Entry point ----------------------------------------------------------------
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        logger.info("app is stopped by KeyboardInterrupt")


if __name__ == "__main__":
    main()
