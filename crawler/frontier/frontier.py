from queue import Queue, Empty


class Frontier:
    def __init__(self) -> None:
        self.queue: Queue[str] = Queue()

    def put(self, url: str) -> None:
        self.queue.put(item=url)

    def get(self) -> str | None:
        try:
            return self.queue.get()
        except Empty:
            return None

    def __bool__(self) -> bool:
        return not self.queue.empty()
