"""
EVRYN Phase 2.4 - Comprehensive Performance Measurement Script.
Runs repeatable cold and warm tests for:
- Short text extraction (Cold vs Warm 10 runs)
- Longer scientific text extraction (Cold vs Warm 10 runs)
- Multi-file uploads (Cold vs Warm)
- Benchmark retrieval (Cold vs Warm 10 runs)
- Verified catalog retrieval (10 runs)
Outputs sample counts, median, mean, p95, min, max, and environment details.
"""

import time
import os
import requests
import numpy as np
import platform

SERVER_URL = "http://127.0.0.1:8000"

def measure_runs(name, func, runs=10):
    # Cold run
    t0 = time.perf_counter()
    func(is_cold=True)
    cold_ms = (time.perf_counter() - t0) * 1000.0

    # Warm runs
    warm_latencies = []
    for _ in range(runs):
        t0 = time.perf_counter()
        func(is_cold=False)
        t1 = time.perf_counter()
        warm_latencies.append((t1 - t0) * 1000.0)

    arr = np.array(warm_latencies)
    return {
        "name": name,
        "cold_ms": cold_ms,
        "runs": runs,
        "median_ms": np.median(arr),
        "mean_ms": np.mean(arr),
        "p95_ms": np.percentile(arr, 95),
        "min_ms": np.min(arr),
        "max_ms": np.max(arr),
    }

def run_all_benchmarks():
    print("=" * 80)
    print("EVRYN PHASE 2.4 PERFORMANCE AUDIT & BENCHMARK PROFILE")
    print("=" * 80)
    print(f"Environment: Linux {platform.release()} | Python {platform.python_version()} | Platform: {platform.machine()}")
    print(f"Server Target: {SERVER_URL}")
    print("-" * 80)

    results = []

    # 1. Benchmark Retrieval
    def bench_fn(is_cold=False):
        r = requests.get(f"{SERVER_URL}/api/benchmark/results")
        assert r.status_code == 200

    results.append(measure_runs("GET /api/benchmark/results", bench_fn, runs=10))

    # 2. Verified Examples Catalog
    def cat_fn(is_cold=False):
        r = requests.get(f"{SERVER_URL}/api/examples/verified")
        assert r.status_code == 200

    results.append(measure_runs("GET /api/examples/verified", cat_fn, runs=10))

    # 3. Short Text Extraction (System A)
    short_text = "EGFR triggers downstream phosphorylation of STAT3."
    def short_fn(is_cold=False):
        # for cold, use unique text to bypass cache
        txt = short_text if not is_cold else f"{short_text} (run_{time.time()})"
        r = requests.post(f"{SERVER_URL}/api/extract", json={"text": txt, "system_mode": "nlp_baseline"})
        assert r.status_code == 200

    results.append(measure_runs("POST /api/extract (Short text, System A)", short_fn, runs=10))

    # 4. Longer Scientific Text (System A)
    long_text = (
        "Acidic environmental pH directly triggers activation of sensor kinase PmrB in Salmonella enterica. "
        "Phosphorylated PmrB subsequently transfers its phosphoryl group to the response regulator PmrA. "
        "Activated PmrA induces transcription of the dltABCD operon, which increases cell surface charge "
        "and confers bacterial resistance to cationic antimicrobial peptides."
    )
    def long_fn(is_cold=False):
        txt = long_text if not is_cold else f"{long_text} (run_{time.time()})"
        r = requests.post(f"{SERVER_URL}/api/extract", json={"text": txt, "system_mode": "nlp_baseline"})
        assert r.status_code == 200

    results.append(measure_runs("POST /api/extract (Long text, System A)", long_fn, runs=10))

    # 5. Longer Scientific Text (System C Hybrid)
    def hybrid_fn(is_cold=False):
        txt = long_text if not is_cold else f"{long_text} (run_{time.time()})"
        r = requests.post(f"{SERVER_URL}/api/extract", json={"text": txt, "system_mode": "hybrid"})
        assert r.status_code == 200

    results.append(measure_runs("POST /api/extract (Long text, System C Hybrid)", hybrid_fn, runs=10))

    # 6. Multi-file Upload Batch
    tmp1 = "/tmp/test_paper_1.txt"
    tmp2 = "/tmp/test_paper_2.txt"
    with open(tmp1, "w") as f:
        f.write("Exposure to hypoxia induces HIF1A stabilization. HIF1A activates VEGF expression.")
    with open(tmp2, "w") as f:
        f.write("VEGF secretion promotes endothelial cell proliferation and accelerates angiogenesis.")

    def upload_fn(is_cold=False):
        with open(tmp1, "rb") as f1, open(tmp2, "rb") as f2:
            files = [
                ("files", ("test_paper_1.txt", f1, "text/plain")),
                ("files", ("test_paper_2.txt", f2, "text/plain")),
            ]
            r = requests.post(f"{SERVER_URL}/api/upload", files=files)
            assert r.status_code == 200

    results.append(measure_runs("POST /api/upload (2 documents batch)", upload_fn, runs=5))

    # Clean up temp files
    if os.path.exists(tmp1): os.remove(tmp1)
    if os.path.exists(tmp2): os.remove(tmp2)

    # Print Table
    header = f"{'Endpoint / Workload':44s} | {'Cold':>8s} | {'Runs':>4s} | {'Median':>9s} | {'Mean':>9s} | {'p95':>9s} | {'Min':>9s}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(f"{r['name']:44s} | {r['cold_ms']:7.2f}ms | {r['runs']:4d} | {r['median_ms']:8.2f}ms | {r['mean_ms']:8.2f}ms | {r['p95_ms']:8.2f}ms | {r['min_ms']:8.2f}ms")
    print("=" * len(header))

if __name__ == "__main__":
    run_all_benchmarks()
