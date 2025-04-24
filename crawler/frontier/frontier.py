from typing import List
from queue import PriorityQueue, Empty, Full
import random
from typing import Tuple


QUEUE_MAX_SIZE: int = 1000


class Frontier:
    def __init__(self) -> None:
        self.queue: PriorityQueue[Tuple[int, str]
                                  ] = PriorityQueue(QUEUE_MAX_SIZE)

    def put(self, url: str) -> None:
        prio: int = random.randrange(0, QUEUE_MAX_SIZE)
        try:
            self.queue.put_nowait(item=(prio, url))
        except Full:
            pass

    def get(self) -> str | None:
        try:
            _, url = self.queue.get()
            return url
        except Empty:
            return None

    def __bool__(self) -> bool:
        return not self.queue.empty()
    
    def load(self, urls: list[str]) -> None:
        """Load a list of URLs into the queue."""
        for url in urls:
            self.put(url)