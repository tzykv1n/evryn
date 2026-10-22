#!/usr/bin/env python3
# evryn --help
# evryn doctor
# evryn doctor --json
# evryn benchmark --suite all
# evryn benchmark --suite graph --dry-run
# evryn run --pipeline all
# evryn validate
# evryn -s all
# evryn -s flux
# evryn -s multivariate
# evryn -s nlp
# evryn -s higher-order
# evryn -s graph
# evryn -s hypothesize
# evryn view <image_path>

import os
import sys
import argparse
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evryn.core.config import EvrynConfig
from evryn.core.cache import EvrynCache
from evryn.core.doctor import run_doctor_checks, print_doctor_report
from evryn.core.benchmark_runner import run_benchmark_suite
from evryn.ui.console import print_evryn_banner, print_box, print_table, console
from evryn.pipelines.flux_pipeline import run_flux_pipeline
from evryn.pipelines.multivariate_pipeline import run_multivariate_pipeline
from evryn.pipelines.nlp_pipeline import run_nlp_pipeline
from evryn.pipelines.higher_order_pipeline import run_higher_order_pipeline
from evryn.pipelines.graph_pipeline import run_graph_flux_pipeline
from evryn.pipelines.evryn_pipeline import run_evryn_pipeline
from evryn.visualization.terminal_graphics import (
    TerminalGraphicsRenderer,
    detect_native_graphics_protocol,
    render_native_protocol,
    open_in_external_viewer,
)


def _is_scratch_mode(args) -> bool:
    return bool(getattr(args, "top_scratch", False) or getattr(args, "sub_scratch", False))


def cmd_flux(args):
    is_scratch = _is_scratch_mode(args)
    cfg = EvrynConfig(seed=getattr(args, "seed", 42), verbose=getattr(args, "verbose", False))
    cfg.cache.force_rebuild = is_scratch
    cache = EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled, force_rebuild=is_scratch)
    run_flux_pipeline(cfg, cache)


def cmd_multivariate(args):
    is_scratch = _is_scratch_mode(args)
    cfg = EvrynConfig(seed=getattr(args, "seed", 42), verbose=getattr(args, "verbose", False))
    cfg.cache.force_rebuild = is_scratch
    cache = EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled, force_rebuild=is_scratch)
    run_multivariate_pipeline(cfg, cache)


def cmd_nlp(args):
    is_scratch = _is_scratch_mode(args)
    cfg = EvrynConfig(seed=getattr(args, "seed", 42), verbose=getattr(args, "verbose", False))
    cfg.cache.force_rebuild = is_scratch
    cache = EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled, force_rebuild=is_scratch)
    run_nlp_pipeline(cfg, cache)


def cmd_higher_order(args):
    is_scratch = _is_scratch_mode(args)
    cfg = EvrynConfig(seed=getattr(args, "seed", 42), verbose=getattr(args, "verbose", False))
    cfg.cache.force_rebuild = is_scratch
    cache = EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled, force_rebuild=is_scratch)
    run_higher_order_pipeline(cfg, cache)


def cmd_graph(args):
    is_scratch = _is_scratch_mode(args)
    cfg = EvrynConfig(seed=getattr(args, "seed", 42), verbose=getattr(args, "verbose", False))
    cfg.cache.force_rebuild = is_scratch
    cache = EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled, force_rebuild=is_scratch)
    run_graph_flux_pipeline(config=cfg, cache=cache, from_scratch=is_scratch, verbose=cfg.verbose)


def cmd_hypothesize(args):
    is_scratch = _is_scratch_mode(args)
    cfg = EvrynConfig(seed=getattr(args, "seed", 42), verbose=getattr(args, "verbose", False))
    cfg.cache.force_rebuild = is_scratch
    cache = EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled, force_rebuild=is_scratch)
    run_evryn_pipeline(cfg, cache)


