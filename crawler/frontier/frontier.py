from asyncio import PriorityQueue, QueueEmpty
import random
from typing import Tuple


class Frontier:
    def __init__(self) -> None:
        self.queue: PriorityQueue[Tuple[int, str]
                                  ] = PriorityQueue(maxsize=10000)

    async def put(self, url: str) -> None:
        prio: int = random.randrange(0, 1000)
        try:
            await self.queue.put(item=(prio, url))
        except:
            return None

    async def get(self) -> str | None:
        try:
            _, url = await self.queue.get()
            return url
        except QueueEmpty:
            return None

    def __bool__(self) -> bool:
        return not self.queue.empty()
