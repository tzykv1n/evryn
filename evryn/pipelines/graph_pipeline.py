# evryn graph
# evryn -s graph

import os
from typing import Dict, Any, List, Optional
from rich.table import Table

from ..ui.console import console, print_box, print_table
from ..core.config import EvrynConfig
from ..core.cache import EvrynCache
from ..visualization.presenter import VisualArtifact, present_artifacts
from ..graph_flux.synthetic_corpus import MultiSentenceBenchmarkGenerator
from ..graph_flux.evaluator import GraphFluxEvaluator
from ..graph_flux.reporting import GraphFluxReportGenerator
from ..nlp.higher_order.types import HigherOrderCategory


def run_graph_flux_pipeline(
    config: Optional[EvrynConfig] = None,
    cache: Optional[EvrynCache] = None,
    from_scratch: bool = False,
    verbose: bool = False,
    n_documents: int = 60,
) -> Dict[str, Any]:
    cfg = config or EvrynConfig()
    cache_obj = cache or EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled, force_rebuild=from_scratch)
    is_scratch = from_scratch or cfg.cache.force_rebuild or cache_obj.force_rebuild
    cache_key = f"graph_flux_benchmark_docs_{n_documents}_s{cfg.seed}"

    if not is_scratch:
        cached_data = cache_obj.get("benchmarks", cache_key)
        if cached_data is not None:
            console.print("[dim cyan][*] Loading Graph-FLUX multi-sentence benchmark from cache...[/dim cyan]")
            _present_graph_flux_results(cached_data, verbose=verbose or cfg.verbose)
            return cached_data

    print_box("Graph-FLUX: Cross-Sentence Higher-Order Causal Discovery", is_scratch=is_scratch)
    console.print(f"[bold cyan][*] Generating multi-sentence corpus ({n_documents} synthetic documents across 11 mechanisms)...[/bold cyan]")

    generator = MultiSentenceBenchmarkGenerator(seed=cfg.seed)
    docs = generator.generate_corpus(n_documents=n_documents)

    evaluator = GraphFluxEvaluator(random_state=cfg.seed)
    results, candidates = evaluator.run_benchmark(docs)

    console.print("[bold cyan][*] Evaluating NLP extraction noise robustness...[/bold cyan]")
    noise_results = evaluator.run_noise_robustness_experiment(docs[:20], noise_levels=[0.0, 0.05, 0.10, 0.20, 0.30])

    console.print("[bold cyan][*] Running feature ablation across Graph-FLUX evidence components...[/bold cyan]")
    ablations = evaluator.run_feature_ablation(candidates)

    console.print("[bold cyan][*] Rendering multi-sentence causal figures and benchmark artifacts...[/bold cyan]")
    report_gen = GraphFluxReportGenerator(output_dir=cfg.output_dir)
    fig_paths = report_gen.plot_all_figures(results, candidates, noise_results, ablations)
    report_file = report_gen.save_benchmark_report(results, candidates, noise_results, ablations)

    pipeline_payload = {
        "results": [r.to_dict() for r in results],
        "total_documents": len(docs),
        "total_candidates": len(candidates),
        "candidate_recall": results[0].candidate_recall,
        "noise_robustness": {str(k): v.to_dict() for k, v in noise_results.items()},
        "ablations": ablations,
        "figure_paths": fig_paths,
        "report_file": report_file,
        "top_hypotheses": [
            c.to_dict() for c in candidates
            if c.predicted_category in (HigherOrderCategory.JOINT_CAUSE, HigherOrderCategory.HIGHER_ORDER_INTERACTION)
        ][:8],
    }

    cache_obj.set("benchmarks", cache_key, pipeline_payload)
    _present_graph_flux_results(pipeline_payload, verbose=verbose or cfg.verbose)
    return pipeline_payload


