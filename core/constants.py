from evdev import ecodes
#  -------- Constants -------------------------------------------------------------------

FRAME_SEC = 1 / 60
TRIGGER_THRESHOLD = 64

NUMPAD = {
    frozenset(): "5",
    frozenset(["UP"]): "8",
    frozenset(["DOWN"]): "2",
    frozenset(["LEFT"]): "4",
    frozenset(["RIGHT"]): "6",
    frozenset(["UP", "RIGHT"]): "9",
    frozenset(["UP", "LEFT"]): "7",
    frozenset(["DOWN", "RIGHT"]): "3",
    frozenset(["DOWN", "LEFT"]): "1",
}

ARROW = {
    "1": "↙",
    "2": "↓",
    "3": "↘",
    "4": "←",
    "5": "·",
    "6": "→",
    "7": "↖",
    "8": "↑",
    "9": "↗",
}

BTN_MAP = {
    ecodes.BTN_SOUTH: "A",
    ecodes.BTN_EAST: "B",
    ecodes.BTN_NORTH: "X",
    ecodes.BTN_WEST: "Y",
    ecodes.BTN_TL: "LB",
    ecodes.BTN_TR: "RB",
    ecodes.BTN_TL2: "LT",
    ecodes.BTN_TR2: "RT",
    ecodes.BTN_TR2: "RT",
    ecodes.BTN_THUMBL: "L3",
    ecodes.BTN_THUMBR: "R3",
    ecodes.BTN_START: "START",
    ecodes.BTN_SELECT: "BACK",
    ecodes.BTN_MODE: "MODE",
}

HAT_MAP = {
    ecodes.ABS_HAT0X: {-1: "LEFT", 1: "RIGHT"},
    ecodes.ABS_HAT0Y: {-1: "UP", 1: "DOWN"},
}

TRIGGER_MAP = {
    ecodes.ABS_Z: "LT",
    ecodes.ABS_RZ: "RT",
}
