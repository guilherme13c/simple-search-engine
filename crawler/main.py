from concurrent.futures import ThreadPoolExecutor
import sys
import threading
import time
from typing import Any, Dict, List, Set
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import requests
from cli import args as cli
from frontier.frontier import *
from cli.defaults import *
from domain_utils import DomainControler
from warc_utils import WarcControler

from bs4 import XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


stdout_lock: threading.Lock


def main() -> None:
    global stdout_lock
    stdout_lock = threading.Lock()

    cfg: cli.Config = cli.parse_args()

    crawler = Crawler(cfg=cfg)
    crawler.start()


class Crawler:
    cfg: cli.Config
    fontier: Frontier
    visited: Set[int]
    domain_data: Dict[str, DomainControler]
    semaphore: threading.Semaphore
    warc: WarcControler
    run: bool
    count: int
    t: float

    def __init__(self, cfg: cli.Config) -> None:
        self.cfg = cfg
        self.frontier = Frontier()
        self.visited = set()
        self.domain_data = dict()
        self.semaphore = threading.Semaphore(
            value=self.cfg.max_concurrency
        )
        self.warc = WarcControler(config=cfg)
        self.run = True
        self.count = 0
        self.t = time.time()

    def start(self) -> None:
        """Crawl using a thread pool to limit concurrency."""

        self._enqueue_seeds()

        with ThreadPoolExecutor(max_workers=self.cfg.max_concurrency) as executor:
            while self.run:
                url: str | None = self.frontier.get()
                if not url or hash(url) in self.visited:
                    continue

                executor.submit(self._fetch_page, url)

            if not self.run:
                executor.shutdown(wait=False, cancel_futures=True)

    def _fetch_page(self, url: str) -> None:
        """Fetches a page, extracts links and the title, and marks it as visited."""
        try:
            domain = url.split(sep="/")[2]
        except:
            return

        if not domain in self.domain_data:
            robots_url = f'http://{domain}/robots.txt'
            rp = RobotFileParser(url=robots_url)

            try:
                rp.read()
            except:
                return

            self.domain_data[domain] = DomainControler(self.cfg, rp)

        dm: DomainControler = self.domain_data[domain]

        with dm.lock:
            crawl_delay: float = float(
                dm.robots.crawl_delay(
                    useragent=self.cfg.user_agent) or self.cfg.default_crawl_delay
            )
            last_time: float = dm.last_request_time or 0
            elapsed: float = time.time() - last_time

            if elapsed < crawl_delay:
                time.sleep(crawl_delay - elapsed)

            dm.last_request_time = time.time()

        if not dm.robots.can_fetch(useragent=self.cfg.user_agent, url=url):
            return

        response: requests.Response
        with self.semaphore and dm.semaphore:
            try:
                response = requests.get(
                    url=url,
                    timeout=5,
                    headers=self.cfg.fetch_header,
                )
                response.raise_for_status()
            except requests.RequestException:
                return

        soup = BeautifulSoup(markup=response.text, features="html.parser")

        # remove unwanted elements
        for element in soup(name=["script", "style", "noscript"]):
            element.extract()

        text_content = str(object=soup.get_text(separator=" ", strip=True))

        if self.cfg.debug:
            title: str
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            else:
                title = ""

            timestamp = int(time.time())

            text = " ".join(text_content[:1000].split()[:20])
            with stdout_lock:
                print(
                    r'{'
                    f'"Title": "{title}",'
                    f'"URL": "{url},'
                    f'"Text": "{text}",'
                    f'"Timestamp": {timestamp}'
                    r'}'
                )
        self.warc.write(url=url, resp=response)

        links: Set[str] = {
            a["href"] for a in soup.find_all("a", href=True)    # type: ignore
        }

        for link in links:
            if link.startswith("http") and link not in self.visited:
                self.frontier.put(link)

        self.visited.add(hash(url))

        self.count += 1

        if self.count >= self.cfg.max_page_count:
            self.run = False

        if self.cfg.show_progress and self.count % 50 == 0:
            with stdout_lock:
                print(f"{self.count}/{self.cfg.max_page_count} | {time.time() - self.t} seconds elapsed | {self.count / (time.time() - self.t):.2f} pages/second")

        if self.count % 1000 == 0:
            self.domain_data.clear()
            print(f"frontier size: {sys.getsizeof(self.frontier.queue.queue)} bytes")
            print(f"visited size: {sys.getsizeof(self.visited)} bytes")
            print(f"domain data size: {sys.getsizeof(self.domain_data)} bytes")
            print(f"warc controler size: {sys.getsizeof(self.warc)} bytes")

    def _enqueue_seeds(self) -> None:
        with open(file=self.cfg.seed_file, mode='r') as f:
            seed: str = "seed"
            while seed:
                seed: str = f.readline().strip("\r\n ")
                if not seed:
                    continue
                self.frontier.put(seed)


if __name__ == "__main__":
    main()
