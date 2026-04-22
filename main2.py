from outputters.server import app
import uvicorn

#  =====================================================================
#            Main Logger
#  =====================================================================
import logging

logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,
        )
    except KeyboardInterrupt:
        logger.info("exit")
