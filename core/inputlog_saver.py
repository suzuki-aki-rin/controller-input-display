from pathlib import Path
from datetime import datetime
from core.pollers import GamepadHoldedButtons
from core.common import holded_buttons_to_str

#  =====================================================================
#            Logger
#  =====================================================================
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class InputLogSaver:
    def __init__(self, file_path: Path) -> None:
        self.input_logs: list = []
        self.file_path = file_path

    def input(self, buttons: GamepadHoldedButtons) -> None:
        self.input_logs.append(buttons)

    def save_to_file(self) -> None:

        with open(self.file_path, "a") as f:
            f.write(f"input log at {datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}\n")
            f.writelines(
                (holded_buttons_to_str(line) + "\n" for line in self.input_logs)
            )
            f.write("\n")
            # for f_payload in self.input_logs:
            #     line = format_payload_to_str(f_payload)
            #     f.writelines(line + "\n")
        logger.debug("saved: %s", str(self.file_path))

    def change_path(self, new_path: Path) -> None:
        self.file_path = new_path


def main():
    path = Path("log____txt")
    history_saver = InputLogSaver(path)
    input_ex = GamepadHoldedButtons(
        dirs={"DOWN", "RIGHT"}, btns={"X", "Y"}, hold_frame=20
    )
    history_saver.input(input_ex)

    history_saver.save_to_file()


if __name__ == "__main__":
    main()
