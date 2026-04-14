import argparse
import asyncio

from core.runner import run


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
    parser.add_argument(
        "--outputter",
        help="select outputter: terminal, browswer",
        type=str,
        default="terminal",
    )
    args = parser.parse_args()

    #  -------- Entry point ----------------------------------------------------------------
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        logger.info("app is stopped by KeyboardInterrupt")


if __name__ == "__main__":
    main()
