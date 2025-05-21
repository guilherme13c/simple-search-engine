import os
import json
import time
import psutil
import multiprocessing
from typing import Dict, Tuple, Any
from utils.cli import CliIndexer
from utils.reader import Reader
from utils.parser import RecordParser

tmp_dir = ".tmp_partial"


class Indexer:
    def __init__(self, corpus_path: str, index_dir: str, mem_limit_mb: int, workers: int | None = None):
        self.corpus_path = corpus_path
        self.index_dir = index_dir
        self.mem_limit = mem_limit_mb * 1024 * 1024
        self.parser = RecordParser()
        self.partial_count = 0
        self.in_memory: Dict[str, Dict[int, int]] = {}
        self.doc_index: Dict[int, int] = {}
        self.workers = workers or multiprocessing.cpu_count()
        os.makedirs(tmp_dir, exist_ok=True)
        os.makedirs(self.index_dir, exist_ok=True)

    @staticmethod
    def _parse_record(args: Tuple[Dict[str, Any], Any]) -> Tuple[int, Dict[str, int]]:
        rec, parser = args
        doc_id = int(rec.get('id', -1))
        toks = parser.parse(rec)
        freqs: Dict[str, int] = {}
        for tok in toks:
            freqs[tok] = freqs.get(tok, 0) + 1
        return doc_id, freqs

    def _check_memory(self) -> bool:
        rss = psutil.Process(os.getpid()).memory_info().rss
        return rss > 0.9 * self.mem_limit

    def _flush_partial(self):
        """Write the in-memory index to a partial file and clear it."""
        path = os.path.join(tmp_dir, f"partial_{self.partial_count}.jsonl")
        with open(path, 'w') as f:
            for term, postings in sorted(self.in_memory.items()):
                entry = {"term": term, "postings": postings}
                f.write(json.dumps(entry) + "\n")
        self.in_memory.clear()
        self.partial_count += 1
        print(f"Flushed partial index #{self.partial_count} to disk.")

    def build(self, batch_size: int = 1000) -> None:
        start = time.time()
        count = 0
        pool = multiprocessing.Pool(self.workers)
        try:
            with Reader(self.corpus_path) as reader:
                while True:
                    batch = []
                    for _ in range(batch_size):
                        rec = reader.next_line()
                        if rec is None:
                            break
                        batch.append((rec, self.parser))
                    if not batch:
                        break
                    for doc_id, freqs in pool.map(Indexer._parse_record, batch):
                        self.doc_index[doc_id] = sum(freqs.values())
                        for term, freq in freqs.items():
                            postings = self.in_memory.setdefault(term, {})
                            postings[doc_id] = freq
                        count += 1
                    if count % (batch_size * 10) == 0:
                        print(f"Processed {count} docs...")
                    if self._check_memory():
                        self._flush_partial()
            if self.in_memory:
                self._flush_partial()
        finally:
            pool.close()
            pool.join()

        self._merge_partials()
        elapsed = time.time() - start
        size_mb, num_terms, avg_list = self._gather_stats()
        stats = {
            "Index Size": size_mb,
            "Elapsed Time": int(elapsed),
            "Number of Lists": num_terms,
            "Average List Size": round(avg_list, 2)
        }
        print(json.dumps(stats))

    def _merge_partials(self) -> None:
        partials = sorted(os.listdir(tmp_dir))
        merged: Dict[str, Dict[int, int]] = {}
        for fname in partials:
            with open(os.path.join(tmp_dir, fname)) as f:
                for line in f:
                    entry = json.loads(line)
                    term = entry['term']
                    for doc, freq in entry['postings'].items():
                        merged.setdefault(term, {})[int(doc)] = freq
        inv_path = os.path.join(self.index_dir, 'inverted_index.jsonl')
        lexicon: Dict[str, Dict] = {}
        with open(inv_path, 'w') as inv_f:
            for term, postings in sorted(merged.items()):
                offset = inv_f.tell()
                inv_f.write(json.dumps(
                    {"term": term, "postings": postings}) + "\n")
                length = inv_f.tell() - offset
                lexicon[term] = {
                    "df": len(postings), "offset": offset, "length": length}
        with open(os.path.join(self.index_dir, 'term_lexicon.json'), 'w') as lex_f:
            json.dump(lexicon, lex_f)
        with open(os.path.join(self.index_dir, 'document_index.json'), 'w') as doc_f:
            json.dump(self.doc_index, doc_f)
        for fname in partials:
            os.remove(os.path.join(tmp_dir, fname))
        os.rmdir(tmp_dir)

    def _gather_stats(self) -> Tuple[int, int, float]:
        total = 0
        for file in os.listdir(self.index_dir):
            total += os.path.getsize(os.path.join(self.index_dir, file))
        size_mb = total // (1024 * 1024)
        lex = json.load(
            open(os.path.join(self.index_dir, 'term_lexicon.json')))
        num_terms = len(lex)
        total_postings = sum(v['df'] for v in lex.values())
        avg_list = total_postings / num_terms if num_terms else 0.0
        return size_mb, num_terms, avg_list


def main() -> None:
    args = CliIndexer()
    workers = args.workers
    indexer = Indexer(args.corpus_path, args.index_dir,
                      args.available_memory, workers)
    indexer.build()


if __name__ == '__main__':
    main()
