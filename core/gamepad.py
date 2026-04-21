"""Gamepad input reader and its state holder.

This class:
- is created by device name or device object created,
- reads events via own devices event loop, and
- update state holding which button and direction are pressed by the events read.

Usage example:
    gp_reader = GamepadReader.from_device_name("Microsoft")

    async def poll_print():
        while True:
            await asyncio.sleep(1)
            print(gp_reader.state)

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(gp_reader.async_read())
            tg.create_task(poll_print())
    except* CancelledError:
        logger.error("cancelled error")
        raise CancelledError
"""

from asyncio import CancelledError
from typing import Self
from dataclasses import dataclass

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


#  =====================================================================
#            Classes
#  =====================================================================
@dataclass
class GamepadState:
    dirs: set[str]  # e.g., {"left", "right"}
    btns: set[str]


class GamepadReader:
    """
    A reader for a gamepad device that reads input events and store them.
    """

    def __init__(self, device: InputDevice):
        self.device: InputDevice = device
        self.state = GamepadState(dirs=set(), btns=set())
        # self.btn_map = self._build_button_map()

    @classmethod
    def find_device(cls, dev_name: str) -> InputDevice | None:
        for path in evdev.list_devices():
            dev = InputDevice(path)
            if dev_name in dev.name:
                return dev
        return None

    @classmethod
    def from_device_name(cls, device_name: str) -> Self:
        device = cls.find_device(device_name)
        return cls(device)

    async def async_read(self):
        # get reference to avoid self reference in loop for a slightly good performance.
        device = self.device
        update = self.update
        logger.debug("event_reader starts")
        try:
            async for event in device.async_read_loop():
                update(event)
        except CancelledError:
            logger.debug("event_reader is cancelled")
            raise

    def read(self):
        # get reference to avoid self reference in loop for a slightly good performance.
        device = self.device
        update = self.update
        logger.debug("event_reader starts")
        try:
            for event in device.read_loop():
                update(event)
        except KeyboardInterrupt:
            logger.debug("KeyboardInterrupt: event_reader is cancelled.")
            raise

    def update(self, event):
        btns = self.state.btns
        dirs = self.state.dirs

        #  -------- EV_KEY --------------------------------------------------------------
        if event.type == ecodes.EV_KEY:
            if event.value not in (0, 1) or event.code not in BTN_MAP:
                return
            name = BTN_MAP[event.code]
            btns.add(name) if event.value == 1 else btns.discard(name)

        #  -------- EV_ABS ---------------------------------------------------------
        elif event.type == ecodes.EV_ABS:
            #  -------- HAT_MAP: direction buttons --------------------------------------
            if event.code in HAT_MAP:
                axis = HAT_MAP[event.code]
                # delete stored values of the axis
                for d in axis.values():
                    dirs.discard(d)
                if event.value in axis:
                    dirs.add(axis[event.value])

            #  -------- TRIGGER_MAP: L and R trigger -------------------------------
            elif event.code in TRIGGER_MAP:
                name = TRIGGER_MAP[event.code]
                btns.add(name) if event.value > TRIGGER_THRESHOLD else btns.discard(
                    name
                )

    # def _build_button_map(self) -> dict[int, str]:
    #     cap = self.device.capabilities(verbose=False)
    #     key_codes = cap.get(ecodes.EV_KEY, [])
    #     logger.debug(key_codes)
    #     button_map = {}
    #
    #     for code in key_codes:
    #         # evdev.ecodes can translate code → name
    #         names = ecodes.bytype[ecodes.EV_KEY].get(code, [f"KEY_{code}"])
    #         # pick up shortest string from names. names can be string or tuple.
    #         name = min(names, key=len) if isinstance(names, tuple) else names
    #
    #         button_map[code] = name[4:]
    #     return button_map


async def main():
    logging.basicConfig(level=logging.DEBUG)
    logger.debug("DEGUG")
    gp_reader = GamepadReader.from_device_name("Microsoft")

    async def poll_print():
        while True:
            await asyncio.sleep(1)
            print(gp_reader.state)

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(gp_reader.async_read())
            tg.create_task(poll_print())
    except* CancelledError as e:
        logger.error("cancellederror")
        raise CancelledError


if __name__ == "__main__":
    import asyncio

    try:
        # print(__doc__)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("exit")
