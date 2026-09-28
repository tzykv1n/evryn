# evryn higher-order
# evryn -s higher-order

import os
import json
from typing import Dict, Any, List

from ..core.config import EvrynConfig
from ..core.cache import EvrynCache
from ..ui.console import print_box, print_table, get_progress_bar
from ..nlp.higher_order.dataset import HigherOrderDatasetBuilder
from ..nlp.higher_order.auditor import CandidateAuditor
from ..nlp.higher_order.benchmark import HigherOrderBenchmarkRunner
from ..visualization.presenter import VisualArtifact, present_artifacts


def _display_higher_order_results(
    audit_data: Dict[str, Any],
    bench_results: List[Dict[str, Any]],
    artifacts: List[VisualArtifact],
    verbose: bool = False,
) -> None:
    audit_headers = ["Audit Dimension", "Value / Count", "Scientific Significance"]
    audit_rows = [
        ["Total Analyzed Candidates", str(audit_data["total_candidates"]), "Candidates flagged with joint coordination markers"],
        ["Unique Sentences", str(audit_data["unique_sentences"]), "Non-redundant linguistic contexts"],
        ["Unique Entity Tuples", str(audit_data["unique_entity_tuples"]), "Distinct entity pair configurations"],
        ["Explicit Causal Triggers", str(audit_data["explicit_causal_count"]), "Explicit causal verbs ('caused', 'induces', 'triggers')"],
        ["Implicit Causal Phrasing", str(audit_data["implicit_causal_count"]), "Domain-specific semantic causality without verb"],
        ["Nominal Conjunctions ('and', 'both')", str(audit_data["has_conjunction_count"]), "Syntactic coordination cues"],
        ["Temporal Confounding Cues", str(audit_data["has_temporal_count"]), "Temporal succession markers ('when', 'after')"],
        ["Negative Controls Added", str(audit_data["control_count"]), "Strict null controls (noun lists, temporal markers)"],
    ]
    print_table(audit_headers, audit_rows, title="Higher-Order Candidate Generation Audit (N = 208)")

    dist_headers = ["Candidate Category", "Count", "Structural Hypothesis", "Evidence Type"]
    dist_rows = []
    cat_desc = {
        "PAIRWISE_DECOMPOSABLE": ("Independent Parallel Causes", "Additive marginals: A -> C and B -> C"),
        "JOINT_CAUSE": ("Conjunctive Joint Causation", "Joint participation: {A, B} -> C"),
        "HIGHER_ORDER_INTERACTION": ("Synergistic / Nonlinear Co-Action", "Nonlinear interaction: A x B -> C"),
        "LINGUISTIC_COORDINATION": ("Syntactic Coordination (Non-Causal)", "Grammatical conjunction without joint causality"),
        "TEMPORAL_RELATION": ("Temporal Succession", "Chronological sequence mistaken for cause"),
        "CONFOUNDED": ("Latent Confounding", "Common unobserved factor / modifier"),
        "INSUFFICIENT_EVIDENCE": ("Insufficient Context", "Fragmentary or ambiguous evidence"),
    }
    for cat_name, count in audit_data["category_distribution"].items():
        hyp_str, ev_str = cat_desc.get(cat_name, ("Relational", "Evidence"))
        dist_rows.append([cat_name, str(count), hyp_str, ev_str])
    print_table(dist_headers, dist_rows, title="Higher-Order Category Distribution (Validated Gold)")

    dist_art = [a for a in artifacts if "distribution" in a.path]
    present_artifacts(dist_art, verbose=verbose)

    bench_headers = [
        "Method / Baseline Architecture",
        "Joint F1",
        "Interaction F1",
        "Pairwise Decomp F1",
        "Macro-F1",
        "False Joint Rate",
        "Exact Match",
    ]
    bench_rows = []
    for r in bench_results:
        bench_rows.append([
            r["baseline_name"],
            f"{r['joint_cause_f1']:.3f}",
            f"{r['higher_order_interaction_f1']:.3f}",
            f"{r['pairwise_decomposition_f1']:.3f}",
            f"{r['macro_f1']:.3f}",
            f"{r['false_joint_cause_rate']*100:.1f}%",
            f"{r['exact_structural_match']*100:.1f}%",
        ])
    print_table(bench_headers, bench_rows, title="Higher-Order Scientific NLP Benchmark Evaluation")

    comp_art = [a for a in artifacts if "comparison" in a.path]
    present_artifacts(comp_art, verbose=verbose)


