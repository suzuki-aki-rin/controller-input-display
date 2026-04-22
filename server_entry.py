from outputters.server import app
import uvicorn

from core.config_loader import AppConfig

#  =====================================================================
#            Main Logger
#  =====================================================================
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app_config = AppConfig()

app.state.device = app_config.device_name
app.state.history_size = app_config.history_size

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        timeout_graceful_shutdown=1,
    )
