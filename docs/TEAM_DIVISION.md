# Four-Member Division of Work & Complexity Analysis

This document details the individual ownership, algorithm traces, and asymptotic complexities implemented by each team member.

---

## Member 1: Data Ingestion, Schema, Correctness Oracle & Hardware Profiling
* **Lead Role**: Ingestion Engineer & Benchmarking Lead
* **Primary Responsibilities**:
  1. Authored strict Pydantic v2 schemas: `AssetType`, `Component`, `Severity`, `TimeInterval`, `SensorRange`, and `FaultReport`.
  2. Curated the **20 Gold Standard Ground-Truth Records** (`data/gold_records_20.json`) and generated **1,000 realistic synthetic domain records** across wind turbines and solar PV arrays.
  3. Implemented the **DataValidator Correctness Oracle**: captures duplicate IDs, inverted intervals ($t_1 > t_2$), NaN values, and late arrivals.
  4. Built the **Ground-Truth Baselines**:
     - `LinearScanBaseline`: $O(N)$ unindexed sequential scan.
     - `ExactAggregatesBaseline`: $O(N)$ linear range aggregator.
     - `ExactPercentilesBaseline`: $O(N \log N)$ sorting-based percentile tracker.
  5. Implemented `hardware_telemetry` and `benchmark_callable` with latency percentiles and memory footprint tracing via `tracemalloc`.

---

## Member 2: Exact Indexes, Update/Version Semantics & Complexity Analysis
* **Lead Role**: Algorithmic Data Structures & Persistence Specialist
* **Primary Responsibilities**:
  1. Designed and implemented the **Fenwick Tree (Binary Indexed Tree)** (`src/algorithms/fenwick.py`):
     - Discretized time buckets over arbitrary intervals.
     - Maintains dual trees: cumulative power loss (kWh) and fault frequencies, partitioned by severity.
     - Replaces linear scans with $O(\log B)$ prefix queries.
  2. Built the **Persistent Store** (`src/algorithms/persistence.py`):
     - Versioned snapshots with copy-on-write semantics.
     - Immutable audit trail recording timestamps, actions (`CREATE`, `UPDATE`, `DELETE`, `ROLLBACK`), diffs, and authors.
     - Point-in-time querying (`get_as_of_version`) and reversible rollback.
  3. Designed the **Inverted Index** (`src/algorithms/inverted_index.py`):
     - Posting lists for multi-attribute set intersection.
* **Algorithmic Complexity Summary**:
  | Operation | Baseline Linear Scan | Indexed Implementation | Improvement |
  |---|---|---|---|
  | **Range Sum / Count Query** | $O(N)$ | $O(\log B)$ (Fenwick Tree) | Exponential speedup |
  | **Point Insert / Update** | $O(1)$ | $O(\log B)$ | Minimal logarithmic cost |
  | **Structured Attribute Filter** | $O(N)$ | $O(k + \|S_1 \cap \dots \cap S_m\|)$ | Fast inverted list intersection |
  | **Version Rollback** | Not supported | $O(1)$ snapshot pointer swap | Audit-safe instant rollback |

---

## Member 3: Probabilistic Summaries, Stream Processing & Drift Detection
* **Lead Role**: Streaming Systems & Data Sketches Specialist
* **Primary Responsibilities**:
  1. Implemented the **t-Digest Quantile Sketch** (`src/algorithms/tdigest.py`):
     - Online clustering with scale function $k_1(q) = \frac{\delta}{2\pi} \arcsin(2q - 1)$.
     - High precision at extreme tails ($P_{90}, P_{95}, P_{99}$) with bounded memory footprint ($O(\delta)$).
     - Supports sketch merging (`merge()`) across distributed sensor partitions.
  2. Implemented **Streaming Concept Drift Detectors** (`src/algorithms/drift_detector.py`):
     - **Page-Hinkley Test**: Tracks cumulative deviation from rolling mean for gradual physical wear detection.
     - **CUSUM Test**: Cumulative sum test for abrupt component step-changes.
  3. Conducted parameter sweeps over compression factor $\delta \in [25, 50, 100, 200]$ and decision threshold $\lambda$.

---

## Member 4: Retrieval Integration, Dashboard/API, Caching & Benchmarking
* **Lead Role**: Retrieval Architect & Full-Stack Integration Lead
* **Primary Responsibilities**:
  1. Built the **Okapi BM25 Lexical Ranking Engine** (`src/algorithms/bm25.py`):
     - Custom tokenizer with stopword pruning and term-frequency posting lists.
     - Standard Lucene-style IDF computation.
  2. Implemented **Semantic Vector Retrieval** (`src/algorithms/semantic_retrieval.py`):
     - TF-IDF vector space model with sublinear TF and cosine similarity.
     - **Hybrid Fusion Ranker**: Weighted combination of normalized BM25 and semantic cosine scores.
     - **Mandatory Candidate Validation Layer**: Verifies candidate reports against strict sensor boundaries and interval constraints before display.
  3. Built the **LRU + TTL Query Cache** (`src/algorithms/cache.py`):
     - Thread-safe caching with hit/miss telemetry (yielding 49,000+ ops/sec throughput).
  4. Built the **Streamlit Interactive UI** (`src/ui/dashboard.py`) and **FastAPI Service** (`src/api/app.py`).
  5. Implemented the **Automated Benchmarking Suite** (`src/benchmarks/benchmark_suite.py`) evaluating MRR, NDCG@5, latencies, and memory footprints.

