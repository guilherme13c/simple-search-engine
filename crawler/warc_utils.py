import json
import os
import shutil
import threading
from typing import Any, Dict, Set, List
import requests
from cli.args import Config
from frontier.frontier import Frontier
from io import BufferedWriter
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
    frontier: Frontier
    visited: Set[str]
    save_interval: int
    use_checkpoint: bool
    make_checkpoints: bool
    max_pages: int
    show_progress: bool
    run: List[bool]

    def __init__(self, config: Config) -> None:
        """Initialize the WARC controller with a thread lock and first file."""
        shutil.rmtree(config.corpus_dir)
        os.makedirs(name=config.corpus_dir, exist_ok=True)
        self.warc_dir = config.corpus_dir
        self.file_index = 1
        self.count = 0
        self.lock = threading.Lock()
        self.max_pages = config.max_page_count
        self.use_checkpoint = config.use_checkpoint
        self.make_checkpoints = config.make_checkpoints
        self.show_progress = config.progress
        self.save_interval = config.save_interval
        self.run = [config.run]  # pass by reference

        if self.use_checkpoint:
            self._load_checkpoint()

        self.file = open(file=self._get_filename(), mode="ab")
        self.writer = WARCWriter(filebuf=self.file, gzip=True)

    def _load_checkpoint(self) -> None:
        """Load the last saved checkpoint (if available)."""
        checkpoint_file = "checkpoint.json"

        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint_data: Dict[str, Any] = json.load(f)

                self.file_index = checkpoint_data["file_index"]
                self.count = checkpoint_data["count"]

                for url in checkpoint_data["frontier"]:
                    self.frontier.put(url)

                self.visited.update(checkpoint_data["visited"])

    def _save_checkpoint(self) -> None:
        """Save the current state to a JSON checkpoint."""
        with self.lock:
            checkpoint_data = {  # type: ignore
                "file_index": self.file_index,
                "count": self.count,
                "frontier": list(self.frontier.queue.queue),
                "visited": list(self.visited),
                "page_count": self.count
            }

            with open(file="checkpoint.json", mode="w", encoding="utf-8") as f:
                json.dump(obj=checkpoint_data, fp=f, indent=4)

    def _get_filename(self) -> str:
        """Return the current WARC filename."""
        return os.path.join(self.warc_dir, f"crawl_{self.file_index}.warc")

    def write(self, url: str, resp: requests.Response) -> None:
        """Thread-safe writing to the WARC file using warcio."""
        with self.lock:
            headers_list = resp.raw.headers.items()
            http_headers = StatusAndHeaders(
                '200 OK', headers_list, protocol='HTTP/1.0')

            record: ArcWarcRecord = self.writer.create_warc_record(  # type: ignore
                uri=url,
                record_type="response",
                payload=resp.raw,
                http_headers=http_headers,
            )
            
            self.writer.write_record(record=record)  # type: ignore

            self.count += 1

            if self.show_progress:
                overall_count = self.count + 1000 * (self.file_index - 1)
                print(f"{overall_count} of {self.max_pages}")

            if self.count >= self.max_pages:
                self.run[0] = False

            if self.count >= self.save_interval:
                self.file.flush()
                self.rotate_file()

    def rotate_file(self) -> None:
        """Rotate to a new WARC file after reaching the save interval."""
        with self.lock:
            self.file.close()
            self.file_index += 1
            self.count = 0
            self.file = open(file=self._get_filename(), mode="ab")
            self.writer = WARCWriter(filebuf=self.file, gzip=True)

    def close(self) -> None:
        """Close the current WARC file safely."""
        with self.lock:
            self.file.close()
            if self.make_checkpoints:
                self._save_checkpoint()
