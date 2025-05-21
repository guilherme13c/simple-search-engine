import os
import numpy as np
import json
from typing import List, Dict, Any
from utils.cli import CliProcessor
from utils.parser import RecordParser
from utils.wand import WandTermPointer, wand_query

class QueryProcessor:
    def __init__(self, index_dir: str, ranker: str, page_size: int) -> None:
        self.index_dir: str = index_dir
        self.ranker: str = ranker.upper()
        with open(os.path.join(index_dir, 'term_lexicon.json'), 'r') as f:
            self.lexicon: Dict[str, Dict] = json.load(f)
        with open(os.path.join(index_dir, 'document_index.json'), 'r') as f:
            self.doc_index: Dict[int, Any] = {
                int(k): v for k, v in json.load(f).items()}
        self.N = len(self.doc_index)
        self.avg_doc_len = sum(self.doc_index.values()) / self.N
        self.parser = RecordParser()
        self.k1 = 1.5
        self.b = 0.75
        self.inv_file = open(os.path.join(index_dir, 'inverted_index.jsonl'), 'r')
        self.page_size: int = page_size

    def _read_postings(self, term: str) -> Dict[int, int]:
        entry = self.lexicon.get(term)
        if not entry:
            return {}
        self.inv_file.seek(entry['offset'])
        line = self.inv_file.readline()
        data = json.loads(line)
        return {int(doc): freq for doc, freq in data['postings'].items()}

    def _score_bm25(self, term: str, freq: int, doc_len: int) -> float:
        df = self.lexicon[term]['df']
        idf = np.log((self.N - df + 0.5) / (df + 0.5) + 1)
        num: float = freq * (self.k1 + 1)
        denom: float = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
        return idf * (num / denom)

    def _score_tfidf(self, term: str, freq: int, doc_len: int) -> float:
        df = self.lexicon[term]['df']
        tf = 1 + np.log(freq)
        idf = np.log((self.N) / df)
        return tf * idf

    def process_query(self, query: str) -> Dict:
        toks = self.parser.parse({'title': query, 'text': ''})
        if not toks:
            return {'Query': query, 'Results': []}

        pointers: List[WandTermPointer] = []
        for term in toks:
            postings: Dict[int, int] = self._read_postings(term)
            if not postings:
                continue
            if self.ranker == 'TFIDF':
                ub = max(self._score_tfidf(term, f, self.doc_index[doc]) for doc, f in postings.items())
            else:
                ub = max(self._score_bm25(term, f, self.doc_index[doc]) for doc, f in postings.items())
            pointers.append(WandTermPointer(term, postings, ub))

        def score_fn(term: str, freq: int, doc_id: int) -> float:
            doc_len = self.doc_index[doc_id]
            return self._score_tfidf(term, freq, doc_len) if self.ranker == 'TFIDF' else self._score_bm25(term, freq, doc_len)

        top_k = wand_query(pointers, self.page_size, score_fn)
        results = [{'ID': f"{doc:07d}", 'Score': round(score, 4)} for score, doc in top_k]
        return {'Query': query, 'Results': results}


def main():
    args = CliProcessor()
    qp = QueryProcessor(args.index_path, args.ranker, args.page_size)
    with open(args.queries_path) as qf:
        for line in qf:
            query = line.strip()
            if not query:
                continue
            output = qp.process_query(query)
            print(json.dumps(output))


if __name__ == '__main__':
    main()

