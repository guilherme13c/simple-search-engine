import threading
import time
import json
import argparse
import nltk
import re
import numpy as np
from typing import TextIO, Optional, Any, Dict, Set, List

nltk.download('stopwords')


class CLI:
    corpusPath: str
    indexDirPath: str
    availableMemory: int

    def __init__(self):
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "-c",
            "--corpus",
            help="path to the corpus jsonl file to be indexed",
            type=str,
            required=False,
            default="corpus.jsonl",
            dest='corpusPath',
        )
        parser.add_argument(
            "-i",
            "--index",
            help="path to the directory where indexes should be created",
            type=str,
            required=False,
            default="indexes",
            dest='indexDirPath',
        )
        parser.add_argument(
            "-m",
            "--memory",
            help="memory available to the indexer in megabytes",
            type=int,
            required=False,
            default=1024,
            dest='availableMemory',
        )

        parser.parse_args(namespace=self)


class Stats:
    begin: float
    indexSize: int
    listCount: int
    sumListLen: int

    def __init__(self):
        self.begin = time.time()
        self.indexSize = 0
        self.listCount = 0
        self.sumListLen = 0

    def print(self):
        self.listCount = max(1, self.listCount)
        print(
            r'{',
            f'\t"Index Size": {None},',
            f'\t"Elapsed Time": {time.time()-self.begin},',
            f'\t"Number of Lists": {self.listCount},',
            f'\t"Average List Size": {self.sumListLen/self.listCount}',
            r'}',
            sep='\n'
        )


class Reader:
    filePath: str
    _lock: threading.Lock
    _file: TextIO | None

    def __init__(self, path: str):
        self.filePath = path
        self._lock = threading.Lock()

    def __enter__(self):
        self._file = open(self.filePath, "r")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._file and not self._file.closed:
            self._file.close()

    def next_line(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            if self._file is None:
                self._file = open(self.filePath, 'r')
            line = self._file.readline()
            if not line:
                return None
            return json.loads(line.strip())

    def close(self):
        with self._lock:
            if self._file and not self._file.closed:
                self._file.close()


class RecordParser:
    _stemmer: nltk.stem.StemmerI
    _stopwords: Set[Any]
    _token_pattern: re.Pattern[str]

    def __init__(self) -> None:
        self._stemmer = nltk.stem.SnowballStemmer('english')
        self._stopwords = set(nltk.corpus.stopwords.words("english"))
        self._token_pattern = re.compile(r"\b\w+\b")

    def parse(self, record: Dict[str, Any]) -> List[str]:
        text: str = record.get('title', '') + ' ' + record.get('text', '')
        text = text.lower()
        tokens: List[str] = self._token_pattern.findall(text)
        processed: List[str] = [
            self._stemmer.stem(tok) for tok in tokens if not tok in self._stopwords
        ]  # type: ignore
        return processed


class LinkedListNode:
    docId: int
    next: LinkedListNode  # type: ignore

    def __init__(self, docId: int = -1, next: LinkedListNode = None):  # type: ignore
        self.docId = docId
        self.next = next


class LinkedList:
    head: LinkedListNode
    skip: Dict[int, LinkedListNode]

    def __init__(self):
        self.head = LinkedListNode()


class IndexShard:
    _id: int
    _filePath: str

    def __init__(self):
        self._id = np.random.randint(100_000, 1_000_000)
        self.filePath = f"{self._id}.idx"

    def add(self, docId: str):
        pass


class Index:
    _shards: List[IndexShard]
    _n: int

    def __init__(self, n=16):
        self._n = n
        self._shards = [IndexShard() for _ in range(self._n)]

    def add(self, docId: str, tokens: List[str]):
        for tok in tokens:
            idx = hash(tok) % self._n
            self._shards[idx].add(docId)


def main():
    args = CLI()
    stats = Stats()

    parser = RecordParser()

    with Reader(args.corpusPath) as reader:
        run = True
        while run:
            record = reader.next_line()
            if not record:
                run = False
                continue

            toks = parser.parse(record)
            print(toks)

    stats.print()


if __name__ == "__main__":
    main()