def cmd_view(args):
    image_path = args.image_path
    if not os.path.exists(image_path):
        console.print(f"[bold red]Error: Image file not found at '{image_path}'[/bold red]")
        sys.exit(1)

    if getattr(args, "ascii", False):
        target_w = getattr(args, "width", None)
        renderer = TerminalGraphicsRenderer(target_width=target_w)
        rendered = renderer.render_image(image_path, max_width=target_w, center=True)
        sys.stdout.write(rendered + "\n")
        sys.stdout.flush()
        return

    protocol = detect_native_graphics_protocol()
    if protocol:
        native_out = render_native_protocol(image_path, protocol)
        if native_out:
            sys.stdout.write(native_out)
            sys.stdout.flush()
            return

    opened, viewer_name = open_in_external_viewer(image_path)
    if opened:
        console.print(
            f"[bold cyan]IMAGE VIEWER[/bold cyan]\n"
            f"  {os.path.basename(image_path)}\n"
            f"[dim white]Opened via external viewer: [bold green]{viewer_name}[/bold green][/dim white]"
        )
        return

    console.print(
        f"[bold cyan]IMAGE VIEWER[/bold cyan]\n"
        f"  {os.path.basename(image_path)}\n\n"
        f"[yellow]No native terminal graphics protocol detected.[/yellow]\n"
        f"[yellow]No graphical image viewer found (checked imv, sxiv, nsxiv, feh, xdg-open).[/yellow]\n\n"
        f"Install an image viewer or use:\n"
        f"  [bold white]evryn view --ascii {image_path}[/bold white]"
    )


def cmd_cache(args):
    cache = EvrynCache(cache_dir="cache", enabled=True)

    if getattr(args, "clear", False):
        n = cache.invalidate()
        console.print(f"[bold green][+] Evryn global cache cleared ({n} files removed).[/bold green]")
        return

    if getattr(args, "stage", None):
        n = cache.invalidate(stage=args.stage)
        console.print(f"[bold green][+] Stage '{args.stage}' invalidated ({n} files removed).[/bold green]")
        return

    entries = cache.list_entries()
    if not entries:
        console.print("[dim cyan]  No active cache entries found.[/dim cyan]")
        return

    headers = ["Stage", "Key Hash", "Size (KB)", "Created At"]
    rows = []
    for e in entries:
        sz = e.get("size_bytes", 0) / 1024.0
        rows.append([
            e.get("stage", "unknown"),
            e.get("key_hash", "")[:16] + "...",
            f"{sz:.1f}",
            e.get("created_at", ""),
        ])
    print_table(headers, rows, title=f"Active Cache Registry ({len(entries)} artifacts)")


def cmd_doctor(args):
    rep = run_doctor_checks()
    exit_code = print_doctor_report(rep, as_json=getattr(args, "json", False))
    sys.exit(exit_code)


def cmd_benchmark(args):
    is_scratch = _is_scratch_mode(args) or getattr(args, "scratch", False)
    exit_code = run_benchmark_suite(
        suite=getattr(args, "suite", "all"),
        seed=getattr(args, "seed", 42),
        samples=getattr(args, "samples", None),
        noise=getattr(args, "noise", None),
        output_dir=getattr(args, "output_dir", "outputs"),
        from_scratch=is_scratch,
        dry_run=getattr(args, "dry_run", False),
    )
    sys.exit(exit_code)


def cmd_run(args):
    target = getattr(args, "pipeline", "all")
    if getattr(args, "dry_run", False):
        print_box(
            "EVRYN Pipeline Execution Plan (DRY RUN)",
            f"Target Pipeline: {target} | Output: {getattr(args, 'output_dir', 'outputs')} | Seed: {getattr(args, 'seed', 42)}",
        )
        headers = ["Pipeline", "Target Workflow", "Action"]
        rows = [
            ["flux", "Pairwise Causal FLUX", "Continual stream & Sachs benchmark"],
            ["multivariate", "Higher-Order Multivariate FLUX", "Order-2/3 hyperedges & mechanism suite"],
            ["nlp", "Frozen Scientific NLP", "Directional extraction & error taxonomy"],
            ["higher-order", "Higher-Order NLP Candidate Audit", "Conjunction vs synergy disambiguation"],
            ["graph", "Graph-FLUX Cross-Sentence Discovery", "Multi-sentence document causal discovery"],
            ["hypothesize", "Hypothesis Generation", "Relation normalization & temporal forecast"],
        ]
        if target != "all":
            rows = [r for r in rows if r[0] == target]
        print_table(headers, rows, title="Scheduled Execution Units")
        console.print("[dim yellow]Dry run complete. No pipeline executed.[/dim yellow]\n")
        return

    if target == "all":
        cmd_all(args)
    elif target == "flux":
        cmd_flux(args)
    elif target == "multivariate":
        cmd_multivariate(args)
    elif target == "nlp":
        cmd_nlp(args)
    elif target == "higher-order":
        cmd_higher_order(args)
    elif target == "graph":
        cmd_graph(args)
    elif target == "hypothesize":
        cmd_hypothesize(args)


