"""Global configuration parameters and default algorithm constants."""
from pathlib import Path
from dataclasses import dataclass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
GOLD_RECORDS_FILE = DATA_DIR / "gold_records_20.json"
DOMAIN_RECORDS_FILE = DATA_DIR / "domain_records_1000.json"
SAMPLE_QUERIES_FILE = DATA_DIR / "sample_queries.json"


@dataclass(frozen=True)
class AlgorithmConfig:
    # Fenwick Tree discretization resolution (e.g. 3600 seconds = 1 hour buckets)
    FENWICK_BUCKET_SECONDS: int = 3600

    # t-Digest compression parameter delta (higher = more centroids, lower error, more memory)
    TDIGEST_DELTA: float = 100.0

    # Page-Hinkley drift detection parameters
    DRIFT_DELTA: float = 0.05
    DRIFT_LAMBDA: float = 50.0
    DRIFT_ALPHA: float = 0.995

    # BM25 parameters
    BM25_K1: float = 1.5
    BM25_B: float = 0.75

    # Hybrid Search Weight (alpha * BM25 + (1 - alpha) * Semantic)
    HYBRID_ALPHA: float = 0.55

    # Cache parameters
    CACHE_CAPACITY: int = 512
    CACHE_TTL_SECONDS: int = 300

