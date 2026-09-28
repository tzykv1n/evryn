# evryn --help

import sys
import shutil
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.text import Text
from rich.align import Align

console = Console()

EVRYN_ASCII_LOGO = """\033[38;2;0;240;255m  ███████╗██╗   ██╗██████╗ ██╗   ██╗███╗   ██╗
\033[38;2;45;212;255m  ██╔════╝██║   ██║██╔══██╗╚██╗ ██╔╝████╗  ██║
\033[38;2;129;140;248m  █████╗  ██║   ██║██████╔╝ ╚████╔╝ ██╔██╗ ██║
\033[38;2;168;85;247m  ██╔══╝  ╚██╗ ██╔╝██╔══██╗  ╚██╔╝  ██║╚██╗██║
\033[38;2;217;70;239m  ███████╗ ╚████╔╝ ██║  ██║   ██║   ██║ ╚████║
\033[38;2;236;72;153m  ╚══════╝  ╚═══╝  ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═══╝\033[0m"""


def print_evryn_banner(
    subtitle: str = "Unified Scientific Knowledge Discovery Platform",
    is_scratch: bool = False,
    seed: int = 42,
):
    print(EVRYN_ASCII_LOGO)
    mode_text = "[bold magenta]from-scratch[/bold magenta]" if is_scratch else "[bold cyan]cached[/bold cyan]"

    content = Text()
    content.append("EVRYN ", style="bold cyan")
    content.append("• ", style="dim white")
    content.append(subtitle, style="bold white")
    content.append("\n")
    content.append("MODE  ", style="bold white")
    content.append("from-scratch" if is_scratch else "cached", style="bold magenta" if is_scratch else "bold cyan")
    content.append("   │   SEED  ", style="dim white")
    content.append(str(seed), style="bold white")
    content.append("   │   OUTPUT  ", style="dim white")
    content.append("outputs/", style="cyan")

    p = Panel(
        Align.center(content),
        border_style="magenta",
        padding=(0, 2),
    )
    console.print(p)


def print_box(title: str, subtitle: Optional[str] = None, is_scratch: Optional[bool] = None):
    t = Text()
    t.append(title, style="bold cyan")
    if subtitle:
        t.append(f"\n{subtitle}", style="dim magenta")
    if is_scratch is not None:
        t.append("\nMODE  ", style="bold white")
        t.append("from-scratch" if is_scratch else "cached", style="bold magenta" if is_scratch else "bold cyan")

    p = Panel(
        t,
        border_style="cyan",
        padding=(0, 2),
    )
    console.print(p)


def print_table(headers: List[str], rows: List[List[str]], title: Optional[str] = None):
    tbl = Table(
        title=title,
        border_style="magenta",
        header_style="bold cyan",
        title_style="bold white",
        show_lines=True,
    )
    for h in headers:
        tbl.add_column(h, justify="left")
    for r in rows:
        tbl.add_row(*r)
    console.print(tbl)


def get_progress_bar(description: str = "Processing") -> Progress:
    return Progress(
        SpinnerColumn(spinner_name="dots", style="bold magenta"),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        BarColumn(complete_style="magenta", finished_style="bold cyan"),
        TextColumn("[bold white]{task.percentage:>3.0f}%[/bold white]"),
        TimeElapsedColumn(),
        console=console,
    )
