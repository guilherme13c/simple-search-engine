import argparse
from typing import Dict
from .defaults import *


class Config:
    seed_file: str
    corpus_dir: str

    max_page_count: int

    debug: bool
    show_progress: bool

    user_agent: str
    fetch_header: Dict[str, str]

    default_crawl_delay: float
    default_max_concurrent_requests_per_domain: int
    max_concurrency: int

    save_interval: int

    run: bool


def parse_args() -> Config:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-s",
        "--seeds",
        help="Seed URLs to begin crawling",
        type=str,
        dest='seed_file',
        required=True,
    )
    parser.add_argument(
        "-n",
        "--number",
        help="Maximum number of unique pages to be crawled",
        type=int,
        default=DEFAULT_PAGE_COUNT,
        dest='max_page_count',
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Run in debug mode",
        action='store_true',
        dest='debug',
        default=False,
    )
    parser.add_argument(
        "-p",
        "--show-progress",
        help="Show progress",
        action='store_true',
        dest='show_progress',
        default=False,
    )
    parser.add_argument(
        "-c",
        "--max-concurrency",
        help="Maximum number threads to be used",
        type=int,
        default=DEFAULT_MAX_CONCURRENCY,
        dest='max_concurrency',
    )
    parser.add_argument(
        "--domain-concurrency",
        help="Default maximum number simultaneous of requests per domain",
        type=int,
        default=DEFAULT_MAX_CONCURRENT_REQUESTS_PER_DOMAIN,
        dest='default_max_concurrent_requests_per_domain',
    )
    parser.add_argument(
        "--craw-delay",
        help="Default craw delay",
        type=float,
        default=DEFAULT_CRAWL_DELAY,
        dest='default_crawl_delay',
    )
    parser.add_argument(
        "--save-interval",
        help="Number of pages written to each warc file",
        type=int,
        default=DEFAULT_SAVE_INTERVAL,
        dest='save_interval',
    )

    args: Config = Config()
    parser.parse_args(namespace=args)

    args.user_agent = "SimpleCrawler/1.0.0"
    args.fetch_header = {
        "User-Agent": args.user_agent,
    }
    args.corpus_dir = DEFAULT_CORPUS_DIR

    args.run = True

    return args