def _present_graph_flux_results(data: Dict[str, Any], verbose: bool = False) -> None:
    results = data.get("results", [])

    stat_table = Table(
        title="Graph-FLUX Corpus & Candidate Statistics",
        title_style="bold magenta",
        header_style="bold cyan",
        border_style="magenta",
        show_lines=True,
    )
    stat_table.add_column("Metric", style="white")
    stat_table.add_column("Value", justify="right", style="cyan")
    stat_table.add_column("Details", style="dim white")

    stat_table.add_row("Processed Documents", str(data.get("total_documents", 0)), "Multi-sentence abstracts across 11 mechanisms")
    stat_table.add_row("Generated Candidates", str(data.get("total_candidates", 0)), "Graph-locality constrained (d <= 3)")
    stat_table.add_row("Candidate Recall", f"{data.get('candidate_recall', 0.0) * 100:.1f}%", "Coverage of true distributed joint causes")

    console.print(stat_table)
    console.print()

    bench_table = Table(
        title="Graph-FLUX Cross-Sentence Benchmark Evaluation",
        title_style="bold magenta",
        header_style="bold cyan",
        border_style="magenta",
        show_lines=True,
    )
    bench_table.add_column("Baseline Architecture", style="white")
    bench_table.add_column("Joint F1", justify="right", style="cyan")
    bench_table.add_column("Inter F1", justify="right", style="purple")
    bench_table.add_column("Macro-F1", justify="right", style="dim white")
    bench_table.add_column("Exact Match", justify="right", style="cyan")
    bench_table.add_column("False Joint Rate", justify="right", style="yellow")
    bench_table.add_column("Cascade Error", justify="right", style="red")
    bench_table.add_column("Confounder Error", justify="right", style="red")

    for r in results:
        f_rate = r.get("false_joint_rate", 0.0)
        c_rate = r.get("cascade_as_joint_error_rate", 0.0)
        u_rate = r.get("confounder_as_joint_error_rate", 0.0)

        f_style = "[bold green]0.0%[/bold green]" if f_rate == 0.0 else f"[yellow]{f_rate * 100:.1f}%[/yellow]" if f_rate < 0.2 else f"[red]{f_rate * 100:.1f}%[/red]"
        c_style = "[bold green]0.0%[/bold green]" if c_rate == 0.0 else f"[red]{c_rate * 100:.1f}%[/red]"
        u_style = "[bold green]0.0%[/bold green]" if u_rate == 0.0 else f"[red]{u_rate * 100:.1f}%[/red]"

        bench_table.add_row(
            r.get("baseline_name", ""),
            f"{r.get('joint_f1', 0.0):.3f}",
            f"{r.get('interaction_f1', 0.0):.3f}",
            f"{r.get('macro_f1', 0.0):.3f}",
            f"{r.get('exact_structural_match', 0.0) * 100:.1f}%",
            f_style,
            c_style,
            u_style,
        )

    console.print(bench_table)
    console.print()

    hypotheses = data.get("top_hypotheses", [])
    if hypotheses:
        hypo_table = Table(
            title="Discovered Higher-Order Hypotheses (Marked UNVALIDATED_HYPOTHESIS)",
            title_style="bold magenta",
            header_style="bold cyan",
            border_style="magenta",
            show_lines=True,
        )
        hypo_table.add_column("Hypothesis Formulation", style="bold cyan")
        hypo_table.add_column("Pattern", style="purple")
        hypo_table.add_column("PID Synergy", justify="right", style="white")
        hypo_table.add_column("ΔR² Gain", justify="right", style="white")
        hypo_table.add_column("Validation Status", style="dim yellow")

        for h in hypotheses[:6]:
            srcs = ", ".join(h.get("source_names", []))
            tgt = h.get("target_name", "")
            hypo_str = f"{{{srcs}}} -> {tgt}"
            ev = h.get("evidence", {})
            hypo_table.add_row(
                hypo_str,
                h.get("generation_pattern", ""),
                f"{ev.get('flux_pid_synergy', 0.0):.3f}",
                f"{ev.get('flux_delta_r2', 0.0):.3f}",
                h.get("validation_status", "UNVALIDATED_HYPOTHESIS"),
            )
        console.print(hypo_table)
        console.print()

    fig_paths = data.get("figure_paths", [])
    if fig_paths:
        artifacts = [
            VisualArtifact(
                path=fig_paths[0],
                title="Example Multi-Sentence Causal Graph",
                role="primary",
                description="Cross-sentence convergence structure {A, B} -> P -> C",
            ),
            VisualArtifact(
                path=fig_paths[2],
                title="Graph-FLUX Evidence Fusion Flow",
                role="primary",
                description="Fusion of linguistic, graph structure, and FLUX statistical evidence",
            ),
            VisualArtifact(
                path=fig_paths[4],
                title="Joint Cause F1 Across Evidence Sources",
                role="primary",
                description="Performance comparison showing impact of graph context and FLUX",
            ),
            VisualArtifact(
                path=fig_paths[5],
                title="False Joint Rate Reduction",
                role="primary",
                description="Graph proximity vs FLUX statistical evidence",
            ),
            VisualArtifact(
                path=fig_paths[7],
                title="NLP Extraction Noise Robustness",
                role="primary",
                description="Performance degradation curve across injected relation errors",
            ),
        ]
        present_artifacts(artifacts, verbose=verbose)
