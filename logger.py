class InputLogger:
    def __init__(self, path: str):
        self._file = open(path, 'w')

    def write(self, line: str):
        self._file.write(line + "\n")
        self._file.flush()

    def close(self):
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
