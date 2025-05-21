from .index_shard import IndexShard

from typing import List
import json
import os
import shutil
import psutil
import gc
import hashlib


class Index:
    _size: int
    _shards: List[IndexShard | None]
    _path: str
    _available_memory: int
    _op_count: int

    def __init__(self, path: str, available_memory: int = 1024, n: int = 16) -> None:
        shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path)

        self._size = n
        self._shards = [IndexShard() for _ in range(n)]
        self._path = path
        self._available_memory = available_memory
        self._op_count = 0

        for i in range(self._size):
            self._save_shard(i)

    def add(self, word: str, docId: int) -> None:
        idx = self._get_shard_index(word)
        self._load_shard(idx)
        self._shards[idx].add(word, docId)  # type: ignore
        self._flush()

    def contains(self, word: str, docId: int) -> bool:
        idx = self._get_shard_index(word)
        self._load_shard(idx)
        self._flush()
        return self._shards[idx].contains(word, docId)  # type: ignore

    def _flush(self) -> None:
        self._op_count += 1

        if self._op_count % 100 != 0:
            return

        curr_mem = self._memory_usage_megabytes()

        i = 0
        while curr_mem > 0.9 * self._available_memory and i < self._size:
            self._save_shard(i)
            i += 1
        gc.collect()

    def save(self) -> None:
        os.makedirs(self._path, exist_ok=True)

        metadata = {'size': self._size}
        with open(os.path.join(self._path, 'metadata.json'), 'w') as f:
            json.dump(metadata, f)

        for i, shard in enumerate(self._shards):
            if shard is None:
                continue

            shard_path = os.path.join(self._path, f'shard_{i}.pkl')
            shard.save(shard_path)

    @staticmethod
    def load(dir_path: str) -> 'Index':
        with open(os.path.join(dir_path, 'metadata.json')) as f:
            metadata = json.load(f)

        size: int = metadata['size']
        shards: List[None | IndexShard] = [None] * size

        for i in range(size):
            shard_path = os.path.join(dir_path, f'shard_{i}.pkl')
            shards[i] = IndexShard.load(shard_path)

        index = Index(dir_path, n=size)
        index._shards = shards  # type: ignore

        return index

    def _get_shard_index(self, word: str) -> int:
        b = hashlib.sha256(word.encode()).hexdigest()
        return int(b, 16) % self._size

    def _memory_usage_megabytes(self) -> int:
        mem_mb = psutil.Process(os.getpid()).memory_info().rss//(1024*1024)
        return mem_mb

    def _load_shard(self, idx: int) -> None:
        if self._shards[idx] is None:
            self._shards[idx] = IndexShard.load(
                os.path.join(self._path, f'shard_{idx}.pkl'))

    def _save_shard(self, idx: int) -> None:
        if self._shards[idx]:
            self._shards[idx].save(  # type: ignore
                os.path.join(self._path, f'shard_{idx}.pkl')
            )
            self._shards[idx] = None
