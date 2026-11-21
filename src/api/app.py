"""FastAPI application exposing search, sensor stream analytics, and audit endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.algorithms.persistence import PersistentFaultStore
from src.core.models import FaultReport, QueryFilter, RangeAggregateResult, SearchResultItem, SensorReading
from src.ingestion.synthetic_data import initialize_datasets_if_missing
from src.services.analytics_service import AnalyticsService
from src.services.search_service import SearchService
from src.services.stream_service import StreamAnalyticsService

INDEX_HTML_PATH = Path(__file__).resolve().parent.parent / "ui" / "index.html"

app = FastAPI(
    title="Renewable Energy Fault Report Search and Sensor Stream Analytics API",
    description="Prototype decision-support API for plant engineers and maintenance planners.",
    version="1.0.0"
)

# In-memory service singletons
search_service = SearchService()
analytics_service = AnalyticsService()
stream_service = StreamAnalyticsService()
persistent_store = PersistentFaultStore()


@app.on_event("startup")
def startup_event():
    _, domain_raw, _ = initialize_datasets_if_missing()
    reports = [FaultReport.model_validate(r) for r in domain_raw]
    for r in reports:
        persistent_store.insert(r, author="SystemInit")
    active_reports = persistent_store.get_current_records()
    search_service.load_and_index_records(active_reports)
    analytics_service.load_reports(active_reports)


@app.get("/", response_class=HTMLResponse)
@app.head("/", response_class=HTMLResponse)
def serve_dashboard():
    """Serve the complete interactive frontend dashboard directly from the application."""
    if INDEX_HTML_PATH.exists():
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>CleanEnergy Analytics Engine Online</h1>")


class SearchRequest(BaseModel):
    query_text: str = ""
    filter_params: QueryFilter = QueryFilter()
    top_k: int = 10
    use_cache: bool = True


class SearchResponse(BaseModel):
    results: List[SearchResultItem]
    latency_ms: float
    cache_hit: bool
    total_matches: int


class RangeQueryRequest(BaseModel):
    start_time: datetime
    end_time: datetime


class RollbackRequest(BaseModel):
    target_version: int
    author: str = "Admin"


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_active_records": len(persistent_store.get_current_records()),
        "current_version": persistent_store.current_version
    }


@app.post("/api/search", response_model=SearchResponse)
def execute_search(req: SearchRequest):
    results, latency, cache_hit = search_service.search(
        query_text=req.query_text,
        q_filter=req.filter_params,
        top_k=req.top_k,
        use_cache=req.use_cache
    )
    return SearchResponse(
        results=results,
        latency_ms=round(latency, 2),
        cache_hit=cache_hit,
        total_matches=len(results)
    )


@app.post("/api/analytics/range")
def execute_range_analytics(req: RangeQueryRequest):
    comparison = analytics_service.query_range_comparison(req.start_time, req.end_time)
    return comparison


@app.post("/api/sensor/stream/step")
def ingest_sensor_reading(reading: SensorReading):
    res = stream_service.process_reading(reading)
    return res


@app.get("/api/sensor/percentiles")
def get_sensor_percentiles():
    return stream_service.get_percentile_comparison()


@app.get("/api/audit/log")
def get_audit_trail():
    return [entry.to_dict() for entry in persistent_store.get_audit_log()]


@app.post("/api/audit/rollback")
def rollback_version(req: RollbackRequest):
    success = persistent_store.rollback_to_version(req.target_version, author=req.author)
    if not success:
        raise HTTPException(status_code=400, detail=f"Version {req.target_version} does not exist.")
    # Refresh active index
    active = persistent_store.get_current_records()
    search_service.load_and_index_records(active)
    analytics_service.load_reports(active)
    return {
        "success": True,
        "restored_version": req.target_version,
        "new_version": persistent_store.current_version,
        "active_records": len(active)
    }

