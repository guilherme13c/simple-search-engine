from threading import Lock, Semaphore
from urllib.robotparser import RobotFileParser
from cli.args import Config


class DomainControler:
    last_request_time: float
    lock: Lock
    semaphore: Semaphore
    robots: RobotFileParser

    def __init__(self, args: Config, robot: RobotFileParser) -> None:
        self.last_request_time = 0
        self.lock = Lock()
        self.semaphore = Semaphore(
            value=args.default_max_concurrent_requests_per_domain)
        self.robots = robot
