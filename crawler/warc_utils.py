import json
import os
import shutil
import threading
from typing import Set, List
import requests
from io import BufferedWriter

from cli.args import Config
from frontier.frontier import Frontier
from warcio.warcwriter import WARCWriter
from warcio.recordloader import ArcWarcRecord
from warcio.statusandheaders import StatusAndHeaders


class WarcControler:
    lock: threading.Lock
    count: int
    file_index: int
    file: BufferedWriter
    writer: WARCWriter
    warc_dir: str
    save_interval: int

    def __init__(self, config: Config) -> None:
        """Initialize the WARC controller with a thread lock and first file."""
        shutil.rmtree(config.corpus_dir)
        os.makedirs(name=config.corpus_dir, exist_ok=True)
        self.warc_dir = config.corpus_dir
        self.file_index = 1
        self.count = 0
        self.lock = threading.Lock()
        self.save_interval = config.save_interval

        self.file = open(file=self._get_filename(), mode="ab")
        self.writer = WARCWriter(filebuf=self.file, gzip=True)

    def _get_filename(self) -> str:
        """Return the current WARC filename."""
        return os.path.join(self.warc_dir, f"crawl_{self.file_index}.warc")

    def write(self, url: str, resp: requests.Response) -> None:
        """Thread-safe writing to the WARC file using warcio."""
        with self.lock:
            headers_list = resp.raw.headers.items()
            http_headers = StatusAndHeaders(
                statusline='200 OK', headers=headers_list, protocol='HTTP/1.0')

            record: ArcWarcRecord = self.writer.create_warc_record(  # type: ignore
                uri=url,
                record_type="response",
                payload=resp.raw,
                http_headers=http_headers,
            )

            self.writer.write_record(record=record)  # type: ignore

            self.count += 1

            if self.count >= self.save_interval:
                self.rotate_file()

    def rotate_file(self) -> None:
        """Rotate to a new WARC file after reaching the save interval."""
        print(f"Rotating WARC file: {self.file_index}")
        self.close()
        self.file_index += 1
        self.count = 0
        self.file = open(file=self._get_filename(), mode="ab")
        self.writer = WARCWriter(filebuf=self.file, gzip=True)

    def close(self) -> None:
        """Close the current WARC file safely."""
        self.file.flush()
        self.file.close()
