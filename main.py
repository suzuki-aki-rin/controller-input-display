import asyncio
import logging


from core.config_loader import AppConfig, GuiConfig
# from core.runner import run

# outputters
from outputters.terminal import TerminalOutputter

# from outputters.gui_dearpygui import GUIOutputter
from outputters.server import app as app_for_browser
import uvicorn


#  SECTION:=============================================================
#            Main
#  =====================================================================
def main():
    #  -------- Load app config -------------------------------------------------------------
    app_config: AppConfig = AppConfig()

    if app_config.write_default_config:
        AppConfig.save_defaults_toml()
        raise SystemExit("default config file is created")

    #  -------- logger ------------------------------------------------------------------

    log_level = app_config.log_level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s", log_level)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)s | %(name)10.10s | %(funcName)10.10s | l:%(lineno)3.3s | %(message)-s",
    )
    logger = logging.getLogger(__name__)

    #  -------- Entry point ----------------------------------------------------------------
    #  use for uvicorn of browser outputter or something else for the futrue.
    if app_config.outputter == "terminal" or not app_config.outputter:
        logger.debug("terminal outputter starts")
        terminal_outputter = TerminalOutputter(
            device_name=app_config.device_name,
            history_size=app_config.history_size,
        )
        # on_update = terminal_outputter.on_update
        # on_frame = terminal_outputter.on_frame
        terminal_outputter.reserve_display()
        try:
            asyncio.run(terminal_outputter.run())
        except KeyboardInterrupt:
            logger.info("app exited by KeyboardInterrupt")
            raise SystemExit

    elif app_config.outputter == "browser":
        browser_config = app_config.outputters.browser

        app_for_browser.state.host = browser_config.host
        app_for_browser.state.port = browser_config.port
        app_for_browser.state.device = app_config.device_name
        app_for_browser.state.history_size = app_config.history_size
        app_for_browser.state.inputlog_path = app_config.inputlog_path

        if __name__ == "__main__":
            uvicorn.run(
                app_for_browser,
                host=browser_config.host,
                port=browser_config.port,
                reload=False,
                timeout_graceful_shutdown=2,
            )
        logger.info("browser outputter stopped or did not start.")
        return

    elif app_config.outputter == "gui":
        pass
    #     gui_config: GuiConfig = app_config.outputters.gui
    #     gui = GUIOutputter(
    #         device_name=app_config.device_name,
    #         history_size=app_config.history_size,
    #         config=gui_config,
    #     )
    #     gui.start(app_config.inputlog_path)
    #     return
    else:
        logger.error("bad outputter. exit")
        raise SystemExit

    # try:
    #     asyncio.run(
    #         run(
    #             device_name=app_config.device_name,
    #             on_frame=on_frame,
    #             on_update=on_update,
    #             enable_liveline=app_config.enable_liveline,
    #             logfile=app_config.inputlog_path,
    #         )
    #     )
    # except KeyboardInterrupt:
    #     logger.info("app is stopped by KeyboardInterrupt")


if __name__ == "__main__":
    main()
