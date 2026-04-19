import asyncio
import logging


from core.config_loader import Config, Gui
from core.runner import run

# outputters
from outputters.terminal import TerminalOutputter
from outputters.gui_dearpygui import GUIOutputter

from outputters.browser import make_browser_outputter
from outputters.browser import app as fastapi_app
import uvicorn


#  SECTION:=============================================================
#            Main
#  =====================================================================
def main():
    #  -------- Load app config -------------------------------------------------------------
    app_config: Config = Config()

    if app_config.write_default_config:
        Config.save_defaults_toml()
        raise SystemExit("default config file is created")

    #  -------- logger ------------------------------------------------------------------

    loglevel = app_config.log_level
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % loglevel)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    #  -------- Entry point ----------------------------------------------------------------
    #  use for uvicorn of browser outputter or something else for the futrue.
    extra_task = None
    if app_config.outputter == "terminal" or not app_config.outputter:
        terminal_outputter = TerminalOutputter(
            history_size=app_config.history_size,
            enable_liveline=app_config.enable_liveline,
        )
        on_update = terminal_outputter.on_update
        on_frame = terminal_outputter.on_frame
        terminal_outputter.reserve_display()
    elif app_config.outputter == "browser":
        on_update, on_frame = make_browser_outputter()
        # send history size to fastapi_app
        fastapi_app.state.history_size = app_config.history_size
        try:
            config = uvicorn.Config(
                fastapi_app,
                host=app_config.outputters.browser.host,
                port=app_config.outputters.browser.port,
                log_level=app_config.log_level,
            )
            server = uvicorn.Server(config)
            extra_task = server.serve
        except Exception:
            logger.exception("uvicorn is not loaded properly")
            raise SystemExit

    elif app_config.outputter == "gui":
        gui_config: Gui = app_config.outputters.gui
        gui = GUIOutputter(
            device_name=app_config.device_name,
            history_size=app_config.history_size,
            config=gui_config,
        )
        gui.start(app_config.inputlog_path)
        return
    else:
        logger.error("bad outputter. exit")
        raise SystemExit

    try:
        asyncio.run(
            run(
                device_name=app_config.device_name,
                on_frame=on_frame,
                on_update=on_update,
                enable_liveline=app_config.enable_liveline,
                logfile=app_config.inputlog_path,
                extra_task=extra_task,
            )
        )
    except KeyboardInterrupt:
        logger.info("app is stopped by KeyboardInterrupt")


if __name__ == "__main__":
    main()
