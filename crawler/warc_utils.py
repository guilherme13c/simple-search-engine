import json
import os
import threading
import time
from typing import TextIO, Set, List
import uuid
from cli.args import Config
from frontier.frontier import Frontier


class WarcControler:
    lock: threading.Lock
    count: int
    file_index: int
    file: TextIO
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
        os.makedirs(config.corpus_dir, exist_ok=True)
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

        self.file = open(os.path.join(
            self.warc_dir, f"crawl_{self.file_index}.warc"), "a", encoding="utf-8")

    def _load_checkpoint(self) -> None:
        """Load the last saved checkpoint (if available)."""
        checkpoint_file = "checkpoint.json"

        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint_data = json.load(f)

                self.file_index = checkpoint_data["file_index"]
                self.count = checkpoint_data["count"]

                for url in checkpoint_data["frontier"]:
                    self.frontier.put(url)

                self.visited.update(checkpoint_data["visited"])

    def _save_checkpoint(self) -> None:
        """Save the current state to a JSON checkpoint."""
        with self.lock:
            checkpoint_data = {
                "file_index": self.file_index,
                "count": self.count,
                "frontier": list(self.frontier.queue.queue),
                "visited": list(self.visited),
                "page_count": self.count
            }

            with open("checkpoint.json", "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=4)

    def _get_filename(self) -> str:
        """Return the current WARC filename."""
        return os.path.join(self.warc_dir, f"crawl_{self.file_index}.warc")

    def write(self, url: str, http_headers: str, content: str) -> None:
        """Thread-safe writing to the WARC file."""
        with self.lock:
            warc_record_id = f"<urn:uuid:{uuid.uuid4()}>"
            warc_date = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            content_length = len(http_headers.encode(
                "utf-8")) + len(content.encode("utf-8"))

            warc_entry = (
                f"WARC/1.0\n"
                f"WARC-Type: response\n"
                f"WARC-Record-ID: {warc_record_id}\n"
                f"WARC-Date: {warc_date}\n"
                f"WARC-Target-URI: {url}\n"
                f"Content-Type: application/http;msgtype=response\n"
                f"Content-Length: {content_length}\n\n"
                f"{http_headers}\n\n"
                f"{content}\n\n"
            )

            self.file.write(warc_entry)
            self.count += 1

            if self.show_progress:
                print(f"{self.count + 1000*(self.file_index-1)} of {self.max_pages}")

            if self.count >= self.max_pages:
                self.run[0] = False  # alter reference

            if self.count >= self.save_interval:
                self.file.flush()
                self.rotate_file()

    def rotate_file(self) -> None:
        """Rotate to a new WARC file after 1000 pages."""
        with self.lock:
            self.file.close()
            self.file_index += 1
            self.count = 0
            self.file = open(self._get_filename(), "a", encoding="utf-8")

    def close(self) -> None:
        """Close the current WARC file safely."""
        with self.lock:
            self.file.close()

            if self.make_checkpoints:
                self._save_checkpoint()
