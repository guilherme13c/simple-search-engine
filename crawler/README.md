# Programming Assignment 1
Guilherme Soeiro de Carvalho Caporali (2021031955)

Universidade Federal de Minas Gerais (UFMG)

Belo Horizonte - MG - Brasil

guilhermesoeiro@dcc.ufmg.br

## Introduction
This project implements a web crawler capable of efficiently collecting a mid-sized corpus of webpages while strictly adhering to crawling policies. The goals include:

- Fetching 100,000 unique HTML pages.
- Respecting site-specific politeness rules (robots.txt, request delays).
- Storing the retrieved data in compressed WARC files.

The crawler is developed in Python 3, running in a controlled virtual environment to ensure compatibility and reproducibility. It supports parallel crawling with multiple threads and includes a debugging mode for detailed tracking. This document outlines the crawler’s design, key data structures, implemented algorithms, and corpus analysis.

## Implementation Details
The crawler is organized under the crawler/ directory. Key components:

### Frontier and URL Management
A thread-safe min-heap stores <priority, URL>. Random priorities help distribute requests across domains. O(log N) per insert/delete, capped at 1,000 entries for memory control.

### Visited Set
URLs are stored as 64-bit hashes instead of full strings. This reduces per-entry storage from O(L) to a fixed 8 bytes. Hash collision probability is negligible for 100k entries.

### Domain Controller Cache
A dictionary maps domains to DomainController objects (robots.txt policies, last-fetch timestamps).
The dictionary is cleared every 1,000 pages to conserve memory, trading slight re-fetch overhead.

### Parallel Crawling
Using T threads (threading.Thread), each worker:

1 .Dequeues a URL (thread-safe).
2. Enforces domain-specific delay.
3. Fetches and parses the page (with BeautifulSoup).
4. Saves the HTML to the WARC file.
5. Extracts and enqueues new links.

Parallel speedup is near O(T) until bottlenecks arise (network/shared structures).

### WARC Storage and Debugging
Pages are written to gzip-compressed WARC files (1,000 records each). In debug mode (-d), a JSON summary (URL, title, first 20 words, timestamp) is printed per page.

## How to Use & Command-Line Arguments
The crawler accepts the following command-line options:

| Shorthand | Argument | Description | Required |
|--|--|--|--|
| -s | --seeds | Path to a file with one seed URL per line. Stored in seed_file. | ✅ |
| -n | --number |	Maximum number of unique pages to crawl (default: 100,000). Stored in max_page_count. | ❌ |
| -d | --debug |	Enable debug mode. Emits JSON record per page. Stored in debug (bool). | ❌ |
| -p | --show-progress |	Display progress and average speed, updated every 50 pages. Stored in show_progress (bool). | ❌ |
| -c | --max-concurrency |	Maximum number of worker threads (default: 16). Stored in max_concurrency. | ❌ |
| | --domain-concurrency | Maximum simultaneous requests per domain (default: 5). Stored in default_max_concurrent_requests_per_domain. | ❌ |
| | --craw-delay | Default delay (in seconds) between requests to the same domain (default: 0.1s). Stored in default_crawl_delay. | ❌ |
| | --save-interval |	Number of pages per WARC file before rotation (default: 1,000). Stored in save_interval. | ❌ |
