"""Baseline linear scan search and filter implementation (O(N) unindexed)."""
from __future__ import annotations

import time
from typing import List, Tuple
from src.core.models import FaultReport, QueryFilter, SearchResultItem


class LinearScanBaseline:
    """Brute-force O(N) unindexed search and structured filtering."""

    def __init__(self, records: List[FaultReport]):
        self.records = records

    def filter_records(self, q_filter: QueryFilter) -> List[FaultReport]:
        """Linear predicate filter over all records without indexes."""
        matches: List[FaultReport] = []
        for r in self.records:
            if r.is_deleted:
                continue

            # Asset type filter
            if q_filter.asset_types and r.asset_type not in q_filter.asset_types:
                continue

            # Component filter
            if q_filter.components and r.component not in q_filter.components:
                continue

            # Minimum severity filter
            if q_filter.min_severity and r.severity.level < q_filter.min_severity.level:
                continue

            # Time range filter (interval overlap)
            if q_filter.start_time and r.time_interval.end_time < q_filter.start_time:
                continue
            if q_filter.end_time and r.time_interval.start_time > q_filter.end_time:
                continue

            # Sensor value filter
            if q_filter.metric_name and r.sensor_range.metric_name != q_filter.metric_name:
                continue
            if q_filter.min_sensor_val is not None and r.sensor_range.max_val < q_filter.min_sensor_val:
                continue
            if q_filter.max_sensor_val is not None and r.sensor_range.min_val > q_filter.max_sensor_val:
                continue

            matches.append(r)
        return matches

    def search_keyword(self, query_text: str, q_filter: QueryFilter, top_k: int = 10) -> Tuple[List[SearchResultItem], float]:
        """Naive unindexed substring / token match scan with timing."""
        start_t = time.perf_counter()
        filtered = self.filter_records(q_filter)
        q_tokens = [tok.lower() for tok in query_text.strip().split() if tok]

        scored: List[SearchResultItem] = []
        for r in filtered:
            text = f"{r.fault_description} {r.maintenance_notes} {r.root_cause_category}".lower()
            token_matches = sum(1 for tok in q_tokens if tok in text)
            if q_tokens and token_matches == 0:
                continue

            score = float(token_matches)
            scored.append(
                SearchResultItem(
                    fault=r,
                    bm25_score=score,
                    semantic_score=0.0,
                    hybrid_score=score,
                    match_explanation={"method": "LinearSubstringScan", "tokens_matched": token_matches},
                    validated=True
                )
            )

        scored.sort(key=lambda x: x.hybrid_score, reverse=True)
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        return scored[:top_k], elapsed_ms

