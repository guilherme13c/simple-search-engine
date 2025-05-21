import unittest
import tempfile
import shutil

from .index import Index


class TestIndex(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.index = Index(path=self.test_dir, n=16)

    def tearDown(self) -> None:
        try:
            shutil.rmtree(self.test_dir)
        except:
            pass

    def test_add_delegates_to_correct_shard(self) -> None:
        word = "apple"
        docId = 42
        shard_idx = self.index._get_shard_index(word)

        self.index.add(word, docId)

        self.assertTrue(self.index._shards[shard_idx].contains(word, docId))

    def test_contains_delegates_and_returns(self) -> None:
        word = "banana"
        docId = 101
        self.index.add(word, docId)

        self.assertTrue(self.index.contains(word, docId))

    def test_save_and_load(self) -> None:
        word = "cherry"
        docId = 99
        self.index.add(word, docId)

        self.index.save()

        loaded_index = Index.load(self.test_dir)

        self.assertTrue(loaded_index.contains(word, docId))
        self.assertEqual(loaded_index._size, 16)
        self.assertEqual(len(loaded_index._shards), 16)


if __name__ == "__main__":
    unittest.main()
