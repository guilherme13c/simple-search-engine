import os
import numpy as np
import json
from typing import List, Dict, Any
from utils.cli import CliProcessor
from utils.parser import RecordParser


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
        self.inv_file = open(os.path.join(
            index_dir, 'inverted_index.jsonl'), 'r')
        self.page_size: int = page_size

    def _read_postings(self, term: str) -> Dict[int, int]:
        entry = self.lexicon.get(term)
        if not entry:
            return {}
        self.inv_file.seek(entry['offset'])
        line = self.inv_file.readline()
        data = json.loads(line)
        return {int(doc): freq for doc, freq in data['postings'].items()}

    def _score_tfidf(self, term: str, freq: int, doc_len: int) -> float:
        df = self.lexicon[term]['df']
        tf = 1 + np.log(freq)
        idf = np.log((self.N) / df)
        return tf * idf

    def _score_bm25(self, term: str, freq: int, doc_len: int) -> float:
        df = self.lexicon[term]['df']
        idf = np.log((self.N - df + 0.5) / (df + 0.5) + 1)
        num: float = freq * (self.k1 + 1)
        denom: float = freq + self.k1 * \
            (1 - self.b + self.b * doc_len / self.avg_doc_len)
        return idf * (num / denom)

    def process_query(self, query: str) -> Dict:
        toks = self.parser.parse({'title': query, 'text': ''})
        if not toks:
            return {'Query': query, 'Results': []}
        postings_lists: List[Dict[int, int]] = [
            self._read_postings(tok) for tok in toks]
        common_docs = set(postings_lists[0].keys())
        for p in postings_lists[1:]:
            common_docs &= p.keys()
        scores: Dict[int, float] = {}
        for doc in common_docs:
            score = 0.0
            for term in toks:
                freq = postings_lists[toks.index(term)][doc]
                if self.ranker == 'TFIDF':
                    score += self._score_tfidf(term, freq, self.doc_index[doc])
                else:
                    score += self._score_bm25(term, freq, self.doc_index[doc])
            scores[doc] = score
        # top 10
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:self.page_size]
        results = [{'ID': f"{doc:07d}", 'Score': round(
            score, 4)} for doc, score in top]
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
