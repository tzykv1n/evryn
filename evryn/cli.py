#!/usr/bin/env python3
# evryn --help
# evryn flux
# evryn multivariate
# evryn nlp
# evryn hypothesize
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
from evryn.visualization.terminal_graphics import TerminalGraphicsRenderer


def cmd_flux(args):
    cfg = EvrynConfig(seed=getattr(args, "seed", 42))
    cache = EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled, force_rebuild=getattr(args, "force", False))
    run_flux_pipeline(cfg, cache)


def cmd_multivariate(args):
    cfg = EvrynConfig(seed=getattr(args, "seed", 42))
    cache = EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled, force_rebuild=getattr(args, "force", False))
    run_multivariate_pipeline(cfg, cache)


def cmd_nlp(args):
    cfg = EvrynConfig(seed=getattr(args, "seed", 42))
    cache = EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled, force_rebuild=getattr(args, "force", False))
    run_nlp_pipeline(cfg, cache)


def cmd_hypothesize(args):
    cfg = EvrynConfig(seed=getattr(args, "seed", 42))
    cache = EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled, force_rebuild=getattr(args, "force", False))
    run_evryn_pipeline(cfg, cache)


def cmd_view(args):
    print_box(f"Terminal Graphics Viewer : {os.path.basename(args.image_path)}")
    renderer = TerminalGraphicsRenderer(target_width=getattr(args, "width", 76))
    rendered = renderer.render_image(args.image_path)
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
    cfg = EvrynConfig(seed=getattr(args, "seed", 42))
    cache = EvrynCache(cache_dir=cfg.cache.cache_dir, enabled=cfg.cache.enabled, force_rebuild=getattr(args, "force", False))

    print_evryn_banner("Full Platform Benchmark & Discovery Suite")
    t0 = time.time()

    f_res = run_flux_pipeline(cfg, cache)
    m_res = run_multivariate_pipeline(cfg, cache)
    n_res = run_nlp_pipeline(cfg, cache)
    e_res = run_evryn_pipeline(cfg, cache)

    duration = time.time() - t0
    print_box(
        "EVRYN Suite Execution Complete",
        f"All 4 Core Subsystems Verified | Runtime: {duration:.2f}s | Output: {cfg.output_dir}",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evryn",
        description="EVRYN : Unified Scientific Knowledge Discovery Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available EVRYN modules")

    p_flux = subparsers.add_parser("flux", help="Run Pairwise Causal FLUX benchmark & continual stream")
    p_flux.add_argument("--force", action="store_true", help="Force cache rebuild")
    p_flux.set_defaults(func=cmd_flux)

    p_multi = subparsers.add_parser("multivariate", help="Run Higher-Order FLUX multivariate & mechanism suite")
    p_multi.add_argument("--force", action="store_true", help="Force cache rebuild")
    p_multi.set_defaults(func=cmd_multivariate)

    p_nlp = subparsers.add_parser("nlp", help="Run Frozen Scientific NLP pairwise baseline & error taxonomy")
    p_nlp.add_argument("--force", action="store_true", help="Force cache rebuild")
    p_nlp.set_defaults(func=cmd_nlp)

    p_hypo = subparsers.add_parser("hypothesize", help="Run end-to-end relation normalization & hypothesis generation")
    p_hypo.add_argument("--force", action="store_true", help="Force cache rebuild")
    p_hypo.set_defaults(func=cmd_hypothesize)

    p_view = subparsers.add_parser("view", help="Render scientific figures directly in the terminal")
    p_view.add_argument("image_path", type=str, help="Path to PNG image to view")
    p_view.add_argument("--width", type=int, default=76, help="Target column width")
    p_view.set_defaults(func=cmd_view)

    p_cache = subparsers.add_parser("cache", help="Manage EVRYN cache")
    p_cache.add_argument("--status", action="store_true", help="List active cache entries")
    p_cache.add_argument("--clear", action="store_true", help="Clear all cache entries")
    p_cache.add_argument("--stage", type=str, default=None, help="Clear specific cache stage")
    p_cache.set_defaults(func=cmd_cache)

    p_all = subparsers.add_parser("all", help="Execute full platform verification across all 4 modules")
    p_all.add_argument("--force", action="store_true", help="Force cache rebuild")
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
