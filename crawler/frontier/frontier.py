from queue import PriorityQueue, Empty
import random
from typing import Tuple


class Frontier:
    def __init__(self) -> None:
        self.queue: PriorityQueue[Tuple[int, str]] = PriorityQueue()

    def put(self, url: str) -> None:
        prio: int = random.randrange(0, 1000)
        self.queue.put(item=(prio, url))

    def get(self) -> str | None:
        try:
            _, url = self.queue.get()
            return url
        except Empty:
            return None

    def __bool__(self) -> bool:
        return not self.queue.empty()
