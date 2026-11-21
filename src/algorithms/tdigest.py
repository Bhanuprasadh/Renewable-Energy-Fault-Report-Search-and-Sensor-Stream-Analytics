"""t-Digest quantile sketch for streaming sensor percentile estimation with bounded memory."""
from __future__ import annotations

import math
import sys
from typing import Dict, List, Optional, Tuple


class Centroid:
    __slots__ = ("mean", "weight")

    def __init__(self, mean: float, weight: float = 1.0):
        self.mean = mean
        self.weight = weight

    def __repr__(self) -> str:
        return f"Centroid(mean={self.mean:.4f}, weight={self.weight:.1f})"


class TDigest:
    """Accurate streaming percentile sketch with sub-linear O(delta) memory footprint.
    
    Uses dynamic centroid clustering with a scale function that gives high precision
    at extreme percentiles (e.g. P90, P95, P99) where fault detection matters most.
    """

    def __init__(self, delta: float = 100.0, buffer_multiplier: int = 5):
        self.delta = max(10.0, delta)
        self.centroids: List[Centroid] = []
        self._buffer: List[float] = []
        self.max_buffer_size = int(self.delta * buffer_multiplier)
        self.total_weight = 0.0

    def update(self, x: float, w: float = 1.0) -> None:
        """Add a streaming value x with optional weight w."""
        if math.isnan(x) or math.isinf(x):
            return
        self._buffer.append(x)
        self.total_weight += w
        if len(self._buffer) >= self.max_buffer_size:
            self._compress()

    def _compress(self) -> None:
        """Merge buffered points into centroids using scale function k_1."""
        if not self._buffer and not self.centroids:
            return

        # Combine existing centroids and buffered values
        combined: List[Tuple[float, float]] = [(c.mean, c.weight) for c in self.centroids]
        for val in self._buffer:
            combined.append((val, 1.0))
        self._buffer.clear()

        # Sort by mean
        combined.sort(key=lambda item: item[0])

        new_centroids: List[Centroid] = []
        w_so_far = 0.0
        curr_mean = combined[0][0]
        curr_weight = combined[0][1]

        def k_scale(q: float) -> float:
            # Scale function k_1: maps quantile [0, 1] to scale units
            clamped = max(1e-7, min(1.0 - 1e-7, q))
            return (self.delta / (2.0 * math.pi)) * math.asin(2.0 * clamped - 1.0)

        for mean_val, weight_val in combined[1:]:
            q0 = w_so_far / self.total_weight
            q1 = (w_so_far + curr_weight + weight_val) / self.total_weight
            dk = k_scale(q1) - k_scale(q0)

            # Check if merging exceeds scale limit 1.0
            if dk <= 1.0:
                # Merge into current centroid
                curr_mean = (curr_mean * curr_weight + mean_val * weight_val) / (curr_weight + weight_val)
                curr_weight += weight_val
            else:
                # Flush current centroid and start new one
                new_centroids.append(Centroid(curr_mean, curr_weight))
                w_so_far += curr_weight
                curr_mean = mean_val
                curr_weight = weight_val

        new_centroids.append(Centroid(curr_mean, curr_weight))
        self.centroids = new_centroids

    def percentile(self, p: float) -> float:
        """Query percentile p in range [0, 100]."""
        if self._buffer:
            self._compress()

        if not self.centroids:
            return 0.0
        if len(self.centroids) == 1:
            return self.centroids[0].mean

        q = max(0.0, min(1.0, p / 100.0))
        target_weight = q * self.total_weight

        # Handle boundary cases
        if target_weight <= self.centroids[0].weight / 2.0:
            return self.centroids[0].mean
        if target_weight >= self.total_weight - (self.centroids[-1].weight / 2.0):
            return self.centroids[-1].mean

        cumulative_weight = self.centroids[0].weight / 2.0
        for i in range(len(self.centroids) - 1):
            c1 = self.centroids[i]
            c2 = self.centroids[i + 1]
            dw = (c1.weight + c2.weight) / 2.0
            if cumulative_weight + dw >= target_weight:
                # Linear interpolation between adjacent centroids
                fraction = (target_weight - cumulative_weight) / dw
                return c1.mean + fraction * (c2.mean - c1.mean)
            cumulative_weight += dw

        return self.centroids[-1].mean

    def get_percentiles_summary(self) -> Dict[str, float]:
        """Compute P50, P90, P95, P99."""
        return {
            "p50": round(self.percentile(50.0), 3),
            "p90": round(self.percentile(90.0), 3),
            "p95": round(self.percentile(95.0), 3),
            "p99": round(self.percentile(99.0), 3)
        }

    def merge(self, other: TDigest) -> TDigest:
        """Merge another t-digest into a new combined t-digest."""
        merged = TDigest(delta=max(self.delta, other.delta))
        self._compress()
        other._compress()
        combined = [(c.mean, c.weight) for c in self.centroids] + [(c.mean, c.weight) for c in other.centroids]
        combined.sort(key=lambda x: x[0])
        merged.total_weight = self.total_weight + other.total_weight
        
        for m, w in combined:
            merged.centroids.append(Centroid(m, w))
        merged._compress()
        return merged

    def memory_bytes(self) -> int:
        """Compute current in-memory footprint in bytes."""
        base_size = sys.getsizeof(self) + sys.getsizeof(self.centroids) + sys.getsizeof(self._buffer)
        centroids_size = len(self.centroids) * 48  # Approx 48 bytes per Centroid object
        buffer_size = len(self._buffer) * 8
        return base_size + centroids_size + buffer_size

