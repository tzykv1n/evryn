# evryn --help

import sys
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.text import Text
from rich.align import Align

console = Console()

EVRYN_ASCII_LOGO = """\033[1;36m  ╔═╗╦  ╦╦═╗╦ ╦╔╗╔\033[0m
\033[1;37m  ║╣ ╚╗╔╝╠╦╝╚╦╝║║║\033[0m
\033[1;35m  ╚═╝ ╚╝ ╩╚═ ╩ ╝╚╝\033[0m"""


def print_evryn_banner(subtitle: str = "Unified Scientific Knowledge Discovery Platform"):
    print(EVRYN_ASCII_LOGO)
    sub_text = Text(subtitle, style="bold cyan")
    p = Panel(
        Align.center(sub_text),
        border_style="magenta",
        padding=(0, 2),
    )
    console.print(p)


def print_box(title: str, subtitle: Optional[str] = None):
    t = Text(title, style="bold cyan")
    if subtitle:
        t.append(f"\n{subtitle}", style="dim magenta")
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
