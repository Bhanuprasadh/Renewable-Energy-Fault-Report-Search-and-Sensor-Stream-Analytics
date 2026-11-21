# Syllabus Mapping & Academic Topic Traceability

This project maps directly to Advanced Data Structures & Algorithms course outcomes and lecture modules:

| Course Outcome | Relevant Topics & Algorithmic Modules | Codebase Implementation |
|---|---|---|
| **CO2: Advanced Search & Prefix Structures** (Sessions 7–8) | Binary Indexed Trees (Fenwick Trees), range queries, discretization, cumulative frequency analysis. | `src/algorithms/fenwick.py`<br>`src/services/analytics_service.py` |
| **CO3: Persistence & Inverted File Structures** (Sessions 16, 19–24) | Persistent data structures, copy-on-write versioning, audit logging, multi-attribute inverted indexes. | `src/algorithms/persistence.py`<br>`src/algorithms/inverted_index.py` |
| **CO4: Probabilistic Summaries & Data Sketches** (Sessions 25–28) | Quantile sketches, t-Digest centroid clustering, error-bounded streaming estimation, space-accuracy trade-offs. | `src/algorithms/tdigest.py`<br>`src/baselines/exact_percentiles.py` |
| **CO5: Streaming Analytics & Concept Drift** (Sessions 29–30) | Streaming event replay, Page-Hinkley test, CUSUM drift detection, adaptive windowing, out-of-order handling. | `src/algorithms/drift_detector.py`<br>`src/ingestion/stream_generator.py` |
| **CO6: Information Retrieval & Hybrid Ranking** (Sessions 31–33) | Inverted index scoring, Okapi BM25 ranking, vector space model, TF-IDF cosine similarity, reciprocal rank fusion, evaluation via MRR and NDCG. | `src/algorithms/bm25.py`<br>`src/algorithms/semantic_retrieval.py`<br>`src/benchmarks/benchmark_suite.py` |

---

## Acceptance Demonstration Checklist

1. **One Correct Baseline Query**:
   - `LinearScanBaseline.search_keyword()` returns matches via sequential scan.
   - `ExactAggregatesBaseline.query_range()` calculates brute-force sum and count.
2. **One Indexed / Approximate Query**:
   - `TimeAggregateIndex.query_range()` executes in $O(\log B)$ with zero error compared to oracle.
   - `SearchService.search()` performs pre-filtering on Inverted Index + BM25 + Semantic Cosine.
3. **Stream Replay with Drift**:
   - `SensorStreamGenerator` emits continuous sensor telemetry.
   - `PageHinkleyDriftDetector` and `CUSUMDriftDetector` dynamically trigger alarms upon degradation.
4. **Adverse Edge Cases**:
   - Duplicate fault ID rejected by `DataValidator`.
   - Sensor reading with `NaN` flagged and sanitized.
   - Out-of-order late arrival detected ($t < t_{prior}$).
   - Stale version querying and snapshot rollback.
5. **Before/After Performance Evidence**:
   - Search latency: Cold (1.58 ms) vs Cached (0.02 ms) -> **79x speedup**.
   - Range aggregation: Baseline (0.165 ms) vs Fenwick (0.021 ms) -> **7.64x speedup**.
   - Memory footprint: t-Digest reduces memory by **15x** compared to storing raw float history.

