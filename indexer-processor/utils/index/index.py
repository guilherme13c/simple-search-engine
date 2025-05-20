from typing import List
from .index_shard import IndexShard


class Index:
    _size: int
    _shards: List[IndexShard]

    def __init__(self, n: int = 16) -> None:
        self._size = n
        self._shards = [IndexShard() for _ in range(n)]

    def _getIdxShardFor(self, word: str):
        return hash(word) % self._size

    def add(self, word: str, docId: int):
        idx = self._getIdxShardFor(word)
        self._shards[idx].add(word, docId)
