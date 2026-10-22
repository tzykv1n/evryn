# evryn benchmark --suite all
# evryn benchmark --suite graph --seed 42 --dry-run

import os
import sys
import time
from typing import Dict, Any, Optional

from evryn.core.config import EvrynConfig
from evryn.core.cache import EvrynCache
from evryn.ui.console import console, print_box, print_table
from evryn.pipelines.flux_pipeline import run_flux_pipeline
from evryn.pipelines.multivariate_pipeline import run_multivariate_pipeline
from evryn.pipelines.nlp_pipeline import run_nlp_pipeline
from evryn.pipelines.higher_order_pipeline import run_higher_order_pipeline
from evryn.pipelines.graph_pipeline import run_graph_flux_pipeline
from evryn.pipelines.evryn_pipeline import run_evryn_pipeline
from evryn.causal.experiments.run_final_benchmark import run_final_benchmark_suite


SUITE_PLANS = {
    "flux": {
        "name": "Pairwise Causal FLUX Stream",
        "description": "Evidence matching and continual adaptation across 8 sequential SCM tasks",
        "default_samples": 800,
        "figures": ["continual_flux_results.png"],
    },
    "multivariate": {
        "name": "Higher-Order Multivariate FLUX",
        "description": "Order-2 and Order-3 hyperedge discovery across 11 synthetic mechanisms",
        "default_samples": 500,
        "figures": ["higher_order_mechanisms.png"],
    },
    "nlp": {
        "name": "Frozen Scientific NLP Extraction",
        "description": "Directional causal relation classification on SemEval-2010 Task 8 test set (2,717 instances)",
        "default_samples": 2717,
        "figures": ["nlp_confusion_matrix.png", "nlp_baseline_comparison.png"],
    },
    "higher-order": {
        "name": "Higher-Order Scientific NLP Audit",
        "description": "Disambiguating conjunctions from causal interactions across 208 audited candidates",
        "default_samples": 208,
        "figures": ["ho_candidate_distribution.png", "ho_nlp_benchmark_comparison.png"],
    },
    "graph": {
        "name": "Graph-FLUX Cross-Sentence Discovery",
        "description": "Multi-sentence document causal discovery, cross-sentence candidate recall, and noise sweeps",
        "default_samples": 60,
        "figures": [
            "fig_graph_example_multisentence.png",
            "fig_graph_evidence_flow.png",
            "fig_graph_joint_f1_by_evidence.png",
            "fig_graph_false_joint_rate.png",
            "fig_graph_nlp_noise_robustness.png",
        ],
    },
    "hypothesize": {
        "name": "End-to-End Hypothesis Generation",
        "description": "Relation canonicalization, family discovery, and temporal forecasting for 2028-2029",
        "default_samples": 8,
        "figures": ["evryn_temporal_forecast.png"],
    },
    "final-phase": {
        "name": "Heavy Synthetic HCAM & Sachs Ensemble Suite",
        "description": "Full multi-seed NOTEARS, HCAM, Sachs protein-signaling, and nested feature ablations",
        "default_samples": 1000,
        "figures": ["fig1_independent_benchmark.png", "fig4_confounding_robustness.png"],
    },
}


def run_benchmark_suite(
    suite: str = "all",
    seed: int = 42,
    samples: Optional[int] = None,
    noise: Optional[float] = None,
    output_dir: str = "outputs",
    from_scratch: bool = False,
    dry_run: bool = False,
) -> int:
    target_suites = list(SUITE_PLANS.keys()) if suite == "all" else [suite]

    if suite != "all" and suite not in SUITE_PLANS:
        console.print(f"[bold red]Error: Unknown benchmark suite '{suite}'. Valid options: {list(SUITE_PLANS.keys()) + ['all']}[/bold red]")
        return 1

    os.makedirs(output_dir, exist_ok=True)

    if dry_run:
        print_box(
            "EVRYN Benchmark Execution Plan (DRY RUN)",
            f"Configured Seed: {seed} | Output Directory: {output_dir} | Mode: {'From-Scratch' if from_scratch else 'Cached'}",
        )
        headers = ["Suite ID", "Suite Name", "Sample Scope", "Key Figures Target"]
        rows = []
        for s in target_suites:
            plan = SUITE_PLANS[s]
            sm = samples if samples is not None else plan["default_samples"]
            figs = ", ".join(plan["figures"][:2]) + ("..." if len(plan["figures"]) > 2 else "")
            rows.append([s, plan["name"], f"N={sm}", figs])
        print_table(headers, rows, title="Planned Benchmark Modules")
        console.print("[dim yellow]Dry run complete. No experiments were executed and no files were modified.[/dim yellow]\n")
        return 0

    print_box(
        "EVRYN Automated Benchmark Suite Execution",
        f"Active Suite: {suite.upper()} | Seed: {seed} | Target Directory: {output_dir}",
    )

    cfg = EvrynConfig(seed=seed)
    cfg.cache.force_rebuild = from_scratch
    cfg.output_dir = output_dir
    cache = EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled, force_rebuild=from_scratch)

    start_time = time.time()
    completed = []

    try:
        for s in target_suites:
            console.print(f"\n[bold cyan]▶ Launching Benchmark Module: [white]{SUITE_PLANS[s]['name']}[/white][/bold cyan]")
            t0 = time.time()
            if s == "flux":
                run_flux_pipeline(cfg, cache)
            elif s == "multivariate":
                run_multivariate_pipeline(cfg, cache)
            elif s == "nlp":
                run_nlp_pipeline(cfg, cache)
            elif s == "higher-order":
                run_higher_order_pipeline(cfg, cache)
            elif s == "graph":
                docs = samples if samples is not None else 60
                run_graph_flux_pipeline(config=cfg, cache=cache, from_scratch=from_scratch, verbose=cfg.verbose, n_documents=docs)
            elif s == "hypothesize":
                run_evryn_pipeline(cfg, cache)
            elif s == "final-phase":
                sm = samples if samples is not None else 500
                run_final_benchmark_suite(seeds=1, samples=sm, noise=noise if noise is not None else 0.25, max_order=3)
            elapsed = time.time() - t0
            completed.append((s, SUITE_PLANS[s]["name"], f"{elapsed:.2f}s", "PASSED"))
    except Exception as e:
        console.print(f"[bold red]Benchmark module '{s}' failed with error: {e}[/bold red]")
        return 1

    total_elapsed = time.time() - start_time
    headers = ["Suite", "Module Name", "Runtime", "Status"]
    rows = [[c[0], c[1], c[2], f"[bold green]{c[3]}[/bold green]"] for c in completed]
    print_table(headers, rows, title=f"Benchmark Execution Summary ({total_elapsed:.2f}s elapsed)")
    console.print(f"[bold green][✓] All {len(completed)} requested benchmark suites successfully completed.[/bold green]\n")
    return 0
