# evryn cli_modules commands_config
# pytest tests/test_cli_commands.py

import os
import json
import sys
from typing import Any, Dict
from rich.console import Console
from rich.table import Table

from evryn.cli_modules.themes import get_theme


CONFIG_DIR = os.path.expanduser("~/.evryn")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "theme": "default",
    "default_corpus": "real_papers",
    "device": "cpu",
    "max_transitive_hops": 4,
    "abstention_threshold": 0.45,
    "output_dir": "outputs",
}


def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = dict(DEFAULT_CONFIG)
            merged.update(data)
            return merged
    except Exception:
        return dict(DEFAULT_CONFIG)


def save_config(cfg: Dict[str, Any]):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def handle_config_command(args: Any):
    console = Console()
    palette = get_theme(getattr(args, "theme", "default"))
    cfg = load_config()

    action = getattr(args, "config_action", "list") or "list"

    if action == "list":
        if getattr(args, "json", False):
            print(json.dumps(cfg, indent=2))
            return

        table = Table(title="EVRYN Configuration", border_style=palette.primary)
        table.add_column("Parameter Key", style=palette.primary, no_wrap=True)
        table.add_column("Current Value", style=palette.secondary)
        table.add_column("Default Value", style=palette.muted)

        for k, v in sorted(cfg.items()):
            def_v = DEFAULT_CONFIG.get(k, "")
            table.add_row(k, str(v), str(def_v))

        console.print(table)

    elif action == "get":
        key = getattr(args, "config_key", None)
        if not key:
            console.print(f"[{palette.danger}]Error: config key required.[/{palette.danger}]")
            sys.exit(1)
        if key not in cfg:
            console.print(f"[{palette.danger}]Key '{key}' not found in configuration.[/{palette.danger}]")
            sys.exit(1)

        val = cfg[key]
        if getattr(args, "json", False):
            print(json.dumps({key: val}, indent=2))
            return
        console.print(f"[{palette.primary}]{key}:[/{palette.primary}] {val}")

    elif action == "set":
        key = getattr(args, "config_key", None)
        val = getattr(args, "config_value", None)
        if not key or val is None:
            console.print(f"[{palette.danger}]Error: key and value required for set.[/{palette.danger}]")
            sys.exit(1)

        if val.lower() in ("true", "yes"):
            typed_val = True
        elif val.lower() in ("false", "no"):
            typed_val = False
        else:
            try:
                typed_val = int(val)
            except ValueError:
                try:
                    typed_val = float(val)
                except ValueError:
                    typed_val = val

        cfg[key] = typed_val
        save_config(cfg)

        if getattr(args, "json", False):
            print(json.dumps({"status": "success", "updated": {key: typed_val}}, indent=2))
            return
        console.print(f"[{palette.success}]Configuration updated:[/{palette.success}] {key} = {typed_val}")
