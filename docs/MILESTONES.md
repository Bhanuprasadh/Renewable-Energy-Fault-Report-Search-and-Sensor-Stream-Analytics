# Project Milestone Releases

This project is organized into six incremental milestones matching the course progression:

## Milestone 1: Data Ingestion, Schemas & Baseline Correctness Oracle (v0.1.0)
* **Goal**: Establish deterministic data generation, schema validation, and baseline reference implementations.
* **Deliverables**:
  - Pydantic models for `FaultReport`, `SensorReading`, `TimeInterval`, `SensorRange`.
  - 20 Curated Gold-standard cases and 1,000 synthetic domain records.
  - Linear scan and exact range baselines for correctness verification.

## Milestone 2: Exact Indexes & Persistence Semantics (v0.2.0)
* **Goal**: Implement prefix time-series aggregations and auditable version control.
* **Deliverables**:
  - Binary Indexed Tree (Fenwick Tree) supporting $O(\log B)$ range queries.
  - Discretized time indexing for hourly renewable generation analytics.
  - Persistent store with snapshot isolation, rollback, and immutable audit logging.
  - Inverted index for discrete categorical filters.

## Milestone 3: Probabilistic Summaries & Streaming Drift Detection (v0.3.0)
* **Goal**: Enable bounded-memory sensor percentile tracking and online degradation alerts.
* **Deliverables**:
  - t-Digest quantile sketch supporting $P_{50}, P_{90}, P_{95}, P_{99}$ with dynamic centroid clustering.
  - Page-Hinkley cumulative deviance drift detector.
  - CUSUM abrupt step change detector.
  - Adverse edge case validation (NaN values, late arrivals).

## Milestone 4: Information Retrieval Integration & Candidate Validation (v0.4.0)
* **Goal**: Provide high-precision search over maintenance logs and fault descriptions.
* **Deliverables**:
  - Okapi BM25 probabilistic relevance ranking engine.
  - TF-IDF vector space model with sublinear TF cosine similarity.
  - Hybrid fusion ranker combining structured predicates, BM25, and semantic scores.
  - Strict validation layer preventing unverified approximate candidates from display.
  - LRU/TTL query cache.

## Milestone 5: Decision Support UI, API & Automated Benchmarking (v0.5.0)
* **Goal**: Deliver unified interfaces for maintenance planners and automated profiling.
* **Deliverables**:
  - FastAPI application with search, stream, and analytics endpoints.
  - Streamlit multi-tab decision support dashboard.
  - Hardware-aware profiler capturing CPU, RAM, latency distributions (Median, P95), and memory deltas.
  - Ranking evaluation evaluating MRR and NDCG@5.

## Milestone 6: Release Packaging, Acceptance Verification & Ethics (v1.0.0)
* **Goal**: Final project hardening, integration testing, and documentation.
* **Deliverables**:
  - Full pytest automated suite (16 tests, 100% pass rate).
  - Benchmark report across 3 data sizes (100, 500, 1000).
  - Limitations and ethics disclosure for renewable plant operations.
  - Clean modular package structure ready for academic review.

