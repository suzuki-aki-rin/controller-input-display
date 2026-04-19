from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
    CliSettingsSource,
)
from pydantic import BaseModel, Field, field_validator

from typing import Literal
from pathlib import Path
from datetime import datetime
import rtoml

#  =====================================================================
#            Logger
#  =====================================================================
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

#  =====================================================================
#             Helper
#  =====================================================================


def dict_to_toml_with_comments(data: dict, output_path: str) -> str:
    # 1. Serialize — rtoml renders None as the sentinel string
    toml_str = rtoml.dumps(data, none_value="@None")

    # 2. Comment out any line containing "@None"
    lines = toml_str.splitlines()
    commented = [f"# {line}" if "@None" in line else line for line in lines]

    result = "\n".join(commented)

    with open(output_path, "w") as f:
        f.write(result)

    return result


#  =====================================================================
#            Config class and classes the Config class has.
#  =====================================================================


class Terminal(BaseModel):
    """Config for terminal outputter"""

    pass


class Browser(BaseModel):
    """Config for browser outputter"""

    port: int = 8000
    host: str = "0.0.0.0"


class Gui(BaseModel):
    """Config for gui outputter"""

    font_path: Path = Field(
        default=Path("/usr/share/fonts/truetype/dejavu/dejavusansmono.ttf"),
        validate_default=True,
    )
    # font_path: Path = Path("/usr/share/fonts/truetype/dejavu/dejavusansmono.ttf")
    font_size: int = 32
    width: int = 300
    height: int = 1200

    @field_validator("font_path")
    @classmethod
    def must_exist(cls, v: Path):
        v = v.expanduser()
        if not v.exists():
            raise ValueError(f"path does not exist: {v}")
        return v


class Outputters(BaseModel):
    terminal: Terminal = Field(default_factory=Terminal)
    browser: Browser = Field(default_factory=Browser)
    gui: Gui = Field(default_factory=Gui)


class Config(BaseSettings):
    """display pad input history. three outputters are available."""

    log_level: str = "info"
    device_name: str = "Microsoft X-Box 360 pad"
    outputter: Literal["terminal", "browser", "gui"] = "terminal"
    history_size: int = 30
    liveline_output: bool = False
    inputlog_path: Path | None = None
    outputters: Outputters

    model_config = SettingsConfigDict(
        toml_file=["config.toml"],
        cli_parse_args=True,
        cli_avoid_json=True,
        cli_hide_none_type=True,
    )

    @field_validator("inputlog_path")
    @classmethod
    def resolve_with_timestamp(cls, v: Path):
        if v is None:
            return v
        v = v.expanduser()
        parent = v.parent

        if v.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            return v.parent / f"{v.stem}_{ts}{v.suffix}"
        if not parent.exists():
            raise ValueError(f"Directory '{parent}' does not exist")
        if not parent.is_dir():
            raise ValueError(f"'{parent}' is not a directory")
        return v

    # add sources of toml and cli
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            TomlConfigSettingsSource(settings_cls),
            CliSettingsSource(settings_cls, cli_parse_args=True),
        )

    @classmethod
    def save_defaults_toml(cls, filepath: str = "defaults.toml") -> None:
        json_dict = cls().model_dump(mode="json")
        dict_to_toml_with_comments(json_dict, filepath)


def main() -> None:
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        Config.save_defaults_toml()
        print(Config())
    except ValueError as e:
        logger.error(e)


if __name__ == "__main__":
    main()
