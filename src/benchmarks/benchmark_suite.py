"""Comprehensive automated benchmarking suite for all four members' algorithms."""
from __future__ import annotations

import json
import math
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
import numpy as np

from src.algorithms.fenwick import TimeAggregateIndex
from src.algorithms.tdigest import TDigest
from src.baselines.exact_aggregates import ExactAggregatesBaseline
from src.baselines.exact_percentiles import ExactPercentilesBaseline
from src.baselines.linear_scan import LinearScanBaseline
from src.core.models import FaultReport, QueryFilter
from src.core.profiling import benchmark_callable, get_hardware_telemetry
from src.ingestion.synthetic_data import CURATED_SAMPLE_QUERIES, generate_synthetic_domain_records
from src.services.search_service import SearchService


def compute_mrr_and_ndcg(
    search_service: SearchService,
    sample_queries: List[Dict[str, Any]],
    k: int = 5
) -> Dict[str, float]:
    """Calculate Mean Reciprocal Rank (MRR) and Normalized Discounted Cumulative Gain (NDCG@k)."""
    reciprocal_ranks: List[float] = []
    ndcgs: List[float] = []

    for sq in sample_queries:
        q_text = sq["query_text"]
        q_filter = QueryFilter.model_validate(sq.get("structured_filter", {}))
        gold_ids = set(sq["relevant_fault_ids"])

        results, _, _ = search_service.search(q_text, q_filter, top_k=k, use_cache=False)
        retrieved_ids = [item.fault.fault_id for item in results]

        # Reciprocal Rank (RR)
        rr = 0.0
        for rank_idx, fid in enumerate(retrieved_ids, start=1):
            if fid in gold_ids:
                rr = 1.0 / rank_idx
                break
        reciprocal_ranks.append(rr)

        # DCG@k and IDCG@k
        dcg = 0.0
        for rank_idx, fid in enumerate(retrieved_ids, start=1):
            rel = 1.0 if fid in gold_ids else 0.0
            dcg += rel / math.log2(rank_idx + 1)

        idcg = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(gold_ids), k) + 1))
        ndcg = (dcg / idcg) if idcg > 0 else 0.0
        ndcgs.append(ndcg)

    return {
        "mrr": float(np.mean(reciprocal_ranks)) if reciprocal_ranks else 0.0,
        f"ndcg@{k}": float(np.mean(ndcgs)) if ndcgs else 0.0
    }


