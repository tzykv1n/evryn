# evryn doctor
# evryn doctor --json

import os
import sys
import platform
import subprocess
import json
from typing import Dict, Any, List

from evryn.ui.console import console, print_box, print_table
from evryn.visualization.terminal_graphics import detect_native_graphics_protocol


def run_doctor_checks() -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []

    py_ver = platform.python_version()
    py_ok = sys.version_info >= (3, 10)
    checks.append({
        "name": "Python Version",
        "category": "runtime",
        "passed": py_ok,
        "details": f"Python {py_ver}",
        "remediation": "EVRYN requires Python 3.10+ (tested on Python 3.10-3.14)" if not py_ok else "",
    })

    os_name = platform.system()
    os_ok = os_name == "Linux"
    checks.append({
        "name": "Operating System",
        "category": "runtime",
        "passed": os_ok,
        "details": f"{os_name} {platform.release()} ({platform.machine()})",
        "remediation": "EVRYN is primarily validated for Linux systems" if not os_ok else "",
    })

    mem_gb = 0.0
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_kb = float(line.split()[1])
                    mem_gb = mem_kb / (1024.0 * 1024.0)
                    break
    except Exception:
        pass
    mem_ok = mem_gb >= 3.5 or mem_gb == 0.0
    checks.append({
        "name": "Host Memory",
        "category": "hardware",
        "passed": mem_ok,
        "details": f"{mem_gb:.1f} GB RAM available" if mem_gb > 0 else "RAM measurement unreadable",
        "remediation": "At least 4 GB RAM recommended for full dataset benchmarks" if not mem_ok else "",
    })

    required_pkgs = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("pandas", "pandas"),
        ("scikit-learn", "sklearn"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
        ("networkx", "networkx"),
        ("rich", "rich"),
        ("pillow", "PIL"),
        ("torch", "torch"),
        ("transformers", "transformers"),
    ]

    for pkg_name, import_name in required_pkgs:
        try:
            mod = __import__(import_name)
            v = getattr(mod, "__version__", "available")
            checks.append({
                "name": f"Dependency: {pkg_name}",
                "category": "dependencies",
                "passed": True,
                "details": f"v{v}",
                "remediation": "",
            })
        except ImportError:
            checks.append({
                "name": f"Dependency: {pkg_name}",
                "category": "dependencies",
                "passed": False,
                "details": "Not installed",
                "remediation": f"Install via pip install {pkg_name}",
            })

    for d in ["outputs", "cache", "data"]:
        exists = os.path.isdir(d)
        writable = os.access(d, os.W_OK) if exists else os.access(".", os.W_OK)
        checks.append({
            "name": f"Directory: {d}/",
            "category": "storage",
            "passed": writable,
            "details": f"Exists ({'writable' if writable else 'read-only'})" if exists else "Will be created automatically",
            "remediation": f"Ensure write permissions to ./{d}" if not writable else "",
        })

    proto = detect_native_graphics_protocol()
    checks.append({
        "name": "Terminal Graphics Protocol",
        "category": "display",
        "passed": True,
        "details": f"Detected: {proto.upper()}" if proto else "ANSI half-block ASCII fallback",
        "remediation": "Install foot or kitty for high-resolution inline terminal rendering",
    })

    repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    git_passed = False
    git_details = "Not a git repository"
    try:
        branch = subprocess.check_output(["git", "-C", repo_dir, "branch", "--show-current"], stderr=subprocess.DEVNULL).decode().strip()
        rev = subprocess.check_output(["git", "-C", repo_dir, "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        git_passed = True
        git_details = f"Branch '{branch}' @ {rev}"
    except Exception:
        pass
    checks.append({
        "name": "Git Repository Tracking",
        "category": "vcs",
        "passed": git_passed,
        "details": git_details,
        "remediation": "Run git init or clone from canonical source" if not git_passed else "",
    })

    has_failures = any(not c["passed"] for c in checks if c["category"] in ("runtime", "dependencies"))
    status = "DEGRADED" if has_failures else "HEALTHY"

    return {
        "status": status,
        "passed_count": sum(1 for c in checks if c["passed"]),
        "total_count": len(checks),
        "checks": checks,
    }


def print_doctor_report(rep: Dict[str, Any], as_json: bool = False) -> int:
    if as_json:
        print(json.dumps(rep, indent=2))
        return 0 if rep["status"] == "HEALTHY" else 1

    status_color = "bold green" if rep["status"] == "HEALTHY" else "bold red"
    print_box(
        "EVRYN System & Platform Diagnostics (Doctor)",
        f"Platform Health: [{status_color}]{rep['status']}[/{status_color}] | Verified: {rep['passed_count']}/{rep['total_count']} checks passed",
    )

    headers = ["Category", "Check Component", "Status", "Details / Diagnostics"]
    rows = []
    for c in rep["checks"]:
        st = "[bold green]PASS[/bold green]" if c["passed"] else "[bold red]FAIL[/bold red]"
        details = c["details"]
        if not c["passed"] and c["remediation"]:
            details += f" ([dim yellow]{c['remediation']}[/dim yellow])"
        rows.append([c["category"].upper(), c["name"], st, details])

    print_table(headers, rows, title="Environment Verification Registry")

    if rep["status"] == "HEALTHY":
        console.print("[bold green][✓] All core requirements satisfied. Platform ready for execution.[/bold green]\n")
        return 0
    else:
        console.print("[bold red][✗] Critical requirements missing. Remediate flagged items before execution.[/bold red]\n")
        return 1
