"""Hardware-aware profiler for latency, memory footprint, and environment telemetry."""
import os
import platform
import time
import tracemalloc
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, List, Tuple
import numpy as np


def get_hardware_telemetry() -> Dict[str, Any]:
    """Capture host architecture, OS, Python runtime, and memory stats."""
    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "pid": os.getpid(),
    }


@contextmanager
def profile_execution(track_memory: bool = True) -> Generator[Dict[str, float], None, None]:
    """Context manager to measure elapsed wall-clock latency (ms) and peak memory delta (KB)."""
    stats: Dict[str, float] = {"elapsed_ms": 0.0, "peak_memory_kb": 0.0}
    if track_memory:
        tracemalloc.start()
        mem_before, _ = tracemalloc.get_traced_memory()

    start_time = time.perf_counter()
    try:
        yield stats
    finally:
        end_time = time.perf_counter()
        stats["elapsed_ms"] = (end_time - start_time) * 1000.0
        if track_memory:
            _, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            stats["peak_memory_kb"] = max(0.0, (peak_mem - mem_before) / 1024.0)


def benchmark_callable(
    fn: Callable[[], Any],
    warmup_runs: int = 3,
    repeat_runs: int = 15,
    track_memory: bool = True
) -> Dict[str, float]:
    """Benchmark a function across repeated executions, reporting median, p95, min, max, and memory."""
    for _ in range(warmup_runs):
        fn()

    latencies_ms: List[float] = []
    peak_mems_kb: List[float] = []

    for _ in range(repeat_runs):
        with profile_execution(track_memory=track_memory) as stats:
            fn()
        latencies_ms.append(stats["elapsed_ms"])
        if track_memory:
            peak_mems_kb.append(stats["peak_memory_kb"])

    arr = np.array(latencies_ms)
    res = {
        "runs": float(repeat_runs),
        "median_latency_ms": float(np.median(arr)),
        "p95_latency_ms": float(np.percentile(arr, 95)),
        "min_latency_ms": float(np.min(arr)),
        "max_latency_ms": float(np.max(arr)),
        "std_latency_ms": float(np.std(arr)),
        "throughput_ops_per_sec": float(1000.0 / np.median(arr)) if np.median(arr) > 0 else 0.0,
    }
    if peak_mems_kb:
        res["peak_memory_kb"] = float(np.max(peak_mems_kb))
    return res

