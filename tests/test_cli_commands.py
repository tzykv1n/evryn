# pytest tests/test_cli_commands.py
# python -m pytest tests/test_cli_commands.py

import os
import subprocess
import sys


def test_cli_help():
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    py_bin = sys.executable
    out = subprocess.check_output([py_bin, "-m", "evryn.cli", "--help"], cwd=repo_dir).decode()
    assert "EVRYN : Unified Scientific Knowledge Discovery Platform" in out
    assert "doctor" in out
    assert "benchmark" in out
    assert "run" in out
    assert "flux" in out
    assert "graph" in out


def test_cli_doctor():
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    py_bin = sys.executable
    res = subprocess.run([py_bin, "-m", "evryn.cli", "doctor"], cwd=repo_dir, capture_output=True, text=True)
    assert res.returncode == 0
    assert "EVRYN System & Platform Diagnostics" in res.stdout
    assert "HEALTHY" in res.stdout


def test_cli_benchmark_dry_run():
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    py_bin = sys.executable
    res = subprocess.run([py_bin, "-m", "evryn.cli", "benchmark", "--dry-run"], cwd=repo_dir, capture_output=True, text=True)
    assert res.returncode == 0
    assert "EVRYN Benchmark Execution Plan (DRY RUN)" in res.stdout
    assert "Dry run complete" in res.stdout


def test_cli_run_dry_run():
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    py_bin = sys.executable
    res = subprocess.run([py_bin, "-m", "evryn.cli", "run", "--dry-run"], cwd=repo_dir, capture_output=True, text=True)
    assert res.returncode == 0
    assert "EVRYN Pipeline Execution Plan (DRY RUN)" in res.stdout
    assert "Dry run complete" in res.stdout


def test_installer_and_uninstaller_dry_run():
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    res_inst = subprocess.run(["./install.sh", "--dry-run"], cwd=repo_dir, capture_output=True, text=True)
    assert res_inst.returncode == 0
    assert "Inspection completed successfully" in res_inst.stdout

    res_uninst = subprocess.run(["./uninstall.sh", "--dry-run"], cwd=repo_dir, capture_output=True, text=True)
    assert res_uninst.returncode == 0
    assert "[DRY-RUN]" in res_uninst.stdout
