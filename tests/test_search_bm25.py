"""Unit tests for Inverted Index, BM25, and Semantic Hybrid Search."""
from src.core.models import AssetType, Component, FaultReport, QueryFilter
from src.ingestion.synthetic_data import CURATED_GOLD_RECORDS
from src.services.search_service import SearchService


def test_hybrid_search_and_validation():
    reports = [FaultReport.model_validate(r) for r in CURATED_GOLD_RECORDS]
    svc = SearchService()
    svc.load_and_index_records(reports)

    # Query targeting gearbox vibration
    q_filter = QueryFilter(asset_types=[AssetType.WIND_TURBINE], components=[Component.GEARBOX])
    results, latency, cache_hit = svc.search(
        query_text="planetary gear pitting bearing vibration",
        q_filter=q_filter,
        top_k=3,
        use_cache=False
    )

    assert len(results) > 0
    top_hit = results[0]
    assert top_hit.fault.component == Component.GEARBOX
    assert top_hit.fault.asset_type == AssetType.WIND_TURBINE
    assert top_hit.validated is True
    assert top_hit.hybrid_score > 0.0

    # Populate cache
    _, _, hit1 = svc.search(
        query_text="planetary gear pitting bearing vibration",
        q_filter=q_filter,
        top_k=3,
        use_cache=True
    )
    assert hit1 is False

    # Repeat with cache enabled -> should hit
    cached_results, _, hit2 = svc.search(
        query_text="planetary gear pitting bearing vibration",
        q_filter=q_filter,
        top_k=3,
        use_cache=True
    )
    assert hit2 is True
    assert cached_results[0].fault.fault_id == top_hit.fault.fault_id
