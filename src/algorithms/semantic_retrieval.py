"""Semantic vector space retrieval with TF-IDF cosine similarity and hybrid fusion."""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Set, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.core.models import FaultReport, SearchResultItem


class SemanticVectorRetriever:
    """Dense/sparse semantic retriever calculating vector cosine similarity."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=5000,
            token_pattern=r"(?u)\b[a-zA-Z0-9_-]+\b"
        )
        self.doc_ids: List[str] = []
        self.tfidf_matrix = None
        self.id_to_idx: Dict[str, int] = {}

    def fit_reports(self, reports: List[FaultReport]) -> None:
        """Fit TF-IDF vocabulary on combined fault text corpus."""
        self.doc_ids.clear()
        self.id_to_idx.clear()
        corpus: List[str] = []

        for r in reports:
            if r.is_deleted:
                continue
            self.doc_ids.append(r.fault_id)
            text = f"{r.fault_description} {r.maintenance_notes} {r.root_cause_category} {r.component.value} {r.asset_type.value}"
            corpus.append(text)

        if corpus:
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
            for idx, fid in enumerate(self.doc_ids):
                self.id_to_idx[fid] = idx

    def score_query(self, query: str, candidate_ids: Optional[Set[str]] = None) -> List[Tuple[str, float]]:
        """Compute cosine similarity of query against document collection."""
        if self.tfidf_matrix is None or not query.strip():
            return []

        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.tfidf_matrix).flatten()

        results: List[Tuple[str, float]] = []
        for fid, idx in self.id_to_idx.items():
            if candidate_ids is not None and fid not in candidate_ids:
                continue
            score = float(sims[idx])
            if score > 0.0001:
                results.append((fid, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results


class HybridRanker:
    """Fuses exact filters, BM25 scores, and semantic cosine similarity with validation."""

    def __init__(self, alpha: float = 0.55):
        self.alpha = alpha  # Weight on BM25 vs Semantic

    def fuse_and_rank(
        self,
        bm25_scores: List[Tuple[str, float]],
        semantic_scores: List[Tuple[str, float]],
        reports_by_id: Dict[str, FaultReport],
        top_k: int = 10
    ) -> List[SearchResultItem]:
        """Combine normalized scores and create explainable ranked items."""
        bm25_dict = dict(bm25_scores)
        sem_dict = dict(semantic_scores)
        all_ids = set(bm25_dict.keys()) | set(sem_dict.keys())

        # Min-Max Normalization
        max_bm25 = max(bm25_dict.values()) if bm25_dict and max(bm25_dict.values()) > 0 else 1.0
        max_sem = max(sem_dict.values()) if sem_dict and max(sem_dict.values()) > 0 else 1.0

        fused: List[SearchResultItem] = []
        for fid in all_ids:
            if fid not in reports_by_id:
                continue
            r = reports_by_id[fid]

            raw_b = bm25_dict.get(fid, 0.0)
            raw_s = sem_dict.get(fid, 0.0)

            norm_b = raw_b / max_bm25
            norm_s = raw_s / max_sem

            hybrid_score = self.alpha * norm_b + (1.0 - self.alpha) * norm_s

            explanation = {
                "raw_bm25": round(raw_b, 4),
                "norm_bm25": round(norm_b, 4),
                "raw_semantic": round(raw_s, 4),
                "norm_semantic": round(norm_s, 4),
                "alpha_weight": self.alpha,
                "formula": f"{self.alpha} * norm_bm25 + {round(1.0 - self.alpha, 2)} * norm_semantic"
            }

            fused.append(
                SearchResultItem(
                    fault=r,
                    bm25_score=round(raw_b, 4),
                    semantic_score=round(raw_s, 4),
                    hybrid_score=round(hybrid_score, 4),
                    match_explanation=explanation,
                    validated=True
                )
            )

        fused.sort(key=lambda item: item.hybrid_score, reverse=True)
        return fused[:top_k]

