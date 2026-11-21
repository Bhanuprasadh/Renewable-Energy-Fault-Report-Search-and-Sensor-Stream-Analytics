"""BM25 (Best Matching 25) probabilistic relevance ranking engine."""
from __future__ import annotations

import math
import re
from typing import Dict, List, Set, Tuple
from src.core.models import FaultReport

STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how",
    "i", "if", "in", "into", "is", "isn't", "it", "its", "itself", "me", "more", "most", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves",
    "out", "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those", "through", "to",
    "too", "under", "until", "up", "very", "was", "wasn't", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric terms excluding stopwords."""
    tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


class BM25Index:
    """Okapi BM25 ranking algorithm with inverted index term posting lists."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_ids: List[str] = []
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0.0
        self.doc_term_freqs: Dict[str, Dict[str, int]] = {}
        self.inverted_index: Dict[str, Dict[str, int]] = {}
        self.idf: Dict[str, float] = {}
        self.num_docs: int = 0

    def index_reports(self, reports: List[FaultReport]) -> None:
        """Build BM25 index over fault descriptions, maintenance notes, and root causes."""
        self.doc_ids.clear()
        self.doc_lengths.clear()
        self.doc_term_freqs.clear()
        self.inverted_index.clear()
        self.idf.clear()

        total_length = 0

        for r in reports:
            if r.is_deleted:
                continue
            doc_id = r.fault_id
            corpus_text = f"{r.fault_description} {r.maintenance_notes} {r.root_cause_category} {r.component.value} {r.asset_type.value}"
            tokens = tokenize(corpus_text)

            self.doc_ids.append(doc_id)
            d_len = len(tokens)
            self.doc_lengths[doc_id] = d_len
            total_length += d_len

            # Term frequencies within this document
            tf_dict: Dict[str, int] = {}
            for t in tokens:
                tf_dict[t] = tf_dict.get(t, 0) + 1
            self.doc_term_freqs[doc_id] = tf_dict

            # Update inverted index
            for t, count in tf_dict.items():
                if t not in self.inverted_index:
                    self.inverted_index[t] = {}
                self.inverted_index[t][doc_id] = count

        self.num_docs = len(self.doc_ids)
        self.avg_doc_length = (total_length / self.num_docs) if self.num_docs > 0 else 0.0

        # Compute IDF for all vocabulary terms
        for term, postings in self.inverted_index.items():
            df = len(postings)
            # Standard Lucene/BM25 IDF formula
            self.idf[term] = math.log(((self.num_docs - df + 0.5) / (df + 0.5)) + 1.0)

    def score_query(self, query: str, candidate_ids: Optional[Set[str]] = None) -> List[Tuple[str, float]]:
        """Score all matching documents for a query. Optionally restrict to candidate_ids."""
        q_tokens = tokenize(query)
        if not q_tokens or self.num_docs == 0:
            return []

        scores: Dict[str, float] = {}

        for term in q_tokens:
            if term not in self.inverted_index:
                continue
            term_idf = self.idf[term]
            postings = self.inverted_index[term]

            for doc_id, tf in postings.items():
                if candidate_ids is not None and doc_id not in candidate_ids:
                    continue

                d_len = self.doc_lengths[doc_id]
                # BM25 term weight
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (d_len / self.avg_doc_length))
                term_score = term_idf * (numerator / denominator)

                scores[doc_id] = scores.get(doc_id, 0.0) + term_score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked

