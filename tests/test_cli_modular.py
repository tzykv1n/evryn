# pytest tests/test_cli_modular.py
# evryn cli_modules

import argparse
import pytest
from evryn.cli import build_parser
from evryn.cli_modules.themes import get_theme, ThemeManager
from evryn.cli_modules.commands_models import handle_models_command
from evryn.cli_modules.commands_config import handle_config_command, load_config, save_config


def test_cli_parser_modular_subcommands():
    parser = build_parser()
    args = parser.parse_args(["models", "list", "--json"])
    assert args.command == "models"
    assert args.models_action == "list"
    assert args.json is True

    args_cfg = parser.parse_args(["config", "get", "theme"])
    assert args_cfg.command == "config"
    assert args_cfg.config_action == "get"
    assert args_cfg.config_key == "theme"

    args_ui = parser.parse_args(["ui", "--theme", "midnight"])
    assert args_ui.command == "ui"
    assert args_ui.theme == "midnight"


def test_theme_manager_and_palettes():
    mgr = ThemeManager("midnight")
    assert mgr.theme_name == "midnight"
    assert mgr.palette.primary == "magenta"

    mgr.set_theme("high-contrast")
    assert mgr.palette.primary == "bright_yellow"

    def_theme = get_theme("nonexistent")
    assert def_theme.name == "default"


def test_config_lifecycle():
    cfg = load_config()
    orig_threshold = cfg.get("abstention_threshold", 0.45)
    cfg["abstention_threshold"] = 0.50
    save_config(cfg)

    reloaded = load_config()
    assert reloaded["abstention_threshold"] == 0.50

    cfg["abstention_threshold"] = orig_threshold
    save_config(cfg)
