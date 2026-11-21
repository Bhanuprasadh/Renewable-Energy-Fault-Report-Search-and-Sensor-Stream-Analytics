# Limitations and Ethics Disclosure

## 1. Non-Production Readiness & Intended Use
> [!IMPORTANT]
> This software is an **academic research prototype and decision-support tool** intended exclusively for educational demonstrations and decision-assistance by trained plant engineers. It is **not** certified for safety-critical plant operations, automated turbine emergency trip control, high-voltage breaker trip decisions, or unmonitored autonomous grid dispatch.

## 2. Key Algorithmic Limitations
1. **Discretization Approximations in Time Aggregation**:
   - The Fenwick Tree discretizes continuous event intervals into fixed-width hourly buckets ($B = 3600\,\text{s}$). While bucket-level queries are exact, sub-hourly event distributions within a single bucket are treated uniformly.
2. **Probabilistic Nature of Sketches**:
   - The t-Digest sketch provides bounded-error approximations ($\epsilon \le 1.5\%$) of sensor percentiles. While it guarantees $O(\delta)$ memory savings, it should not be used as an exact legal audit record for regulatory environmental reporting without raw sample retention.
3. **Drift Detection Sensitivity**:
   - The Page-Hinkley and CUSUM tests are tuned for stationary baselines with additive gaussian noise. Sudden extreme weather anomalies (such as severe turbulence or icing) may trigger alarms that require human engineer physical inspection to distinguish between sensor drift and genuine mechanical wear.
4. **Lexical & Semantic Retrieval Boundary**:
   - Approximate vector and BM25 candidates are passed through the strict Validation Oracle layer. In extreme edge cases where maintenance logs contain ambiguous or incomplete notes, manual engineering inspection is mandatory.

## 3. Ethical & Environmental Considerations
- **Data Integrity & Traceability**:
  All modifications to fault reports are versioned in an append-only persistent store with cryptographic audit logging to prevent tampering with equipment maintenance history.
- **Fair Resource Attribution**:
  Hardware-aware profiling ensures algorithms minimize computational energy and memory overhead, adhering to green computing best practices.

