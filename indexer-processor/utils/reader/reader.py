from typing import Optional, TextIO, Dict, Any
import threading
import json


class Reader:
    filePath: str
    _lock: threading.Lock
    _file: TextIO | None

    def __init__(self, path: str):
        self.filePath = path
        self._file = None
        self._lock = threading.Lock()

    def __enter__(self):
        self._file = open(self.filePath, "r")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._file and not self._file.closed:
            self._file.close()

    def next_line(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            if self._file is None:
                self._file = open(self.filePath, 'r')
            line = self._file.readline()
            if not line:
                return None
            return json.loads(line.strip())

    def close(self):
        with self._lock:
            if self._file and not self._file.closed:
                self._file.close()
