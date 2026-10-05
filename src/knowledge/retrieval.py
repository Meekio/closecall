"""
Lightweight TF-IDF + cosine similarity retrieval over the styling
knowledge base. No external ML libraries or API calls required —
this is a deliberate choice for prototype reliability (see report).
"""

from __future__ import annotations

import math
import re
from collections import Counter

from src.knowledge.styling_kb import STYLING_KB


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


class _TfidfIndex:
    def __init__(self, documents: list[dict]):
        self.documents = documents
        self.doc_tokens = [_tokenize(d["text"]) for d in documents]
        self.doc_count = len(documents)

        # Document frequency per term
        df = Counter()
        for tokens in self.doc_tokens:
            for term in set(tokens):
                df[term] += 1
        self.idf = {
            term: math.log((1 + self.doc_count) / (1 + freq)) + 1
            for term, freq in df.items()
        }

        # Precompute TF-IDF vectors for each document
        self.doc_vectors = [self._vectorize(tokens) for tokens in self.doc_tokens]

    def _vectorize(self, tokens: list[str]) -> dict[str, float]:
        tf = Counter(tokens)
        total = len(tokens) or 1
        return {
            term: (count / total) * self.idf.get(term, 0.0)
            for term, count in tf.items()
        }

    @staticmethod
    def _cosine(v1: dict[str, float], v2: dict[str, float]) -> float:
        common = set(v1) & set(v2)
        if not common:
            return 0.0
        dot = sum(v1[t] * v2[t] for t in common)
        norm1 = math.sqrt(sum(v * v for v in v1.values()))
        norm2 = math.sqrt(sum(v * v for v in v2.values()))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def query(self, text: str, top_k: int = 3) -> list[dict]:
        q_tokens = _tokenize(text)
        q_vector = self._vectorize(q_tokens)
        scored = [
            {**self.documents[i], "score": round(self._cosine(q_vector, self.doc_vectors[i]), 4)}
            for i in range(self.doc_count)
        ]
        scored.sort(key=lambda d: d["score"], reverse=True)
        return scored[:top_k]


_index = _TfidfIndex(STYLING_KB)


def retrieve_styling_guidance(query: str, top_k: int = 3) -> list[dict]:
    """Public entry point used by the agent tool wrapper."""
    return _index.query(query, top_k=top_k)