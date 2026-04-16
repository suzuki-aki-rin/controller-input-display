# controller-input-display

show controller input history.
Three outputters: terminal, web browser and gui(dear pygui)

## Environment

Ubuntu 25.10, Kernerl 6.17.0
Python 3.13.7
libraries: see requirements.txt

## Dependencies

pip install evdev

1. outputter: browser
pip install uvicorn websockets
1. outputter: gui
pip install dearpygui

## Usage

```bash
$python main.py --help
usage: python main.py [options]

displays gamepad input history.
Modify config.py to change default values.

options:
  -h, --help            show this help message and exit
  --logfile LOGFILE     log file name. if none, log file is not created.
  --device-name DEVICE_NAME
                        device name. partial name is okay like Microsoft but case-sensitive.
                        To know device names see evtest or something.
  --outputter OUTPUTTER
                        select outputter: terminal, browswer, gui. if none, terminal
  --loglevel LOGLEVEL   loglevel: set info, warning,debug or something
  --port PORT           browser port. that is used for web browser outputter
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

# Configuration. Edit conig.py
vim config.py
```
