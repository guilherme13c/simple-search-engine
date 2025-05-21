from utils.linked_list import LinkedList

from threading import Lock
from typing import Dict, Any
import pickle


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

    def contains(self, word: str, docId: int) -> bool:
        with self._lock:
            if not word in self._data:
                return False
            return self._data[word].index(docId) != -1

    def save(self, path: str) -> None:
        with self._lock:
            with open(path, "wb") as f:
                pickle.dump(self, f)

    @staticmethod
    def load(path: str) -> 'IndexShard':
        with open(path, 'rb') as f:
            return pickle.load(f)

    def __getstate__(self) -> Dict[str, Any]:
        state = self.__dict__.copy()
        del state['_lock']
        return state

    def __setstate__(self, state) -> None:
        self.__dict__.update(state)
        self._lock = Lock()
