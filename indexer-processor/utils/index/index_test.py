import unittest

from .index import Index


class TestIndex(unittest.TestCase):
    def setUp(self):
        self.index = Index(16)

    def test_add_delegates_to_correct_shard(self):
        word = "apple"
        docId = 42
        shard_idx = self.index._get_shard_index(word)

        self.index.add(word, docId)

        self.assertTrue(self.index._shards[shard_idx].contains(word, docId))

    def test_contains_delegates_and_returns(self):
        word = "banana"
        shard_idx = self.index._get_shard_index(word)

        self.assertGreaterEqual(shard_idx, 0)
        self.assertLess(shard_idx, self.index._size)


if __name__ == "__main__":
    unittest.main()
