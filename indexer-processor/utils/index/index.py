from typing import List
from .index_shard import IndexShard

class Index:
    _size: int
    _shards: List[IndexShard]

    def __init__(self, n: int = 16) -> None:
        self._size = n
        self._shards = [IndexShard() for _ in range(n)]

    def _get_shard_index(self, word: str) -> int:
        return hash(word) % self._size

    def add(self, word: str, docId: int) -> None:
        idx = self._get_shard_index(word)
        self._shards[idx].add(word, docId)

    def contains(self, word: str, docId: int) -> bool:
        idx = self._get_shard_index(word)
        return self._shards[idx].contains(word, docId)