def run_full_benchmark_suite(
    sizes: List[int] = [100, 500, 1000],
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Execute evaluation across multiple dataset sizes for Member 1-4 deliverables."""
    telemetry = get_hardware_telemetry()
    timestamp = datetime.now(timezone.utc).isoformat()

    benchmark_results: Dict[str, Any] = {
        "metadata": {
            "timestamp": timestamp,
            "telemetry": telemetry,
            "evaluated_sizes": sizes
        },
        "search_scaling": {},
        "fenwick_vs_baseline": {},
        "tdigest_accuracy_and_memory": {},
        "ranking_quality": {}
    }

    # Generate the largest dataset once
    max_size = max(sizes)
    all_raw = generate_synthetic_domain_records(num_records=max_size, seed=42)
    all_reports = [FaultReport.model_validate(r) for r in all_raw]

    # 1. Search & Filter Benchmarks across 3 dataset sizes
    for sz in sizes:
        subset = all_reports[:sz]
        linear_scanner = LinearScanBaseline(subset)
        search_svc = SearchService()

        # Build index time
        t0 = time.perf_counter()
        search_svc.load_and_index_records(subset)
        build_time_ms = (time.perf_counter() - t0) * 1000.0

        test_filter = QueryFilter(min_severity="MEDIUM")
        test_query = "bearing vibration temperature"

        # Linear scan latency
        linear_perf = benchmark_callable(
            lambda: linear_scanner.search_keyword(test_query, test_filter, top_k=10),
            warmup_runs=2,
            repeat_runs=10
        )

        # Indexed Search (Cold / Uncached)
        indexed_perf = benchmark_callable(
            lambda: search_svc.search(test_query, test_filter, top_k=10, use_cache=False),
            warmup_runs=2,
            repeat_runs=10
        )

        # Cached Search
        search_svc.search(test_query, test_filter, top_k=10, use_cache=True)
        cached_perf = benchmark_callable(
            lambda: search_svc.search(test_query, test_filter, top_k=10, use_cache=True),
            warmup_runs=2,
            repeat_runs=15
        )

        benchmark_results["search_scaling"][f"size_{sz}"] = {
            "build_cost_ms": round(build_time_ms, 2),
            "linear_baseline": linear_perf,
            "indexed_hybrid": indexed_perf,
            "cached": cached_perf,
            "speedup_ratio": round(linear_perf["median_latency_ms"] / max(0.001, indexed_perf["median_latency_ms"]), 2)
        }

    # 2. Fenwick Tree vs Baseline Range Scan across 3 dataset sizes
    for sz in sizes:
        subset = all_reports[:sz]
        min_t = min(r.time_interval.start_time for r in subset)
        max_t = max(r.time_interval.end_time for r in subset)

        fenwick_idx = TimeAggregateIndex(min_time=min_t, max_time=max_t, bucket_seconds=3600)
        fenwick_idx.bulk_load(subset)
        baseline_agg = ExactAggregatesBaseline(subset)

        q_start = min_t + timedelta(days=5)
        q_end = q_start + timedelta(days=20)

        fenwick_perf = benchmark_callable(
            lambda: fenwick_idx.query_range(q_start, q_end),
            warmup_runs=5,
            repeat_runs=20
        )
        baseline_perf = benchmark_callable(
            lambda: baseline_agg.query_range(q_start, q_end),
            warmup_runs=5,
            repeat_runs=20
        )

        # Oracle correctness verification
        b_start, b_end = fenwick_idx.get_bucket_bounds(q_start, q_end)
        f_res = fenwick_idx.query_range(q_start, q_end)
        b_res = baseline_agg.query_range(b_start, b_end)
        verified = (f_res.total_faults == b_res.total_faults) and (abs(f_res.total_power_loss_kwh - b_res.total_power_loss_kwh) < 0.1)

        benchmark_results["fenwick_vs_baseline"][f"size_{sz}"] = {
            "fenwick_latency": fenwick_perf,
            "baseline_latency": baseline_perf,
            "speedup_ratio": round(baseline_perf["median_latency_ms"] / max(0.0001, fenwick_perf["median_latency_ms"]), 2),
            "exact_oracle_match": verified
        }

    # 3. t-Digest Accuracy and Memory across parameter sweeps
    stream_samples = [np.random.normal(loc=3.5, scale=0.8) for _ in range(5000)]
    exact_tracker = ExactPercentilesBaseline()
    for s in stream_samples:
        exact_tracker.update(s)
    exact_p = exact_tracker.get_percentiles_summary()

    for delta in [25.0, 50.0, 100.0, 200.0]:
        td = TDigest(delta=delta)
        for s in stream_samples:
            td.update(s)
        td_p = td.get_percentiles_summary()

        errors = {}
        for p in ["p50", "p90", "p95", "p99"]:
            err = abs(td_p[p] - exact_p[p])
            rel = (err / exact_p[p]) * 100.0 if exact_p[p] != 0 else 0.0
            errors[p] = {"abs_err": round(err, 4), "rel_err_pct": round(rel, 2)}

        benchmark_results["tdigest_accuracy_and_memory"][f"delta_{int(delta)}"] = {
            "compression_delta": delta,
            "exact_percentiles": exact_p,
            "tdigest_percentiles": td_p,
            "errors": errors,
            "tdigest_memory_bytes": td.memory_bytes(),
            "exact_memory_bytes": exact_tracker.memory_bytes(),
            "memory_reduction_ratio": round(exact_tracker.memory_bytes() / max(1, td.memory_bytes()), 1)
        }

    # 4. Retrieval Ranking Evaluation (MRR & NDCG)
    eval_svc = SearchService()
    eval_svc.load_and_index_records(all_reports[:1000])
    ranking_metrics = compute_mrr_and_ndcg(eval_svc, CURATED_SAMPLE_QUERIES, k=5)
    benchmark_results["ranking_quality"] = ranking_metrics

    # Save to disk if requested
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(benchmark_results, f, indent=2)

    return benchmark_results


if __name__ == "__main__":
    out_file = Path(__file__).resolve().parent.parent.parent / "data" / "benchmark_report.json"
    print("Executing full benchmark suite...")
    report = run_full_benchmark_suite(sizes=[100, 500, 1000], output_path=out_file)
    print(f"Benchmark finished and saved to {out_file}")
    print(json.dumps(report["ranking_quality"], indent=2))
