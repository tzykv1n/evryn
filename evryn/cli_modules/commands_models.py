# evryn cli_modules commands_models
# pytest tests/test_cli_commands.py

import json
import sys
from typing import Any
import numpy as np
from rich.console import Console
from rich.table import Table

from evryn.models.registry import get_model_registry
from evryn.cli_modules.themes import get_theme


def handle_models_command(args: Any):
    console = Console()
    palette = get_theme(getattr(args, "theme", "default"))
    registry = get_model_registry()

    action = getattr(args, "models_action", "list") or "list"

    if action == "list":
        models = registry.list_models()
        if getattr(args, "json", False):
            print(json.dumps({"models": models}, indent=2))
            return

        table = Table(title="EVRYN Model Registry", border_style=palette.primary)
        table.add_column("Model Name", style=palette.primary, no_wrap=True)
        table.add_column("Architecture Type", style=palette.secondary)
        table.add_column("Status", style=palette.success)

        for m in models:
            stat_style = palette.success if m["status"] == "ready" else palette.warning
            table.add_row(m["name"], m["type"], f"[{stat_style}]{m['status']}[/{stat_style}]")

        console.print(table)

    elif action == "info":
        model_name = getattr(args, "model_name", None)
        if not model_name:
            console.print(f"[{palette.danger}]Error: model name required.[/{palette.danger}]")
            sys.exit(1)

        try:
            mod = registry.get(model_name)
        except KeyError as e:
            console.print(f"[{palette.danger}]{e}[/{palette.danger}]")
            sys.exit(1)

        info = {
            "name": model_name,
            "class": type(mod).__name__,
            "module": type(mod).__module__,
        }
        if hasattr(mod, "model_name"):
            info["base_checkpoint"] = getattr(mod, "model_name")
        if hasattr(mod, "abstention_threshold"):
            info["abstention_threshold"] = getattr(mod, "abstention_threshold")
        if hasattr(mod, "weights"):
            info["calibrated_weights"] = [round(float(w), 4) for w in getattr(mod, "weights")]

        if getattr(args, "json", False):
            print(json.dumps(info, indent=2))
            return

        console.print(f"[{palette.primary} bold]Model Specification: {model_name}[/{palette.primary} bold]")
        for k, v in info.items():
            console.print(f"  [{palette.secondary}]{k}:[/{palette.secondary}] {v}")

    elif action == "calibrate":
        verifier = registry.get("calibrated-verifier")
        rng = np.random.RandomState(42)
        X = rng.randn(100, 4)
        y = (X[:, 0] * 1.5 + X[:, 1] * 0.8 + rng.randn(100) * 0.3 > 0.0).astype(int)

        verifier.fit_calibration(X, y)
        metrics = verifier.evaluate_calibration(X, y)

        if getattr(args, "json", False):
            print(json.dumps(metrics.__dict__, indent=2))
            return

        console.print(f"[{palette.success} bold]Calibrated Verifier Diagnostics[/{palette.success} bold]")
        console.print(f"  [{palette.secondary}]Expected Calibration Error (ECE):[/{palette.secondary}] {metrics.expected_calibration_error:.4f}")
        console.print(f"  [{palette.secondary}]Brier Score:[/{palette.secondary}] {metrics.brier_score:.4f}")
        console.print(f"  [{palette.secondary}]Abstention Rate:[/{palette.secondary}] {metrics.abstention_rate:.2%}")
        console.print(f"  [{palette.secondary}]Coverage Rate:[/{palette.secondary}] {metrics.coverage_rate:.2%}")
        console.print(f"  [{palette.secondary}]Total Evaluated Samples:[/{palette.secondary}] {metrics.num_samples}")
