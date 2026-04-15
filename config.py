from pathlib import Path

#  SECTION:=============================================================
#            Logger
#  =====================================================================
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


#  -------- User config ----------------------------------------------------------------

LOG_LEVEL = logging.INFO

DEFAULT_DEVICE_NAME = "Microsoft X-Box 360 pad"
HISTORY_SIZE = 30


GUI_FONT = Path("~/.local/share/fonts/Cica_v5.0.3/Cica-Bold.ttf").expanduser()
if not GUI_FONT.exists():
    logger.error("font:GUI_FONT does not exists")
GUI_FONT_SIZE = 32
GUI_WIDTH = 300
GUI_HEIGHT = 1200
