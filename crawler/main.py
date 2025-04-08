import asyncio
import time
from typing import Dict, Set
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import requests

import cProfile
import pstats

from cli import args
from domain_utils import DomainControler
from frontier.frontier import Frontier


class Crawler:
    cfg: args.Config
    frontier: Frontier
    visited: Set[str]
    domain_data: Dict[str, DomainControler]
    semaphore: asyncio.Semaphore
    run: bool
    count: int
    count_lock: asyncio.Lock

    def __init__(self, cfg: args.Config) -> None:
        self.cfg = cfg
        self.run = False

        self.frontier = Frontier()
        self.visited = set()
        self.domain_data = dict()
        self.semaphore = asyncio.Semaphore(value=cfg.max_concurrency)

        self.count = 0
        self.count_lock = asyncio.Lock()

    async def begin(self) -> None:
        await self._enqueue_seeds()

        self.run = True

        while self.run:
            url: str | None = await self.frontier.get()
            if not url or url in self.visited:
                continue
            await self._fetch_page(url)
            self.frontier.queue.task_done()

            async with self.count_lock:
                self.count += 1

                if self.count >= self.cfg.max_page_count:
                    self.run = False

    async def _enqueue_seeds(self) -> None:
        with open(file=self.cfg.seed_file, mode='r') as f:
            seed: str = "aaaa"
            while seed:
                seed: str = f.readline().strip("\r\n ")
                if not seed:
                    continue
                await self.frontier.put(seed)

    async def _fetch_robots_txt(self, domain: str) -> RobotFileParser | None:
        robots_url = f'http://{domain}/robots.txt'
        try:
            resp = await self._fetch(url=robots_url)
            text = resp.text
        except Exception:
            return None

        rp = RobotFileParser()
        rp.parse(text.splitlines())

        return rp

    async def _fetch_page(self, url: str) -> None:
        domain = url.split("/")[2]

        robot_rules: RobotFileParser | None = await self._fetch_robots_txt(domain=domain)
        if not robot_rules:
            return

        if domain not in self.domain_data:
            rb = await self._fetch_robots_txt(domain=domain)
            if not rb:
                return

            self.domain_data[domain] = DomainControler(
                args=self.cfg,
                robots=rb,
            )

        dm: DomainControler = self.domain_data[domain]
        async with dm.lock:
            crawl_delay: float = float(
                dm.robots.crawl_delay(
                    useragent=self.cfg.user_agent) or self.cfg.default_crawl_delay
            )
            last_time: float = dm.last_request_time or 0
            elapsed: float = time.time() - last_time

            if elapsed < crawl_delay:
                await asyncio.sleep(crawl_delay - elapsed)

            dm.last_request_time = time.time()

        if not robot_rules.can_fetch(useragent=self.cfg.user_agent, url=url):
            return

        response: requests.Response
        async with self.semaphore and dm.semaphore:
            try:
                response = await self._fetch(url=url)
            except requests.RequestException:
                return

        soup = BeautifulSoup(markup=response.text, features="html.parser")

        for element in soup(name=["script", "style", "noscript"]):
            element.extract()

        text_content = str(soup.get_text()).replace("\n\n", "")

        if self.cfg.debug:
            title: str = soup.title.string.strip(
                "\n\t\r ") if soup.title and soup.title.string else ""  # type: ignore
            timestamp = int(time.time())

            text = " ".join(text_content[:1000].split()[:20])
            print(
                r'{'
                f'"Title": "{title}",'
                f'"URL": "{url},'
                f'"Text": "{text}",'
                f'"Timestamp": {timestamp}'
                r'}'
            )

        links: Set[str] = {
            a["href"] for a in soup.find_all("a", href=True)    # type: ignore
        }

        async with asyncio.TaskGroup() as tasks:
            for link in links:
                if link.startswith("http") and link not in self.visited:
                    tasks.create_task(self.frontier.put(link))

        self.visited.add(url)

    async def _fetch(self, url: str) -> requests.Response:
        async with self.semaphore:
            response = await asyncio.to_thread(requests.get, url, timeout=5, headers=self.cfg.fetch_header)
            response.raise_for_status()
            return response


async def main() -> None:
    cfg: args.Config = args.parse_args()
    crawler = Crawler(cfg=cfg)

    profiler = cProfile.Profile()
    profiler.enable()

    crawler_task = asyncio.create_task(crawler.begin())

    await crawler.frontier.queue.join()
    crawler.run = False
    await crawler_task

    profiler.disable()

    with open("profile_stats.txt", "w") as f:
        stats = pstats.Stats(profiler, stream=f).sort_stats("cumtime")
        stats.print_stats()


if __name__ == "__main__":
    asyncio.run(main())
