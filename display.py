from collections import deque
from constants import NUMPAD, ARROW, HISTORY_SIZE


def format_line(hold: int, dirs: set[str], btns: set[str]) -> str:
    numpad   = NUMPAD.get(frozenset(dirs), '5')
    arrow    = ARROW[numpad]
    btns_str = '+'.join(sorted(btns)) if btns else ''
    return f"{hold:>4} : {arrow}  {btns_str}".rstrip()


def reserve_display():
    """Print blank lines once at startup to reserve the display block."""
    for _ in range(HISTORY_SIZE + 1):
        print()


def redraw(live_line: str, history: deque[str]):
    print(f"\033[{HISTORY_SIZE + 1}A", end='')
    print(f"\r{live_line:<40}")
    for line in history:
        print(f"\r{line:<40}")
    blank_count = HISTORY_SIZE - len(history)
    for _ in range(blank_count):
        print(f"\r{'':<40}")
