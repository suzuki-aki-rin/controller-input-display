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
