from utils.linked_list import LinkedList
from typing import Dict
from threading import Lock


class IndexShard:
    _data: Dict[str, LinkedList]
    _size: int
    _lock: Lock

    def __init__(self) -> None:
        self._data = dict()
        self._size = 0
        self._lock = Lock()

    def add(self, word: str, docId: int) -> None:
        with self._lock:
            if not word in self._data:
                self._size += 1
                self._data[word] = LinkedList()

            self._data[word].add(docId)

    def contains(self, word: str, docId: int):
        with self._lock:
            if not word in self._data:
                return False
            return self._data[word].index(docId) != -1
