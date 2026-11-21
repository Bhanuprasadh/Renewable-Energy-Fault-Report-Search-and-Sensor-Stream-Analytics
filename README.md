# Renewable Energy Fault Report Search and Sensor Stream Analytics

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B.svg)](https://streamlit.io)
[![Tests Passing](https://img.shields.io/badge/tests-16%20passed-brightgreen.svg)]()

An industry-level, local decision-support system designed for plant engineers and maintenance planners managing solar (PV) and wind energy installations. It couples continuous sensor stream telemetry, probabilistic data sketching, concept drift detection, and auditable versioned storage with high-precision hybrid retrieval.

---

## 🌟 Highlights & Algorithmic Solutions

| Capability | Algorithm / Technique | Complexity | Baseline Comparison |
|---|---|---|---|
| **Time Range Aggregations** | **Fenwick Tree (Binary Indexed Tree)** | $O(\log B)$ | **7.64x faster** than $O(N)$ linear range scan |
| **Streaming Percentiles** | **t-Digest Quantile Sketch** | $O(\delta)$ bounded space | **15x memory reduction** vs raw float buffer with $<1.5\%$ error |
| **Sensor Degradation** | **Page-Hinkley & CUSUM Drift Tests** | $O(1)$ per event | Detects gradual wear & sudden step-changes |
| **Fault Report Search** | **Inverted Index + Okapi BM25 + Semantic Cosine** | $O(k + \|S_1 \cap S_2\|)$ | **MRR = 1.0, NDCG@5 = 0.67**, verified with strict validation oracle |
| **High-Throughput Caching** | **Thread-Safe LRU + TTL Cache** | $O(1)$ | **49,000+ queries/sec** ($0.020\text{ ms}$ latency) |
| **Auditable Persistence** | **Persistent Store with Snapshot Rollback** | $O(1)$ versioning | Point-in-time recovery & immutable audit log |

---

## 👥 Four-Member Team Division of Work

* **Member 1 (Ingestion & Correctness Oracle Lead)**:
  - Pydantic v2 schemas (`AssetType`, `FaultReport`, `SensorReading`, `TimeInterval`, `SensorRange`).
  - 20 Curated Gold-standard cases + 1,000 synthetic domain records.
  - Streaming event generator with adverse edge cases (NaNs, late arrivals, noise, spikes).
  - Ground-truth baselines: `LinearScanBaseline`, `ExactAggregatesBaseline`, `ExactPercentilesBaseline`.
  - Hardware-aware profiler capturing CPU, RAM, and latency distributions (Median, P95).
  - *Syllabus Mapping: CO2, CO3*

* **Member 2 (Exact Indexes & Persistence Specialist)**:
  - Fenwick Tree (Binary Indexed Tree) for range power loss and fault frequency aggregations.
  - Persistent & versioned store with snapshot rollback and immutable audit trail.
  - Multi-attribute inverted index for discrete categorical filters.
  - Theoretical complexity analysis.
  - *Syllabus Mapping: CO3, CO4*

* **Member 3 (Probabilistic Summaries & Streaming Drift Specialist)**:
  - t-Digest online quantile sketch for bounded-memory $P_{50}, P_{90}, P_{95}, P_{99}$ percentiles.
  - Streaming concept drift detectors: Page-Hinkley test and CUSUM test.
  - Parameter sweeps over compression factor $\delta \in [25, 200]$ and threshold $\lambda$.
  - *Syllabus Mapping: CO4, CO5*

* **Member 4 (Retrieval Integration, UI/API & Benchmarks Lead)**:
  - Okapi BM25 lexical ranking engine.
  - TF-IDF vector space model with sublinear TF cosine similarity.
  - Hybrid fusion ranker with strict candidate validation oracle.
  - Thread-safe LRU + TTL query cache.
  - FastAPI backend (`src/api/app.py`) & Streamlit interactive dashboard (`src/ui/dashboard.py`).
  - Comprehensive automated benchmarking suite (`src/benchmarks/benchmark_suite.py`).
  - *Syllabus Mapping: CO5, CO6*

---

## 📁 Project Architecture

```
├── data/
│   ├── gold_records_20.json        # 20 Curated gold benchmark records
│   ├── domain_records_1000.json    # 1,000 Synthetic renewable asset records
│   ├── sample_queries.json         # Judged queries for MRR/NDCG evaluation
│   └── benchmark_report.json       # Automated benchmark output
├── docs/
│   ├── ARCHITECTURE.md             # System architecture & Mermaid data flow
│   ├── TEAM_DIVISION.md            # Detailed 4-member ownership & complexity tables
│   ├── SYLLABUS_MAPPING.md         # CO2-CO6 mapping & lecture references
│   ├── MILESTONES.md               # 6 incremental milestone releases
│   └── LIMITATIONS_ETHICS.md       # Limitations & non-production ethics note
├── src/
│   ├── core/                       # Pydantic schemas, configs, profiling utilities
│   ├── ingestion/                  # Data generators, stream replay, schema validator
│   ├── baselines/                  # O(N) unindexed ground-truth oracles
│   ├── algorithms/                 # Fenwick, Persistence, InvertedIndex, t-Digest, Page-Hinkley, BM25, Cache
│   ├── services/                   # Search, Stream Analytics, Time-Series Range Services
│   ├── api/                        # FastAPI application
│   ├── ui/                         # Streamlit Decision Support Dashboard
│   └── benchmarks/                 # Automated benchmarking suite
├── tests/                          # 16 unit & integration tests (100% pass rate)
├── pyproject.toml                  # Project metadata and dependencies
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Environment Setup (using `uv`)

```bash
# Clone repository and navigate to workspace
cd "Renewable Energy Fault Report Search and Sensor Stream Analytics"

# Activate the virtual environment
source .venv/bin/activate
```

### 2. Run the Automated Test Suite

```bash
PYTHONPATH=. pytest tests -v
```
*Expected: 16 passed tests covering models, Fenwick tree, persistence rollback, t-digest, drift detection, BM25, and adverse cases.*

### 3. Run the Automated Benchmark Suite

```bash
PYTHONPATH=. python src/benchmarks/benchmark_suite.py
```
*Evaluates latency, P95, throughput, memory footprint, t-Digest errors, and MRR/NDCG ranking across dataset sizes (100, 500, 1000).*

### 4. Launch the Interactive Decision Support Dashboard (Streamlit)

```bash
PYTHONPATH=. streamlit run src/ui/dashboard.py
```
*Open your browser at `http://localhost:8501` to access:*
- **Tab 1: 🔍 Intelligent Fault Search**: Hybrid search combining exact filters, BM25, and semantic vector ranking.
- **Tab 2: ⚡ Live Stream & Drift Detection**: Real-time sensor stream replay, interactive telemetry plot, and Page-Hinkley drift alerts.
- **Tab 3: 📈 Fenwick Range Analytics**: $O(\log B)$ time-series aggregations vs $O(N)$ linear scan comparison.
- **Tab 4: 📊 Streaming Percentiles**: t-Digest quantile sketch ($P_{50}, P_{90}, P_{95}, P_{99}$) vs exact baseline with error metrics.
- **Tab 5: 🛡️ Version Control & Audit Trail**: Auditable event log, diff inspection, and one-click snapshot rollback.
- **Tab 6: 🚀 Hardware Benchmarks & Team**: Real-time hardware telemetry and 4-member contribution report.

### 5. Launch the REST API (FastAPI)

```bash
PYTHONPATH=. uvicorn src.api.app:app --reload --port 8000
```
*Interactive Swagger API documentation available at `http://localhost:8000/docs`.*

---

## 📊 Benchmark Summary

| Metric | Baseline Linear Scan | Indexed / Optimized | Speedup / Reduction |
|---|---|---|---|
| **Search Latency (Cold, N=1000)** | $3.48\text{ ms}$ | $1.58\text{ ms}$ (Inverted + BM25) | **2.2x speedup** |
| **Search Latency (Cached)** | $3.48\text{ ms}$ | $0.020\text{ ms}$ (LRU Cache) | **174x speedup (49,000+ ops/sec)** |
| **Range Query Latency (N=1000)** | $0.165\text{ ms}$ | $0.021\text{ ms}$ (Fenwick Tree) | **7.64x speedup** |
| **Range Oracle Match** | Exact Ground Truth | Exact Mathematical Match | **100% Agreement (0 error)** |
| **Sensor Percentiles Memory** | $40,000\text{ bytes}$ (Full buffer) | $2,700\text{ bytes}$ (t-Digest $\delta=100$) | **15x memory reduction** |
| **t-Digest Tail Error ($P_{99}$)** | Exact | $\pm 0.08\%$ relative error | High tail precision |
| **Search Ranking Quality** | Naive substring | **MRR: 1.0 \| NDCG@5: 0.67** | Gold-standard rank #1 |

---

## 📜 Academic Acceptance Demonstration Checklist

1. **Baseline Query**: Demonstrated via `LinearScanBaseline` and `ExactAggregatesBaseline`.
2. **Indexed Query**: Demonstrated via `TimeAggregateIndex` (Fenwick) and `SearchService` (Inverted + BM25 + Semantic).
3. **Stream Replay with Drift**: Demonstrated via `SensorStreamGenerator` with `PageHinkleyDriftDetector` and `CUSUMDriftDetector`.
4. **Adverse Edge Cases**: Explicit tests for duplicate IDs, missing/NaN values, and out-of-order arrivals.
5. **Quality-Latency-Memory Trade-offs**: Documented empirical telemetry recorded in `data/benchmark_report.json`.

---

## ⚖️ Limitations & Ethics Notice
*This software is an educational prototype and decision-support tool. It is not intended for automated safety-critical control or unmonitored plant emergency decisions. See [LIMITATIONS_ETHICS.md](docs/LIMITATIONS_ETHICS.md) for full disclosure.*

# Renewable-Energy-Fault-Report-Search-and-Sensor-Stream-Analytics
