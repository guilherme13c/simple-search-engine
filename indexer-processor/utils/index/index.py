from .index_shard import IndexShard

from typing import List
import json
import os
import shutil


class Index:
    _size: int
    _shards: List[IndexShard]
    _path: str

    def __init__(self, path: str, n: int = 16) -> None:
        shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path)

        self._size = n
        self._shards = [IndexShard() for _ in range(n)]
        self._path = path

    def _get_shard_index(self, word: str) -> int:
        return hash(word) % self._size

    def add(self, word: str, docId: int) -> None:
        idx = self._get_shard_index(word)
        self._shards[idx].add(word, docId)

    def contains(self, word: str, docId: int) -> bool:
        idx = self._get_shard_index(word)
        return self._shards[idx].contains(word, docId)

    def save(self) -> None:
        os.makedirs(self._path, exist_ok=True)

        metadata = {'size': self._size}
        with open(os.path.join(self._path, 'metadata.json'), 'w') as f:
            json.dump(metadata, f)

        for i, shard in enumerate(self._shards):
            shard_path = os.path.join(self._path, f'shard_{i}.pkl')
            shard.save(shard_path)

    @staticmethod
    def load(dir_path: str) -> 'Index':
        with open(os.path.join(dir_path, 'metadata.json')) as f:
            metadata = json.load(f)

        size: int = metadata['size']
        shards: List[None|IndexShard] = [None] * size

        for i in range(size):
            shard_path = os.path.join(dir_path, f'shard_{i}.pkl')
            shards[i] = IndexShard.load(shard_path)

        index = Index(dir_path, n=size)
        index._shards = shards # type: ignore

        return index
