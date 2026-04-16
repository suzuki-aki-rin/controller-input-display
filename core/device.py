from asyncio import CancelledError
import evdev
from evdev import InputDevice, ecodes
from core.constants import (
    BTN_MAP,
    HAT_MAP,
    TRIGGER_MAP,
    TRIGGER_THRESHOLD,
)

#  SECTION:=============================================================
#            Logger
#  =====================================================================
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ControllerState:
    def __init__(self):
        self.dirs: set[str] = set()
        self.btns: set[str] = set()

    def update(self, event):
        if event.type == ecodes.EV_KEY:
            if event.value not in (0, 1) or event.code not in BTN_MAP:
                return
            name = BTN_MAP[event.code]
            self.btns.add(name) if event.value == 1 else self.btns.discard(name)

        elif event.type == ecodes.EV_ABS:
            if event.code in HAT_MAP:
                axis = HAT_MAP[event.code]
                for d in axis.values():
                    self.dirs.discard(d)
                if event.value in axis:
                    self.dirs.add(axis[event.value])

            elif event.code in TRIGGER_MAP:
                name = TRIGGER_MAP[event.code]
                self.btns.add(
                    name
                ) if event.value > TRIGGER_THRESHOLD else self.btns.discard(name)


def find_device(dev_name: str) -> InputDevice | None:
    for path in evdev.list_devices():
        dev = InputDevice(path)
        if dev_name in dev.name:
            return dev
    return None


async def event_reader(device: InputDevice, state: ControllerState):
    logger.debug("event_reader starts")
    try:
        async for event in device.async_read_loop():
            state.update(event)
    except CancelledError:
        logger.debug("event_reader is cancelled")
