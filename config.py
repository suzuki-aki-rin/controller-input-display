from pathlib import Path

#  SECTION:=============================================================
#            Logger
#  =====================================================================
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


#  -------- User config ----------------------------------------------------------------
LOG_LEVEL = "info"

DEVICE_NAME = "Microsoft X-Box 360 pad"
HISTORY_SIZE = 30
OUTPUTTER = "terminal"
BROWSER_PORT = 8100
LOGFILE_PATH = ""
GUI_FONT = "NotoSerifCJKjp-Medium.otf"
# GUI_FONT = Path("~/.local/share/fonts/Cica_v5.0.3/Cica-Bold.ttf").expanduser()
# if not GUI_FONT.exists():
#     logger.error("font:GUI_FONT does not exists")
GUI_FONT_SIZE = 32
GUI_WIDTH = 300
GUI_HEIGHT = 1200
