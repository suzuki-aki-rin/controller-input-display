from collections import deque
from core.constants import NUMPAD, ARROW


def format_line(hold: int, dirs: set[str], btns: set[str]) -> str:
    numpad = NUMPAD.get(frozenset(dirs), "5")
    arrow = ARROW[numpad]
    btns_str = "+".join(sorted(btns)) if btns else ""
    return f"{hold:>4} : {arrow}  {btns_str}".rstrip()


class TerminalOutputter:
    """
    Outputs input history to terminal
    """

    def __init__(self, history_size) -> None:
        self.history_size = history_size
        self.history: deque[str] = deque(maxlen=self.history_size)

    def reserve_display(self) -> None:
        """Print blank lines once at startup to reserve the display block."""
        for _ in range(self.history_size + 1):
            print()

    def redraw(self, live_line: str) -> None:
        print(f"\033[{self.history_size + 1}A", end="")
        print(f"\r{live_line:<40}")
        for line in self.history:
            print(f"\r{line:<40}")
        blank_count = self.history_size - len(self.history)
        for _ in range(blank_count):
            print(f"\r{'':<40}")

    def on_update(self, hold, dirs, btns) -> None:
        line = format_line(hold, dirs, btns)
        self.history.appendleft(line)

    def on_frame(self, hold, dirs, btns) -> None:
        live_line = format_line(hold, dirs, btns)
        self.redraw(live_line)
