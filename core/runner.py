import asyncio
from typing import Callable

from core.poll_loop import poll_loop
from core.device import find_device, event_reader, ControllerState

from input_logger import InputLogger

#  SECTION:=============================================================
#            Logger
#  =====================================================================
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


async def run(
    args, on_update: Callable | None = None, on_frame: Callable | None = None
):
    #  -------- Set file logger if commnadline argument exist. -------------------------

    filelogger = None
    if args.logfile:
        try:
            filelogger = InputLogger(args.logfile)
        except Exception:
            logger.exception("Bad logfile is specified.")
            raise SystemExit

        logger.info("Log file: %s", args.logfile)

    #  ---------- Detect device ----------------------------------------

    device = find_device(args.device_name)
    if not device:
        if args.device_name:
            logger.error("argument device: %s not found.", args.device_name)
        raise SystemExit()

    logger.info("Logging: %s", device.name)

    #  -------- Poll device and display input history ----------------------------------
    state = ControllerState()

    # Select outputter and asign on_update and on_frame to display input history
    match args.outputter:
        case "terminal" | None:
            from outputters.terminal import make_terminal_outputter, reserve_display

            on_update, on_frame = make_terminal_outputter()
            reserve_display()
        case "browser":
            from outputters.browser import app as fastapi_app, make_browser_outputter
            import uvicorn

            on_update, on_frame = make_browser_outputter()

        case "gui":
            logger.info("gui is going to start")
        case _:
            logger.error("outputter: %s not found", args.outputter)
            raise SystemExit

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
            if args.outputter == "browser":
                # send history size to fastapi_app
                fastapi_app.state.history_size = args.history_size
                try:
                    config = uvicorn.Config(
                        fastapi_app,
                        host=args.host,
                        port=args.port,
                        log_level=args.loglevel,
                    )
                    server = uvicorn.Server(config)
                except Exception:
                    logger.exception("uvicorn is not loaded properly")
                    raise SystemExit
                tg.create_task(server.serve())
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
