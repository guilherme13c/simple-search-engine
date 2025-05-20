import os
import json
import threading
import tempfile
import unittest
from .reader import Reader


class TestReader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        self.records = [
            {"id": 1, "text": "hello"},
            {"id": 2, "text": "world"},
            {"id": 3, "text": "!"}
        ]
        for rec in self.records:
            self.tmp.write(json.dumps(rec) + "\n")
        self.tmp.flush()
        self.tmp.close()
        self.path = self.tmp.name

    def tearDown(self):
        os.remove(self.path)

    def test_context_manager_and_eof(self):
        # Using 'with' should open and close automatically
        with Reader(self.path) as rdr:
            out = []
            while True:
                rec = rdr.next_line()
                if rec is None:
                    break
                out.append(rec)
            self.assertEqual(out, self.records)
            self.assertFalse(rdr._file.closed) # type: ignore
        self.assertTrue(rdr._file.closed) # type: ignore

    def test_lazy_opening(self):
        # Calling next_line() before 'with' should still open file
        rdr = Reader(self.path)
        first = rdr.next_line()
        self.assertEqual(first, self.records[0])
        # Continue reading to end
        second = rdr.next_line()
        third = rdr.next_line()
        self.assertEqual(second, self.records[1])
        self.assertEqual(third, self.records[2])
        self.assertIsNone(rdr.next_line())
        rdr.close()
        self.assertTrue(rdr._file.closed) # type: ignore

    def test_close_idempotent(self):
        rdr = Reader(self.path)
        rdr.__enter__()
        rdr.close()
        # second close() should not error
        rdr.close()
        self.assertTrue(rdr._file.closed) # type: ignore
        rdr.__exit__(None, None, None)

    def test_thread_safety(self):
        # In a multithreaded scenario, all records are read exactly once
        with Reader(self.path) as rdr:
            results = []
            lock = threading.Lock()

            def worker():
                while True:
                    rec = rdr.next_line()
                    if rec is None:
                        break
                    with lock:
                        results.append(rec)

            threads = [threading.Thread(target=worker) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # Since there are 3 records, results should match (order may differ)
            self.assertCountEqual(results, self.records)

    def test_empty_file(self):
        # Empty file should immediately return None
        empty = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        empty.close()
        with Reader(empty.name) as rdr:
            self.assertIsNone(rdr.next_line())
        os.remove(empty.name)


if __name__ == '__main__':
    unittest.main()
