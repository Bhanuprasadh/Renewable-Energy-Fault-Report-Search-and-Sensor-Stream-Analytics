"""Exact multi-attribute inverted index for fast set-intersection structured filtering."""
from __future__ import annotations

from typing import Dict, List, Optional, Set
from src.core.models import AssetType, Component, FaultReport, QueryFilter, Severity


class InvertedIndex:
    """Maintains inverted posting lists for exact attribute lookups in O(1) / O(k)."""

    def __init__(self):
        self.by_asset_type: Dict[str, Set[str]] = {}
        self.by_component: Dict[str, Set[str]] = {}
        self.by_severity: Dict[str, Set[str]] = {}
        self.by_metric: Dict[str, Set[str]] = {}
        self.reports_by_id: Dict[str, FaultReport] = {}

    def build(self, reports: List[FaultReport]) -> None:
        """Clear and rebuild inverted posting lists."""
        self.by_asset_type.clear()
        self.by_component.clear()
        self.by_severity.clear()
        self.by_metric.clear()
        self.reports_by_id.clear()

        for r in reports:
            if r.is_deleted:
                continue
            fid = r.fault_id
            self.reports_by_id[fid] = r

            self.by_asset_type.setdefault(r.asset_type.value, set()).add(fid)
            self.by_component.setdefault(r.component.value, set()).add(fid)
            self.by_severity.setdefault(r.severity.value, set()).add(fid)
            self.by_metric.setdefault(r.sensor_range.metric_name, set()).add(fid)

    def filter_ids(self, q_filter: QueryFilter) -> Set[str]:
        """Compute candidate ID set using posting list intersections."""
        candidate_sets: List[Set[str]] = []

        # Asset types filter (union of specified asset types)
        if q_filter.asset_types:
            asset_set: Set[str] = set()
            for at in q_filter.asset_types:
                asset_set.update(self.by_asset_type.get(at.value, set()))
            candidate_sets.append(asset_set)

        # Components filter
        if q_filter.components:
            comp_set: Set[str] = set()
            for c in q_filter.components:
                comp_set.update(self.by_component.get(c.value, set()))
            candidate_sets.append(comp_set)

        # Min severity filter
        if q_filter.min_severity:
            sev_set: Set[str] = set()
            for s in Severity:
                if s.level >= q_filter.min_severity.level:
                    sev_set.update(self.by_severity.get(s.value, set()))
            candidate_sets.append(sev_set)

        # Metric filter
        if q_filter.metric_name:
            candidate_sets.append(self.by_metric.get(q_filter.metric_name, set()))

        if not candidate_sets:
            return set(self.reports_by_id.keys())

        # Intersect posting lists starting with the smallest set
        candidate_sets.sort(key=len)
        result = set(candidate_sets[0])
        for s in candidate_sets[1:]:
            result.intersection_update(s)
            if not result:
                break
        return result

    def filter_records(self, q_filter: QueryFilter) -> List[FaultReport]:
        """Return validated list of FaultReports matching structured criteria."""
        candidate_ids = self.filter_ids(q_filter)
        matched: List[FaultReport] = []

        for fid in candidate_ids:
            r = self.reports_by_id[fid]
            # Secondary range checks that cannot be indexed in discrete categorical lists
            if q_filter.start_time and r.time_interval.end_time < q_filter.start_time:
                continue
            if q_filter.end_time and r.time_interval.start_time > q_filter.end_time:
                continue
            if q_filter.min_sensor_val is not None and r.sensor_range.max_val < q_filter.min_sensor_val:
                continue
            if q_filter.max_sensor_val is not None and r.sensor_range.min_val > q_filter.max_sensor_val:
                continue

            matched.append(r)
        return matched

