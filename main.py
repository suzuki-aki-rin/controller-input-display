import asyncio
import logging


from core.config_loader import AppConfig, GuiConfig, BrowserConfig
from core.runner import run

# outputters
from outputters.terminal import TerminalOutputter
from outputters.gui_dearpygui import GUIOutputter
from outputters.browser import BrowserOutputter, app as fastapi_app


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
        raise ValueError("Invalid log level: %s" % log_level)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    #  -------- Entry point ----------------------------------------------------------------
    #  use for uvicorn of browser outputter or something else for the futrue.
    if app_config.outputter == "terminal" or not app_config.outputter:
        terminal_outputter = TerminalOutputter(
            history_size=app_config.history_size,
            enable_liveline=app_config.enable_liveline,
        )
        on_update = terminal_outputter.on_update
        on_frame = terminal_outputter.on_frame
        terminal_outputter.reserve_display()

    elif app_config.outputter == "browser":
        browser_config: BrowserConfig = app_config.outputters.browser
        browser_outputter = BrowserOutputter(
            app=fastapi_app,
            history_size=app_config.history_size,
            device_name=app_config.device_name,
            config=browser_config,
            logfile=app_config.inputlog_path,
            log_level=app_config.log_level,
        )

        on_update = browser_outputter.on_update
        on_frame = browser_outputter.on_frame
        try:
            browser_outputter.start()
        except Exception:
            logger.exception("server is not loaded properly")
            raise SystemExit
        return

    elif app_config.outputter == "gui":
        gui_config: GuiConfig = app_config.outputters.gui
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
            )
        )
    except KeyboardInterrupt:
        logger.info("app is stopped by KeyboardInterrupt")


if __name__ == "__main__":
    main()
