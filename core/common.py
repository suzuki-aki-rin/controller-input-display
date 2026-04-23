from core.constants import NUMPAD, ARROW
from core.pollers import GamepadHoldedButtons
from dataclasses import dataclass


@dataclass
class FormattedHoldedButtons:
    hold_frame: str
    arrow: str
    btns: str


def format_holded_buttons(holded_btns: GamepadHoldedButtons) -> FormattedHoldedButtons:
    numpad = NUMPAD.get(frozenset(holded_btns.dirs), "5")
    sorted_btns = sorted(holded_btns.btns)

    return FormattedHoldedButtons(
        hold_frame=str(holded_btns.hold_frame),
        arrow=ARROW[numpad],
        btns=" ".join(sorted_btns),
    )


def holded_buttons_to_str(holded_btns: GamepadHoldedButtons) -> str:
    numpad = NUMPAD.get(frozenset(holded_btns.dirs), "5")
    sorted_btns = sorted(holded_btns.btns)

    hold_frame = str(holded_btns.hold_frame)
    arrow = ARROW[numpad]
    btns = " ".join(sorted_btns)

    return " ".join((hold_frame, arrow, btns))
