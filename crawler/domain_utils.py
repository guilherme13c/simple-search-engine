from threading import Lock, Semaphore
from cli.args import Config


class DomainControler:
    last_request_time: float
    lock: Lock
    semaphore: Semaphore

    def __init__(self, args: Config) -> None:
        self.last_request_time = 0
        self.lock = Lock()
        self.semaphore = Semaphore(
            args.default_max_concurrent_requests_per_domain)
