from concurrent.futures import ThreadPoolExecutor
import threading
import time
from typing import Dict, Set
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import requests
from cli import args as cli
from frontier.frontier import *
from cli.defaults import *
from domain_utils import DomainControler
from warc_utils import WarcControler


def main() -> None:
    cfg: cli.Config = cli.parse_args()

    start_crawling(cfg)


def start_crawling(cfg: cli.Config) -> None:
    """Crawl using a thread pool to limit concurrency."""

    frontier = Frontier()

    visited: Set[str] = set()

    robots_cache: Dict[str, RobotFileParser] = dict()

    domain_metadata: Dict[str, DomainControler] = dict()

    semaphore: threading.Semaphore = threading.Semaphore(
        cfg.max_concurrency
    )

    warc = WarcControler(config=cfg)

    enqueue_seeds(seed_file=cfg.seeds, frontier=frontier)

    with ThreadPoolExecutor(max_workers=cfg.max_concurrency) as executor:
        while cfg.run:
            url: str | None = frontier.get()
            if not url or url in visited:
                continue

            domain = url.split(sep="/")[2]
            robot_rules: RobotFileParser | None = fetch_robots_txt(
                domain=domain, robots_cache=robots_cache)
            if not robot_rules:
                continue

            executor.submit(fetch_page, url, robot_rules,
                            frontier, visited, domain_metadata, semaphore, cfg, warc)
        if not cfg.run:
            executor.shutdown(wait=True, cancel_futures=True)


def fetch_page(url: str, robot_rules: RobotFileParser, frontier: Frontier, visited: Set[str], domain_metadata: Dict[str, DomainControler], semaphore: threading.Semaphore, config: cli.Config, warc: WarcControler) -> None:
    """Fetches a page, extracts links and the title, and marks it as visited."""
    domain: str = url.split(sep="/")[2]
    if domain not in domain_metadata:
        domain_metadata[domain] = DomainControler(args=config)

    with domain_metadata[domain].lock:
        crawl_delay: float = float(
            robot_rules.crawl_delay(
                useragent=config.user_agent) or config.default_crawl_delay
        )
        last_time: float = domain_metadata[domain].last_request_time or 0
        elapsed: float = time.time() - last_time

        if elapsed < crawl_delay:
            time.sleep(crawl_delay - elapsed)

        domain_metadata[domain].last_request_time = time.time()

    if not robot_rules.can_fetch(useragent=config.user_agent, url=url):
        return

    response: requests.Response
    with semaphore and domain_metadata[domain].semaphore:
        try:
            response = requests.get(
                url, timeout=5, headers=config.fetch_header)
            response.raise_for_status()
        except requests.RequestException:
            return

    soup = BeautifulSoup(markup=response.text, features="html.parser")

    # remove unwanted elements
    for element in soup(["script", "style", "noscript"]):
        element.extract()

    text_content = str(soup.prettify())

    if config.debug:
        title: str = soup.title.string.strip() if soup.title else ""  # type: ignore
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
    warc.write(url, response)

    links: Set[str] = {
        a["href"] for a in soup.find_all("a", href=True)    # type: ignore
    }

    for link in links:
        if link.startswith("http") and link not in visited:
            frontier.put(link)

    visited.add(url)


def fetch_robots_txt(domain: str, robots_cache: Dict[str, RobotFileParser]) -> RobotFileParser | None:
    """Fetch and parse robots.txt for a domain, caching the result."""
    if domain in robots_cache:
        return robots_cache[domain]

    robots_url = f'http://{domain}/robots.txt'
    rp: RobotFileParser = RobotFileParser(robots_url)

    try:
        rp.read()
    except:
        return None

    robots_cache[domain] = rp
    return rp


def enqueue_seeds(seed_file: str, frontier: Frontier) -> None:
    with open(file=seed_file, mode='r') as f:
        seed: str = f.readline().strip("\r\n ")
        while seed:
            if not seed:
                continue
            frontier.put(seed)
            seed: str = f.readline().strip("\r\n ")


if __name__ == "__main__":
    main()
