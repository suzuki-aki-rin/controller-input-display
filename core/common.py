from core.constants import NUMPAD, ARROW
from core.pollers import GamepadHoldedButtons


def format_payload(pressed_buttons: GamepadHoldedButtons) -> dict:
    numpad = NUMPAD.get(frozenset(pressed_buttons.dirs), "5")
    arrow = ARROW[numpad]
    return {
        "type": "update",
        "hold": pressed_buttons.hold_frame,
        "arrow": arrow,
        "btns": sorted(pressed_buttons.btns),
    }


def format_payload_to_str(fp: dict) -> str:
    return f"{fp['hold']} {fp['arrow']} {' '.join(fp['btns'])}"
