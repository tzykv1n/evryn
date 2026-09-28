#!/usr/bin/env python3
# evryn --help
# evryn -s all
# evryn -s flux
# evryn -s multivariate
# evryn -s nlp
# evryn -s hypothesize
# evryn view <image_path>
# evryn all

import os
import sys
import argparse
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evryn.core.config import EvrynConfig
from evryn.core.cache import EvrynCache
from evryn.ui.console import print_evryn_banner, print_box, print_table, console
from evryn.pipelines.flux_pipeline import run_flux_pipeline
from evryn.pipelines.multivariate_pipeline import run_multivariate_pipeline
from evryn.pipelines.nlp_pipeline import run_nlp_pipeline
from evryn.pipelines.evryn_pipeline import run_evryn_pipeline
from evryn.visualization.terminal_graphics import TerminalGraphicsRenderer, get_terminal_geometry


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


def cmd_hypothesize(args):
    is_scratch = _is_scratch_mode(args)
    cfg = EvrynConfig(seed=getattr(args, "seed", 42), verbose=getattr(args, "verbose", False))
    cfg.cache.force_rebuild = is_scratch
    cache = EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled, force_rebuild=is_scratch)
    run_evryn_pipeline(cfg, cache)


def cmd_view(args):
    target_w = getattr(args, "width", None)
    term_cols, term_rows = get_terminal_geometry()
    print_box(
        f"Terminal Graphics Viewer : {os.path.basename(args.image_path)}",
        f"Terminal Geometry: {term_cols}x{term_rows} | Rendering Mode: Adaptive",
    )
    renderer = TerminalGraphicsRenderer(target_width=target_w)
    rendered = renderer.render_image(args.image_path, max_width=target_w, center=True)
    sys.stdout.write(rendered + "\n")
    sys.stdout.flush()


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
    e_res = run_evryn_pipeline(cfg, cache)

    duration = time.time() - t0
    print_box(
        "EVRYN Suite Execution Complete",
        f"All 4 Core Subsystems Verified | Mode: {'from-scratch' if is_scratch else 'cached'} | Runtime: {duration:.2f}s | Output: {cfg.output_dir}",
    )


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

    p_hypo = subparsers.add_parser("hypothesize", help="Run end-to-end relation normalization & hypothesis generation")
    _add_scratch_opt(p_hypo)
    p_hypo.set_defaults(func=cmd_hypothesize)

    p_view = subparsers.add_parser("view", help="Render scientific figures directly in the terminal")
    p_view.add_argument("image_path", type=str, help="Path to PNG image to view")
    p_view.add_argument("--width", type=int, default=None, help="Target column width (default: automatic)")
    p_view.set_defaults(func=cmd_view)

    p_cache = subparsers.add_parser("cache", help="Manage EVRYN cache")
    p_cache.add_argument("--status", action="store_true", help="List active cache entries")
    p_cache.add_argument("--clear", action="store_true", help="Clear all cache entries")
    p_cache.add_argument("--stage", type=str, default=None, help="Clear specific cache stage")
    p_cache.set_defaults(func=cmd_cache)

    p_all = subparsers.add_parser("all", help="Execute full platform verification across all 4 modules")
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
