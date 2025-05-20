import unittest

from .index_shard import IndexShard


class TestIndexShard(unittest.TestCase):
    def setUp(self):
        self.shard = IndexShard()

    def test_empty_shard(self) -> None:
        self.assertEqual(self.shard._size, 0)
        self.assertFalse(self.shard.contains('ligma', 69))

    def test_add_new_word(self) -> None:
        self.shard.add('apple', 1)
        self.assertEqual(self.shard._size, 1)
        self.assertTrue(self.shard.contains('apple', 1))

    def test_add_existing_word(self) -> None:
        self.shard.add('banana', 2)
        self.assertEqual(self.shard._size, 1)
        self.shard.add('banana', 3)
        self.assertEqual(self.shard._size, 1)

    def test_multiple_words(self) -> None:
        pairs = [('cat', 1), ('dog', 2), ('cat', 3), ('mouse', 4)]
        for word, docId in pairs:
            self.shard.add(word, docId)
        self.assertEqual(self.shard._size, 3)

    def test_contains_empty(self) -> None:
        self.assertFalse(self.shard.contains("apple", 3))
        self.assertFalse(self.shard.contains("pear", 9))

    def test_contains(self) -> None:
        self.shard.add("mango", 24)

        self.assertTrue(self.shard.contains("mango", 24))


if __name__ == '__main__':
    unittest.main()
