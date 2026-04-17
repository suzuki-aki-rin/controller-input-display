import argparse
import asyncio

from core.runner import run
from config import LOG_LEVEL, DEVICE_NAME, BROWSER_PORT, OUTPUTTER

import logging


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
        raise ValueError("In valid outputter. select from : %s" % str(outputters))

    #  -------- Entry point ----------------------------------------------------------------
    #
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
