"""Unified Search Service combining exact filtering, BM25, semantic vector retrieval, and caching."""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple

from src.algorithms.bm25 import BM25Index
from src.algorithms.cache import LRUTTLCache
from src.algorithms.inverted_index import InvertedIndex
from src.algorithms.semantic_retrieval import HybridRanker, SemanticVectorRetriever
from src.core.config import AlgorithmConfig
from src.core.models import FaultReport, QueryFilter, SearchResultItem
from src.ingestion.validator import DataValidator


class SearchService:
    """Orchestrates structured filtering, BM25 keyword matching, semantic reranking, and caching."""

    def __init__(self, config: Optional[AlgorithmConfig] = None):
        self.config = config or AlgorithmConfig()
        self.inverted_index = InvertedIndex()
        self.bm25_index = BM25Index(k1=self.config.BM25_K1, b=self.config.BM25_B)
        self.semantic_retriever = SemanticVectorRetriever()
        self.hybrid_ranker = HybridRanker(alpha=self.config.HYBRID_ALPHA)
        self.cache = LRUTTLCache(capacity=self.config.CACHE_CAPACITY, ttl_seconds=self.config.CACHE_TTL_SECONDS)
        self.validator = DataValidator()
        self.reports: List[FaultReport] = []

    def load_and_index_records(self, reports: List[FaultReport]) -> None:
        """Initialize or refresh all indexes from reports list."""
        self.reports = reports
        self.inverted_index.build(reports)
        self.bm25_index.index_reports(reports)
        self.semantic_retriever.fit_reports(reports)
        self.cache.clear()

    def _make_cache_key(self, query: str, q_filter: QueryFilter, top_k: int) -> str:
        filter_dict = q_filter.model_dump(mode="json")
        return f"SEARCH:{query.strip().lower()}:{json.dumps(filter_dict, sort_keys=True)}:{top_k}"

    def search(
        self,
        query_text: str,
        q_filter: QueryFilter,
        top_k: int = 10,
        use_cache: bool = True
    ) -> Tuple[List[SearchResultItem], float, bool]:
        """Execute full hybrid search pipeline with timing and cache check."""
        start_t = time.perf_counter()
        cache_key = self._make_cache_key(query_text, q_filter, top_k)

        if use_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                return cached, elapsed_ms, True

        # Step 1: Exact structured filtering (Member 2 Inverted Index)
        candidate_ids = self.inverted_index.filter_ids(q_filter)
        if not candidate_ids:
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            return [], elapsed_ms, False

        # If query text is empty, return exact filtered records without text scoring
        if not query_text.strip():
            matched_records = self.inverted_index.filter_records(q_filter)
            results = [
                SearchResultItem(
                    fault=r,
                    bm25_score=1.0,
                    semantic_score=1.0,
                    hybrid_score=1.0,
                    match_explanation={"method": "ExactFilterOnly", "matched_filter": True},
                    validated=True
                )
                for r in matched_records[:top_k]
            ]
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            if use_cache:
                self.cache.put(cache_key, results)
            return results, elapsed_ms, False

        # Step 2: BM25 text relevance scoring over candidates
        bm25_scores = self.bm25_index.score_query(query_text, candidate_ids=candidate_ids)

        # Step 3: Semantic vector similarity scoring over candidates
        semantic_scores = self.semantic_retriever.score_query(query_text, candidate_ids=candidate_ids)

        # Step 4: Hybrid fusion and ranking
        ranked_candidates = self.hybrid_ranker.fuse_and_rank(
            bm25_scores=bm25_scores,
            semantic_scores=semantic_scores,
            reports_by_id=self.inverted_index.reports_by_id,
            top_k=top_k * 2
        )

        # Step 5: Strict Validation Oracle Layer (guarantees approximate candidates are validated)
        validated_results: List[SearchResultItem] = []
        for item in ranked_candidates:
            # Re-verify structured predicates on item
            r = item.fault
            if q_filter.start_time and r.time_interval.end_time < q_filter.start_time:
                continue
            if q_filter.end_time and r.time_interval.start_time > q_filter.end_time:
                continue
            if q_filter.min_sensor_val is not None and r.sensor_range.max_val < q_filter.min_sensor_val:
                continue
            if q_filter.max_sensor_val is not None and r.sensor_range.min_val > q_filter.max_sensor_val:
                continue

            item.validated = True
            validated_results.append(item)
            if len(validated_results) >= top_k:
                break

        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        if use_cache:
            self.cache.put(cache_key, validated_results)
        return validated_results, elapsed_ms, False