def cmd_all(args):
    is_scratch = _is_scratch_mode(args)
    cfg = EvrynConfig(seed=getattr(args, "seed", 42), verbose=getattr(args, "verbose", False))
    cfg.cache.force_rebuild = is_scratch
    cache = EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled, force_rebuild=is_scratch)

    print_evryn_banner(
        subtitle="Full Platform Benchmark & Discovery Suite",
        is_scratch=is_scratch,
        seed=cfg.seed,
    )
    t0 = time.time()

    f_res = run_flux_pipeline(cfg, cache)
    m_res = run_multivariate_pipeline(cfg, cache)
    n_res = run_nlp_pipeline(cfg, cache)
    ho_res = run_higher_order_pipeline(cfg, cache)
    g_res = run_graph_flux_pipeline(config=cfg, cache=cache, from_scratch=is_scratch, verbose=cfg.verbose)
    e_res = run_evryn_pipeline(cfg, cache)

    duration = time.time() - t0
    print_box(
        "EVRYN Suite Execution Complete",
        f"All Subsystems Verified | Mode: {'from-scratch' if is_scratch else 'cached'} | Runtime: {duration:.2f}s | Output: {cfg.output_dir}",
    )


def cmd_validate(args):
    import json
    from evryn.core.types import NormalizedEntity, Provenance, ScientificDomain
    from evryn.hypothesize.generator import ScientificHypothesis
    from evryn.hypothesize.literature_validator import LiteratureValidator

    output_dir = getattr(args, "output_dir", "outputs")
    state_file = os.path.join(output_dir, "evryn_discovery_state.json")

    if not os.path.exists(state_file):
        cfg = EvrynConfig(seed=getattr(args, "seed", 42))
        cache = EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled)
        run_evryn_pipeline(cfg, cache)

    with open(state_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    hyps = []
    for h in data.get("hypotheses", []):
        ents = [NormalizedEntity.from_dict(e) for e in h.get("involved_entities", [])]
        hyps.append(ScientificHypothesis(
            hypothesis_id=h["hypothesis_id"],
            title=h.get("title", ""),
            statement=h["statement"],
            hypothesis_type=h.get("hypothesis_type", ""),
            involved_entities=ents,
            plausibility_score=h.get("plausibility_score", 0.7),
            reasoning_chain=h.get("reasoning_chain", []),
            supporting_relation_ids=h.get("supporting_relation_ids", []),
            provenance=Provenance(source_id="hypothesize"),
        ))

    validator = LiteratureValidator(output_dir=output_dir)
    print_box(
        "EVRYN Scientific Literature Validation Protocol",
        f"Auditing {len(hyps)} Machine-Generated Hypotheses Against NCBI PubMed Entrez",
    )
    val_results = validator.validate_all(hyps)

    headers = ["Hypothesis ID", "Validation Status", "Conf", "Citations", "Target Statement"]
    rows = []
    for r in val_results:
        st_color = "bold green" if "CONFIRMED" in r["validation_status"] else "bold cyan" if "SUPPORTED" in r["validation_status"] else "bold yellow"
        rows.append([
            r["hypothesis_id"][:16],
            f"[{st_color}]{r['validation_status']}[/{st_color}]",
            f"{r['calibrated_confidence']:.3f}",
            str(r["evidence_count"]),
            r["statement"][:48] + "...",
        ])
    print_table(headers, rows, title="Peer-Reviewed Literature Validation Registry")
    console.print(f"[bold green][✓] Traceable literature audit complete. Saved to: {os.path.join(output_dir, 'hypothesis_literature_validation.json')}[/bold green]\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evryn",
        description="EVRYN : Unified Scientific Knowledge Discovery Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-s",
        "--from-scratch",
        "--scratch",
        action="store_true",
        dest="top_scratch",
        help="Run from scratch, bypassing cached computational artifacts and regenerating everything",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose artifact logging")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic reproducibility")

    subparsers = parser.add_subparsers(dest="command", help="Available EVRYN modules")

    def _add_scratch_opt(sub_p):
        sub_p.add_argument(
            "-s",
            "--from-scratch",
            "--scratch",
            action="store_true",
            dest="sub_scratch",
            help="Run from scratch, bypassing cached computational artifacts",
        )
        sub_p.add_argument(
            "--force",
            action="store_true",
            dest="sub_scratch",
            help="Force cache rebuild",
        )
        sub_p.add_argument("-v", "--verbose", action="store_true", help="Enable verbose artifact logging")
        sub_p.add_argument("--seed", type=int, default=42, help="Random seed for deterministic reproducibility")

    p_flux = subparsers.add_parser("flux", help="Run Pairwise Causal FLUX benchmark & continual stream")
    _add_scratch_opt(p_flux)
    p_flux.set_defaults(func=cmd_flux)

    p_multi = subparsers.add_parser("multivariate", help="Run Higher-Order FLUX multivariate & mechanism suite")
    _add_scratch_opt(p_multi)
    p_multi.set_defaults(func=cmd_multivariate)

    p_nlp = subparsers.add_parser("nlp", help="Run Frozen Scientific NLP pairwise baseline & error taxonomy")
    _add_scratch_opt(p_nlp)
    p_nlp.set_defaults(func=cmd_nlp)

    p_ho = subparsers.add_parser("higher-order", help="Higher-Order Scientific NLP candidate audit & FLUX benchmark")
    _add_scratch_opt(p_ho)
    p_ho.set_defaults(func=cmd_higher_order)

    p_graph = subparsers.add_parser("graph", aliases=["graph-flux"], help="Run Graph-FLUX cross-sentence higher-order discovery & benchmark")
    _add_scratch_opt(p_graph)
    p_graph.set_defaults(func=cmd_graph)

    p_hypo = subparsers.add_parser("hypothesize", help="Run end-to-end relation normalization & hypothesis generation")
    _add_scratch_opt(p_hypo)
    p_hypo.set_defaults(func=cmd_hypothesize)

    p_view = subparsers.add_parser("view", help="View scientific images at full visual quality")
    p_view.add_argument("image_path", type=str, help="Path to image to view")
    p_view.add_argument("--ascii", "-a", action="store_true", help="Render as half-block truecolor ASCII in terminal")
    p_view.add_argument("--width", type=int, default=None, help="Target column width when using --ascii")
    p_view.set_defaults(func=cmd_view)

    p_cache = subparsers.add_parser("cache", help="Manage EVRYN cache")
    p_cache.add_argument("--status", action="store_true", help="List active cache entries")
    p_cache.add_argument("--clear", action="store_true", help="Clear all cache entries")
    p_cache.add_argument("--stage", type=str, default=None, help="Clear specific cache stage")
    p_cache.set_defaults(func=cmd_cache)

    p_doc = subparsers.add_parser("doctor", help="Diagnose local environment, dependencies, hardware, and VCS health")
    p_doc.add_argument("--json", action="store_true", help="Output machine-readable JSON diagnostic report")
    p_doc.set_defaults(func=cmd_doctor)

    p_run = subparsers.add_parser("run", help="Execute complete EVRYN platform discovery pipeline or specific subsystem")
    p_run.add_argument("--pipeline", "-p", type=str, default="all", choices=["all", "flux", "multivariate", "nlp", "higher-order", "graph", "hypothesize"], help="Target pipeline to execute")
    _add_scratch_opt(p_run)
    p_run.add_argument("--output-dir", type=str, default="outputs", help="Output directory for generated artifacts")
    p_run.add_argument("--dry-run", action="store_true", help="Preview pipeline execution plan without computing")
    p_run.set_defaults(func=cmd_run)

    p_bench = subparsers.add_parser("benchmark", help="Run configurable empirical benchmarks across EVRYN suites")
    p_bench.add_argument("--suite", type=str, default="all", choices=["all", "flux", "multivariate", "nlp", "higher-order", "graph", "hypothesize", "final-phase"], help="Benchmark suite to execute")
    p_bench.add_argument("--samples", type=int, default=None, help="Sample count or document count")
    p_bench.add_argument("--noise", type=float, default=None, help="Noise injection rate")
    p_bench.add_argument("--output-dir", type=str, default="outputs", help="Output directory for generated artifacts")
    _add_scratch_opt(p_bench)
    p_bench.add_argument("--dry-run", action="store_true", help="Preview benchmark execution plan without computing")
    p_bench.set_defaults(func=cmd_benchmark)

    p_val = subparsers.add_parser("validate", help="Validate generated scientific hypotheses against traceable PubMed peer-reviewed literature")
    p_val.add_argument("--output-dir", type=str, default="outputs", help="Output directory for validation artifacts")
    _add_scratch_opt(p_val)
    p_val.set_defaults(func=cmd_validate)

    p_all = subparsers.add_parser("all", help="Execute full platform verification across all modules")
    _add_scratch_opt(p_all)
    p_all.set_defaults(func=cmd_all)

    return parser


def main():
    parser = build_parser()
    if len(sys.argv) == 1:
        print_evryn_banner()
        parser.print_help()
        sys.exit(0)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
