import asyncio
from typing import Callable
from pathlib import Path

from core.poll_loop import poll_loop
from core.device import find_device, event_reader, ControllerState

from core.input_logger import InputLogger


#  SECTION:=============================================================
#            Logger
#  =====================================================================
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


async def run(
    device_name: str,
    on_update: Callable,
    on_frame: Callable,
    logfile: Path | None = None,
    extra_task: Callable | None = None,
):
    #  -------- Set file logger if inputlog_path is set. -------------------------

    filelogger = None
    if logfile:
        try:
            filelogger = InputLogger(logfile)
        except Exception as e:
            logger.exception("Bad logfile is specified. ", e)
            raise SystemExit

        logger.info("Log file: %s", logfile)

    #  ---------- Detect device ----------------------------------------

    device = find_device(device_name)
    if not device:
        if device_name:
            logger.error("argument device: %s not found.", device_name)
        raise SystemExit()

    logger.info("Logging: %s", device.name)

    #  -------- Poll device and display input history ----------------------------------
    state = ControllerState()

    try:
        async with asyncio.TaskGroup() as tg:
            # event_reader catches controller events
            tg.create_task(event_reader(device, state))
            # poll_loop read controller state per frame (1/60sec)
            tg.create_task(
                poll_loop(
                    state=state,
                    on_update=on_update,
                    on_frame=on_frame,
                    filelog=filelogger,
                )
            )
            if extra_task:
                tg.create_task(extra_task())
    except* asyncio.CancelledError:
        # except* expands ExceptionGroup
        # ExceptionGroup happens, then all group tasks are cancelled
        # this raise asyncio.exceptions.CancelledError causes KeyboardInterrupt that asyncio.run() raises.
        # without this except*, it also causes KeyboardInterrupt that asyncio.run() raises.
        # logger.debug("task group(event_reader, poll_loop) is cancelled")
        raise asyncio.CancelledError
    finally:
        logger.debug("task group(event_reader, poll_loop) is cancelled or finished")
        if filelogger:
            filelogger.close()
