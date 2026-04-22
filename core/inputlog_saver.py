from pathlib import Path
from core.common import format_payload_to_str

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

    def input(self, buttons) -> None:
        self.input_logs.append(buttons)

    def save_to_file(self) -> None:
        with open(self.file_path, "w") as f:
            for f_payload in self.input_logs:
                line = format_payload_to_str(f_payload)
                f.writelines(line + "\n")

    def change_path(self, new_path: Path) -> None:
        self.file_path = new_path


def main():
    path = Path("log____txt")
    history_saver = InputLogSaver(path)
    history_saver.input({"type": "update", "hold": 434, "arrow": "·", "btns": []})
    history_saver.input({"type": "update", "hold": 2, "arrow": "·", "btns": ["B"]})
    history_saver.input(
        {"type": "update", "hold": 1, "arrow": "·", "btns": ["B", "LT"]}
    )
    history_saver.input({"type": "update", "hold": 3, "arrow": "·", "btns": ["B"]})
    history_saver.input({"type": "update", "hold": 13, "arrow": "·", "btns": []})
    history_saver.input({"type": "update", "hold": 5, "arrow": "·", "btns": ["B"]})

    history_saver.save_to_file()


if __name__ == "__main__":
    main()
