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
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def poll_loop(
    state: ControllerState, history: deque[str], log: InputLogger | None
):
    prev_dirs: set[str] = set()
    prev_btns: set[str] = set()
    hold = 0

    logger.debug("poll_loop starts")

    try:
        while True:
            await asyncio.sleep(FRAME_SEC)

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
    finally:
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
        logger.info("app is stopped.")


if __name__ == "__main__":
    main()

#
# def main():
#     # ------- ArgumentParser
#
#
#     # -------- Device detection
#
#     device = find_device(args.device_name)
#     if not device:
#         if args.device_name:
#             logger.error("argument device: %s not found.", args.device_name)
#         else:
#             logger.error("default device: %s not found.", DEFAULT_DEVICE_NAME)
#         return
#
#     logger.info("Logging: %s", device.name)
#     if args.logfile:
#         logger.info("Log file: %s", args.logfile)
#     logger.info("Format:  frames : direction  buttons")
#
#     #  ========== Device polling ========================================
#
#     # state is used to get controller state in the thread
#     state = ControllerState()
#     # Use to stop device.read_loop() in the thread
#     stop_event = threading.Event()
#
#     # Create thread to read device event
#     t = threading.Thread(
#         target=event_reader, args=(device, state, stop_event), daemon=True
#     )
#     t.start()
#
#     # Variables to save the controller state
#     prev_dirs: set[str] = set()
#     prev_btns: set[str] = set()
#
#     # to store holding frame
#     hold = 0
#     # For 1f(1/60 sec) tick
#     next_tick = time.perf_counter()
#
#     # to store input log
#     history: deque[str] = deque(maxlen=HISTORY_SIZE)
#     # file logger
#     log = InputLogger(args.logfile) if args.logfile else None
#
#     reserve_display()
#
#     # Read device state every frame(1/60 sec)
#     try:
#         while True:
#             next_tick += FRAME_SEC
#             sleep = next_tick - time.perf_counter()
#             if sleep > 0:
#                 time.sleep(sleep)
#
#             cur_dirs, cur_btns = state.snapshot()
#             hold += 1
#
#             if cur_dirs != prev_dirs or cur_btns != prev_btns:
#                 final_line = format_line(hold - 1, prev_dirs, prev_btns)
#                 if hold - 1 > 0:
#                     history.appendleft(final_line)
#                     if log:
#                         log.write(final_line)
#
#                 hold = 1
#                 prev_dirs = cur_dirs
#                 prev_btns = cur_btns
#
#             live_line = format_line(hold, cur_dirs, cur_btns)
#             redraw(live_line, history)
#
#     except KeyboardInterrupt:
#         logger.info("\nKeyboard interruption. Stopped.")
#     finally:
#         stop_event.set()
#         device.close()
#         logger.info("device is closed")
#         t.join()
#         if log:
#             log.close()
#
#
# if __name__ == "__main__":
#     main()