def run_higher_order_pipeline(config: EvrynConfig, cache: EvrynCache) -> Dict[str, Any]:
    print_box(
        "Higher-Order Scientific NLP : Candidate Validation & FLUX Integration",
        "Auditing 208 Joint-Cause Candidates, Disambiguating Conjunction vs Synergy, Negative Controls",
        is_scratch=cache.force_rebuild,
    )

    p_dist = os.path.join(config.output_dir, "ho_candidate_distribution.png")
    p_comp = os.path.join(config.output_dir, "ho_nlp_benchmark_comparison.png")

    default_artifacts = [
        VisualArtifact(
            path=p_dist,
            title="Audited Category Distribution of 208 Joint-Cause Candidates",
            role="primary",
            description="Categorization across pairwise decomposable, joint cause, interaction, and linguistic coordination",
        ),
        VisualArtifact(
            path=p_comp,
            title="Higher-Order NLP Benchmark: Linguistic vs FLUX Evidence Integration",
            role="primary",
            description="Performance across 5 baselines showing dramatic reduction in false joint causation via FLUX evidence",
        ),
    ]

    cached_res = cache.get("benchmarks", f"ho_nlp_benchmark_{config.seed}")
    if cached_res is not None and not cache.force_rebuild:
        _display_higher_order_results(
            cached_res["audit_data"],
            cached_res["benchmark_results"],
            cached_res.get("artifacts", default_artifacts),
            verbose=config.verbose,
        )
        return cached_res

    os.makedirs(config.output_dir, exist_ok=True)
    results = {}
    with get_progress_bar("Executing Higher-Order NLP Pipeline") as prog:
        t_id = prog.add_task("Step 1: Extracting & Validating 208 Joint Candidates...", total=4)

        builder = HigherOrderDatasetBuilder(cache_dir="cache", force_rebuild=cache.force_rebuild)
        candidates = builder.build_dataset()
        prog.advance(t_id)

        prog.update(t_id, description="Step 2: Conducting Systematic Linguistic & Causal Audit...")
        auditor = CandidateAuditor()
        audit_data = auditor.audit(candidates)
        prog.advance(t_id)

        prog.update(t_id, description="Step 3: Benchmarking Baselines vs FLUX Evidence Integration...")
        runner = HigherOrderBenchmarkRunner()
        bench_evals = runner.run_all_baselines(candidates)
        bench_dicts = [b.to_dict() for b in bench_evals]
        prog.advance(t_id)

        prog.update(t_id, description="Step 4: Rendering Benchmark Figures & Saving State...")
        fig_paths = runner.plot_benchmark_figures(candidates, bench_evals, output_dir=config.output_dir)

        p_dataset_json = os.path.join(config.output_dir, "higher_order_nlp_dataset.json")
        with open(p_dataset_json, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in candidates], f, indent=2)

        results = {
            "audit_data": audit_data,
            "benchmark_results": bench_dicts,
            "candidate_count": len(candidates),
            "dataset_path": p_dataset_json,
            "distribution_plot": fig_paths["distribution"],
            "comparison_plot": fig_paths["comparison"],
            "artifacts": default_artifacts,
        }
        prog.advance(t_id)

    _display_higher_order_results(audit_data, bench_dicts, default_artifacts, verbose=config.verbose)
    cache.set("benchmarks", f"ho_nlp_benchmark_{config.seed}", results)
    return results
