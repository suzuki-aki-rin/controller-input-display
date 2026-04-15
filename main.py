import argparse
import asyncio

from core.runner import run
from config import LOG_LEVEL, DEFAULT_DEVICE_NAME

#  SECTION:=============================================================
#            Main Logger
#  =====================================================================
import logging

log_level = LOG_LEVEL if LOG_LEVEL else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


#  SECTION:=============================================================
#            Main
#  =====================================================================
def main():
    #  -------- ArgumentParser -------------------------------------------------------------

    parser = argparse.ArgumentParser(
        description="displays gamepad input history",
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
        help="device name. partial name is okay like Microsoft but case-sensitive. \
        To know device names see evtest or something. if none, default device name is used.",
        type=str,
        default=DEFAULT_DEVICE_NAME,
    )
    parser.add_argument(
        "--outputter",
        help="select outputter: terminal, browswer, gui. if none, terminal",
        type=str,
        default="terminal",
    )
    args = parser.parse_args()

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
