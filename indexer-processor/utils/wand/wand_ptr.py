import heapq
import numpy as np
from typing import List, Dict, Tuple

class WandTermPointer:
    def __init__(self, term: str, postings: Dict[int, int], upper_bound: float):
        self.term = term
        self.doc_ids = np.array(sorted(postings.keys()), dtype=np.int32)
        self.freqs = np.array([postings[doc_id] for doc_id in self.doc_ids], dtype=np.int32)
        self.index = 0
        self.upper_bound = upper_bound

    def has_next(self) -> bool:
        return self.index < len(self.doc_ids)

    def current_doc(self) -> int:
        return self.doc_ids[self.index] if self.has_next() else np.iinfo(np.int32).max

    def current_freq(self) -> int:
        return self.freqs[self.index] if self.has_next() else 0

    def skip_to(self, doc_id: int):
        while self.has_next() and self.current_doc() < doc_id:
            self.index += 1

    def next(self):
        self.index += 1


def wand_query(pointers: List[WandTermPointer], k: int, score_fn) -> List[Tuple[float, int]]:
    heap: List[Tuple[float, int]] = []  # (score, docId)
    threshold = 0.0

    while True:
        pointers.sort(key=lambda p: p.current_doc())
        pivot = -1
        score_upper = 0.0

        for i, ptr in enumerate(pointers):
            if not ptr.has_next():
                return sorted(heap, reverse=True)
            score_upper += ptr.upper_bound
            if score_upper > threshold:
                pivot = i
                break

        if pivot == -1:
            break

        pivot_doc = pointers[pivot].current_doc()
        if all(ptr.current_doc() == pivot_doc for ptr in pointers[:pivot + 1]):
            doc_id = pivot_doc
            term_freqs = [(ptr.term, ptr.current_freq()) for ptr in pointers if ptr.current_doc() == doc_id]
            for ptr in pointers:
                if ptr.current_doc() == doc_id:
                    ptr.next()
            score = np.sum([score_fn(term, freq, doc_id) for term, freq in term_freqs])
            if score > threshold:
                heapq.heappush(heap, (score, doc_id))
                if len(heap) > k:
                    heapq.heappop(heap)
                threshold = heap[0][0]
        else:
            for ptr in pointers[:pivot]:
                ptr.skip_to(pivot_doc)

    return sorted(heap, reverse=True)

