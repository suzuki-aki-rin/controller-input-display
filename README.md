# controller-input-display

show controller input history.
Three outputters: terminal, web browser and gui(dear pygui)

## Environment

Ubuntu 25.10, Kernerl 6.17.0
Python 3.13.7
libraries: see requirements.txt

## Dependencies

pip install evdev pydantic rtoml

1. outputter: browser
pip install uvicorn websockets jinja2
1. outputter: gui
pip install dearpygui

## Usage

```bash
$python main.py --help
usage: main.py [-h] [--log_level str] [--device_name str]
               [--outputter {terminal,browser,gui}] [--history_size int]
               [--enable_liveline bool] [--inputlog_path Path]
               [--write_default_config bool]

Displays pad input history. three outputters are available.
Settings except for the commandline options is written in config.toml.
If no config.toml, create defaults.toml via --write_default_config=True option
and modfiy it.

gui font_path in defaults.toml is possibly not valid. Is so, modify it in config.toml.
check device name by using evtest or something.

options:
  -h, --help            show this help message and exit
  --log_level str       (default: info)
  --device_name str     (default: Microsoft X-Box 360 pad)
  --outputter {terminal,browser,gui}
                        (default: terminal)
  --history_size int    (default: 30)
  --inputlog_path Path  (default: None)
  --write_default_config bool
                        if True(true in toml), outputs default_config.toml and
                        app ends. (default: False)

```

```bash
# if needed
python -m venv venv
source venv/bin/activate
# install libraries.
pip install -r requirements.txt
# Or install only libraries needed. For example, "browser" outputter.
# pip install evdev uvicorn websockets

# Run
python main.py
# Exit by ctrl-c.

# Run gui
python main.py --outputter=gui
# Exit by the gui window close

# Specify game pad 
# Default device name is written in config.py
# If target device is "Microsoft X-Box 360 pad"
python main.py --device-name=X-Box # Valid
python main.py --device-name="X-Box pad" # Invalid

# Configuration.
# Create defaults.toml
python main.py --write_default_config=True
# Edit defaults.toml and save it as config.toml
vim defaults.toml
```
