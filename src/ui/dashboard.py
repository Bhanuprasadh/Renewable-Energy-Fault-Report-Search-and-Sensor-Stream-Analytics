"""Streamlit Decision Support Dashboard for Renewable Energy Asset Maintenance."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.algorithms.persistence import PersistentFaultStore
from src.benchmarks.benchmark_suite import run_full_benchmark_suite
from src.core.config import AlgorithmConfig
from src.core.models import AssetType, Component, FaultReport, QueryFilter, Severity
from src.core.profiling import get_hardware_telemetry
from src.ingestion.stream_generator import SensorStreamGenerator
from src.ingestion.synthetic_data import CURATED_SAMPLE_QUERIES, initialize_datasets_if_missing
from src.services.analytics_service import AnalyticsService
from src.services.search_service import SearchService
from src.services.stream_service import StreamAnalyticsService

st.set_page_config(
    page_title="Renewable Energy Fault & Sensor Stream Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 12px;
        border-left: 4px solid #1E88E5;
        margin-bottom: 8px;
    }
    .badge-critical { background-color: #ffcdd2; color: #b71c1c; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .badge-high { background-color: #ffe0b2; color: #e65100; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .badge-medium { background-color: #fff9c4; color: #f57f17; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .badge-low { background-color: #c8e6c9; color: #1b5e20; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_system_state():
    initialize_datasets_if_missing()
    from src.core.config import DOMAIN_RECORDS_FILE
    with open(DOMAIN_RECORDS_FILE, "r", encoding="utf-8") as f:
        records_raw = json.load(f)

    store = PersistentFaultStore()
    reports = [FaultReport.model_validate(r) for r in records_raw]
    for r in reports:
        store.insert(r, author="SystemStartup")

    search_svc = SearchService()
    search_svc.load_and_index_records(store.get_current_records())

    analytics_svc = AnalyticsService()
    analytics_svc.load_reports(store.get_current_records())

    stream_svc = StreamAnalyticsService()
    stream_gen = SensorStreamGenerator(seed=42)

    # Pre-populate 80 streaming events on startup so charts & percentiles are immediately visible
    for step in range(1, 81):
        r = stream_gen.generate_reading(
            drift_slope=0.03 if step >= 45 else 0.0,
            inject_nan=(step == 25),
            inject_spike=(step == 60)
        )
        stream_svc.process_reading(r)

    return store, search_svc, analytics_svc, stream_svc, stream_gen


store, search_svc, analytics_svc, stream_svc, stream_gen = get_system_state()

# Sidebar
st.sidebar.title("⚡ CleanEnergy Analytics")
st.sidebar.caption("Prototype Local Decision-Support System")

st.sidebar.markdown("---")
telemetry = get_hardware_telemetry()
st.sidebar.markdown(f"**Host**: `{telemetry['architecture']}` | `{telemetry['python_version']}`")
st.sidebar.markdown(f"**Records Loaded**: `{len(store.get_current_records())}`")
st.sidebar.markdown(f"**Store Version**: `v{store.current_version}`")

nav_choice = st.sidebar.radio(
    "Navigation Modules",
    [
        "🔍 Intelligent Fault Search",
        "⚡ Live Stream & Drift Detection",
        "📈 Fenwick Range Analytics",
        "📊 Streaming Percentiles (t-Digest)",
        "🛡️ Version Control & Audit Trail",
        "🚀 Hardware Benchmarks & Team"
    ]
)

# ----------------- MODULE 1: SEARCH & FILTER -----------------
if nav_choice == "🔍 Intelligent Fault Search":
    st.header("🔍 Intelligent Renewable Fault Report Search")
    st.write("Structured predicates filtered via **Inverted Index** combined with **BM25 + Semantic Vector Retrieval** and strict candidate validation.")

    # Preset sample query selector
    preset_names = ["-- Custom Query --"] + [f"{q['query_id']}: {q['query_text']}" for q in CURATED_SAMPLE_QUERIES]
    selected_preset = st.selectbox("Quick Benchmark Queries (Curated Ground Truth):", preset_names)

    default_text = ""
    default_asset_types: list[str] = []
    default_components: list[str] = []

    if selected_preset != "-- Custom Query --":
        q_idx = int(selected_preset.split(":")[0].replace("Q-", "")) - 1
        sq = CURATED_SAMPLE_QUERIES[q_idx]
        default_text = sq["query_text"]
        s_filt = sq.get("structured_filter", {})
        default_asset_types = s_filt.get("asset_types", [])
        default_components = s_filt.get("components", [])

    col1, col2 = st.columns([3, 1])
    with col1:
        query_input = st.text_input("Natural Language Description / Notes Query:", value=default_text)
    with col2:
        top_k = st.slider("Top K Results", min_value=1, max_value=25, value=5)

    with st.expander("🛠️ Advanced Structured Predicate Filters", expanded=True):
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            asset_sel = st.multiselect("Asset Type", [a.value for a in AssetType], default=default_asset_types)
        with fcol2:
            comp_sel = st.multiselect("Component", [c.value for c in Component], default=default_components)
        with fcol3:
            sev_sel = st.selectbox("Minimum Severity", ["ANY", "LOW", "MEDIUM", "HIGH", "CRITICAL"])

    # Build filter object
    q_filter = QueryFilter(
        asset_types=[AssetType(a) for a in asset_sel] if asset_sel else None,
        components=[Component(c) for c in comp_sel] if comp_sel else None,
        min_severity=Severity(sev_sel) if sev_sel != "ANY" else None
    )

    # Execute search automatically and display results immediately
    results, latency_ms, cache_hit = search_svc.search(
        query_text=query_input,
        q_filter=q_filter,
        top_k=top_k,
        use_cache=True
    )

    st.markdown(f"**Returned `{len(results)}` validated matches in `{latency_ms:.2f} ms`** | Cache Hit: `{cache_hit}`")

    if not results:
        st.info("No records matched the combined filter and search query.")
    else:
        for idx, item in enumerate(results, start=1):
            f = item.fault
            sev_color = {
                "CRITICAL": "badge-critical",
                "HIGH": "badge-high",
                "MEDIUM": "badge-medium",
                "LOW": "badge-low"
            }.get(f.severity.value, "")

            with st.container():
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <span style="font-size: 1.1em; font-weight: bold;">#{idx} {f.fault_id} — {f.asset_id} ({f.component.value})</span>
                        &nbsp;<span class="{sev_color}">{f.severity.value}</span>
                        &nbsp;<span style="color: #666; font-size: 0.9em;">Hybrid Score: {item.hybrid_score:.4f} (BM25: {item.bm25_score:.3f}, Semantic: {item.semantic_score:.3f})</span>
                        <p style="margin: 6px 0 3px 0;"><strong>Fault:</strong> {f.fault_description}</p>
                        <p style="margin: 0; color: #444;"><strong>Maintenance Notes:</strong> {f.maintenance_notes}</p>
                        <p style="margin: 4px 0 0 0; font-size: 0.85em; color: #555;">
                            <strong>Interval:</strong> {f.time_interval.start_time.strftime('%Y-%m-%d %H:%M')} to {f.time_interval.end_time.strftime('%H:%M')} |
                            <strong>Sensor:</strong> {f.sensor_range.metric_name} [{f.sensor_range.min_val} - {f.sensor_range.max_val} {f.sensor_range.unit}] |
                            <strong>Power Loss:</strong> {f.power_loss_kwh} kWh |
                            <strong>Validated:</strong> ✅
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


# ----------------- MODULE 2: LIVE STREAM & DRIFT DETECTION -----------------
elif nav_choice == "⚡ Live Stream & Drift Detection":
    st.header("⚡ Live Sensor Telemetry & Streaming Drift Detection")
    st.write("Streams synthetic sensor readings, dynamically estimates percentiles via **t-Digest**, and monitors concept drift with the **Page-Hinkley** algorithm.")

    scol1, scol2, scol3 = st.columns([1, 1, 1])
    with scol1:
        steps_to_run = st.number_input("Step count to simulate", min_value=10, max_value=300, value=60, step=10)
    with scol2:
        drift_active = st.checkbox("Inject Gradual Concept Drift", value=True)
    with scol3:
        adverse_active = st.checkbox("Inject Adverse Conditions (NaN / Late)", value=True)

    if st.button("Replay Sensor Stream Batch", type="primary"):
        for _ in range(steps_to_run):
            reading = stream_gen.generate_reading(
                drift_slope=0.035 if drift_active else 0.0,
                inject_nan=(adverse_active and stream_gen.step_count == 40),
                inject_spike=(adverse_active and stream_gen.step_count == 85),
                out_of_order_offset_sec=(30 if adverse_active and stream_gen.step_count == 110 else 0)
            )
            stream_svc.process_reading(reading)

        st.success(f"Processed batch. Total readings in stream buffer: {len(stream_svc.reading_history)}")

    # Visualizations
    if stream_svc.reading_history:
        df_readings = pd.DataFrame([
            {
                "timestamp": r.timestamp,
                "value": r.value,
                "is_anomalous": r.is_anomalous,
                "reading_id": r.reading_id
            }
            for r in stream_svc.reading_history
        ])

        fig = px.line(df_readings, x="timestamp", y="value", title=f"Real-Time Telemetry: {stream_gen.metric_name} ({stream_gen.unit})", markers=True)
        # Highlight anomalies
        anom_points = df_readings[df_readings["is_anomalous"]]
        if not anom_points.empty:
            fig.add_trace(go.Scatter(
                x=anom_points["timestamp"],
                y=anom_points["value"],
                mode="markers",
                marker=dict(color="red", size=9, symbol="x"),
                name="Injected Anomaly"
            ))
        st.plotly_chart(fig, use_container_width=True)

        mcol1, mcol2, mcol3 = st.columns(3)
        with mcol1:
            st.metric("Total Stream Events", len(stream_svc.reading_history))
        with mcol2:
            st.metric("Drift Alarms Triggered", len(stream_svc.drift_events))
        with mcol3:
            st.metric("Adverse Sanitations Handled", len(stream_svc.validation_errors))

        if stream_svc.drift_events:
            st.subheader("🚨 Detected Drift Events (Page-Hinkley / CUSUM)")
            st.dataframe(pd.DataFrame(stream_svc.drift_events))

        if stream_svc.validation_errors:
            with st.expander("⚠️ Adverse Edge Case Log"):
                for err in stream_svc.validation_errors[-10:]:
                    st.warning(err)


# ----------------- MODULE 3: FENWICK RANGE ANALYTICS -----------------
elif nav_choice == "📈 Fenwick Range Analytics":
    st.header("📈 Time-Series Range Aggregations: Fenwick Tree vs Linear Scan")
    st.write("Demonstrates $O(\\log B)$ prefix/range aggregation on historical power loss and fault counts vs unindexed $O(N)$ baseline scan.")

    # Time bounds from data
    all_reps = store.get_current_records()
    min_t = min(r.time_interval.start_time for r in all_reps).date()
    max_t = max(r.time_interval.end_time for r in all_reps).date()

    rcol1, rcol2 = st.columns(2)
    with rcol1:
        start_d = st.date_input("Query Start Date", value=min_t + timedelta(days=10), min_value=min_t, max_value=max_t)
    with rcol2:
        end_d = st.date_input("Query End Date", value=min_t + timedelta(days=40), min_value=min_t, max_value=max_t)

    start_dt = datetime.combine(start_d, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(end_d, datetime.max.time(), tzinfo=timezone.utc)

    # Always compute and display range analytics immediately
    comparison = analytics_svc.query_range_comparison(start_dt, end_dt)

    f_res = comparison["fenwick"]
    b_res = comparison["baseline"]

    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("Total Faults Count", f_res["total_faults"])
    with colB:
        st.metric("Total Power Loss (kWh)", f"{f_res['total_power_loss_kwh']:,.1f}")
    with colC:
        st.metric("Oracle Match Verified", "✅ TRUE" if comparison["results_match_oracle"] else "❌ MISMATCH")

    # Performance comparison table
    perf_df = pd.DataFrame([
        {
            "Algorithm": "Fenwick Tree (Indexed)",
            "Complexity": "O(log B)",
            "Execution Time (ms)": f"{f_res['execution_time_ms']:.4f}",
            "Power Loss (kWh)": f_res["total_power_loss_kwh"]
        },
        {
            "Algorithm": "Linear Scan (Baseline)",
            "Complexity": "O(N)",
            "Execution Time (ms)": f"{b_res['execution_time_ms']:.4f}",
            "Power Loss (kWh)": b_res["total_power_loss_kwh"]
        }
    ])
    st.table(perf_df)
    st.success(f"Fenwick Tree achieved a **{comparison['speedup_factor']}x speedup** over linear scanning while yielding exact mathematical equivalence.")


# ----------------- MODULE 4: STREAMING PERCENTILES -----------------
elif nav_choice == "📊 Streaming Percentiles (t-Digest)":
    st.header("📊 Streaming Sensor Percentiles: t-Digest vs Exact Baseline")
    st.write("Evaluates t-Digest quantile sketching error $(\\epsilon)$ and memory compression relative to storing all observations.")

    comp_data = stream_svc.get_percentile_comparison()
    if comp_data["samples_processed"] == 0:
        st.info("No stream data ingested yet. Go to '⚡ Live Stream & Drift Detection' and run a batch first!")
    else:
        st.markdown(f"**Samples Ingested**: `{comp_data['samples_processed']}` | **t-Digest Memory**: `{comp_data['tdigest_memory_bytes']} bytes` | **Exact Memory**: `{comp_data['exact_memory_bytes']} bytes`")
        st.markdown(f"**Memory Reduction**: `{comp_data['memory_reduction_ratio']}x less memory`")

        p_rows = []
        for p, d in comp_data["comparison"].items():
            p_rows.append({
                "Percentile": p.upper(),
                "Exact Sorted Value": d["exact"],
                "t-Digest Sketch Value": d["tdigest"],
                "Absolute Error": d["abs_error"],
                "Relative Error (%)": f"{d['rel_error_pct']:.2f}%"
            })
        st.dataframe(pd.DataFrame(p_rows), use_container_width=True)


# ----------------- MODULE 5: VERSION CONTROL & AUDIT -----------------
elif nav_choice == "🛡️ Version Control & Audit Trail":
    st.header("🛡️ Auditable Version Control & Snapshot Rollback")
    st.write("Demonstrates persistence semantics, append-only immutable audit logging, and point-in-time state rollback.")

    st.subheader(f"Current System State: Version v{store.current_version}")
    audit_entries = store.get_audit_log()

    st.dataframe(pd.DataFrame([e.to_dict() for e in audit_entries]), use_container_width=True)

    with st.expander("🔄 Rollback Store to Previous Version"):
        target_v = st.number_input("Target Version Number", min_value=1, max_value=max(1, store.current_version - 1), value=1)
        if st.button("Confirm Rollback", type="secondary"):
            success = store.rollback_to_version(int(target_v), author="PlantEngineer")
            if success:
                active = store.get_current_records()
                search_svc.load_and_index_records(active)
                analytics_svc.load_reports(active)
                st.success(f"Successfully rolled back to snapshot v{target_v}! New version created: v{store.current_version}")
                st.rerun()


# ----------------- MODULE 6: BENCHMARKS & TEAM -----------------
elif nav_choice == "🚀 Hardware Benchmarks & Team":
    st.header("🚀 Hardware-Aware Benchmarks & Four-Member Division")

    st.subheader("Hardware & System Telemetry")
    st.json(telemetry)

    st.markdown("---")
    st.subheader("Four-Member Division of Work & Syllabus Mapping")
    colM1, colM2 = st.columns(2)
    with colM1:
        st.markdown("""
        **Member 1: Ingestion, Schema, Correctness Oracle & Hardware Telemetry**
        - Pydantic schema validation (`AssetType`, `FaultReport`, `SensorReading`).
        - 20 Curated Gold-standard cases + 1,000 synthetic domain records.
        - Stream generator with adverse edge cases (NaNs, late arrivals, spikes).
        - Hardware telemetry profiling (CPU, RAM, latency distributions).
        - *Syllabus Mapping: CO2, CO3*
        
        **Member 2: Exact Indexes, Update/Version Semantics & Complexity**
        - Fenwick Tree (Binary Indexed Tree) for $O(\\log N)$ time range aggregates.
        - Persistent / Versioned Store with immutable audit log and rollback.
        - Multi-attribute Inverted Index for fast set-intersection candidate filtering.
        - *Syllabus Mapping: CO3, CO4*
        """)
    with colM2:
        st.markdown("""
        **Member 3: Probabilistic Summaries & Streaming Drift Detection**
        - t-Digest online quantile sketch for bounded memory P50-P99 percentiles.
        - Page-Hinkley streaming concept drift detector for wear degradation.
        - CUSUM step-change detector for abrupt component faults.
        - Parameter sweeps over compression factor $\\delta$ and threshold $\\lambda$.
        - *Syllabus Mapping: CO4, CO5*

        **Member 4: Retrieval Integration, Modern UI/API & Benchmarks**
        - BM25 relevance ranking + TF-IDF semantic vector retrieval.
        - Hybrid ranking fusion with strict candidate validation oracle.
        - Thread-safe LRU/TTL query cache.
        - FastAPI endpoints + Interactive Streamlit Decision Support UI.
        - *Syllabus Mapping: CO5, CO6*
        """)

    st.markdown("---")
    st.subheader("Run Automated Benchmark Suite (Sizes: 100, 500, 1000)")
    if st.button("Run Full Benchmark Suite", type="primary"):
        with st.spinner("Benchmarking algorithms across data sizes..."):
            report = run_full_benchmark_suite(sizes=[100, 500, 1000])
            st.success("Benchmarks completed successfully!")
            st.json(report)

