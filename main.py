import argparse
import asyncio
import logging
from pathlib import Path

from config import (
    HISTORY_SIZE,
    LOG_LEVEL,
    DEVICE_NAME,
    BROWSER_PORT,
    OUTPUTTER,
    LOGFILE_PATH,
)

from core.runner import run
from outputters.terminal import TerminalOutputter
from outputters.browser import make_browser_outputter

from outputters.browser import app as fastapi_app
import uvicorn


#  SECTION:=============================================================
#            Main
#  =====================================================================
def main():
    #  -------- ArgumentParser -------------------------------------------------------------

    parser = argparse.ArgumentParser(
        description="displays gamepad input history.\nModify config.py to change default values.",
        formatter_class=argparse.RawTextHelpFormatter,
        prog="python main.py",
        usage="%(prog)s [options]",
    )
    parser.add_argument(
        "--logfile",
        help="log file name. if none, log file is not created.",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--device-name",
        help="device name. partial name is okay like Microsoft but case-sensitive.\n\
To know device names see evtest or something.",
        type=str,
        default=DEVICE_NAME if DEVICE_NAME else "X-Box",
    )
    parser.add_argument(
        "--outputter",
        help="select outputter: terminal, browswer, gui. if none, terminal",
        type=str,
        default=OUTPUTTER if OUTPUTTER else "terminal",
    )
    parser.add_argument(
        "--loglevel",
        help="loglevel: set info, warning,debug or something",
        type=str,
        default=LOG_LEVEL if LOG_LEVEL else "info",
    )
    parser.add_argument(
        "--history-size",
        help="line number of input display",
        type=str,
        default=30,
    )
    parser.add_argument(
        "--host",
        help="host for browswer outputter.",
        type=str,
        default="0.0.0.0",
    )
    parser.add_argument(
        "--port",
        help="port for browser outputter.",
        type=str,
        default=8000,
    )
    args = parser.parse_args()

    #  -------- logger ------------------------------------------------------------------

    loglevel = args.loglevel
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % loglevel)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    #  -------- validate arguments ------------------------------------------------------
    outputters = ("terminal", "browser", "gui")
    if args.outputter not in outputters:
        raise ValueError("Invalid outputter. select from : %s" % str(outputters))

    logfile = args.logfile if args.logfile else LOGFILE_PATH

    if logfile and not Path(logfile).exists():
        raise FileExistsError("Invalid logfile path: %s" % str(logfile))

    logfile = Path(logfile) if logfile else None

    #  -------- Entry point ----------------------------------------------------------------

    if args.outputter == "terminal" or not args.outputter:
        terminal_outputter = TerminalOutputter(history_size=HISTORY_SIZE)
        on_update = terminal_outputter.on_update
        on_frame = terminal_outputter.on_frame
        terminal_outputter.reserve_display()
    elif args.output == "browser":
        on_update, on_frame = make_browser_outputter()
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
        asyncio.create_task(server.serve())

    asyncio.run(
        run(
            device_name=args.device_name,
            on_frame=on_frame,
            on_update=on_update,
            logfile=logfile,
        )
    )

    if args.outputter == "gui":
        from outputters.gui_dearpygui import gui_loop

        gui_loop(args)
    else:
        try:
            asyncio.run(run(args))
        except KeyboardInterrupt:
            logger.info("app is stopped by KeyboardInterrupt")


if __name__ == "__main__":
    main()
