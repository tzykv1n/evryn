# evryn view <image_path>

import os
import sys
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from rich.text import Text
from rich.panel import Panel
from rich.align import Align

from .terminal_graphics import TerminalGraphicsRenderer, get_terminal_geometry
from ..ui.console import console


@dataclass
class VisualArtifact:
    path: str
    title: str
    role: str = "primary"
    artifact_type: str = "image"
    description: Optional[str] = None


def present_artifacts(
    artifacts: List[VisualArtifact],
    verbose: bool = False,
    max_width: Optional[int] = None,
) -> None:
    if not artifacts:
        return

    renderer = TerminalGraphicsRenderer(target_width=max_width)
    term_cols, _ = get_terminal_geometry()

    for art in artifacts:
        if not verbose and art.role not in ("primary", "diagnostic"):
            continue

        rel_path = os.path.relpath(art.path) if os.path.isabs(art.path) else art.path
        if not os.path.exists(art.path):
            fallback_box = renderer.render_fallback_card(
                art.path,
                title=art.title,
                reason="Artifact not yet generated on disk",
            )
            console.print(fallback_box)
            continue

        size_kb = os.path.getsize(art.path) / 1024.0

        title_text = Text()
        title_text.append("  ◆ ", style="bold magenta")
        title_text.append(f"{art.title} ", style="bold cyan")
        title_text.append(f"[{art.role.upper()}]", style="dim magenta")
        console.print(title_text)

        if art.artifact_type == "image":
            rendered = renderer.render_image(art.path, max_width=max_width, center=True)
            sys.stdout.write(rendered + "\n")
            sys.stdout.flush()

        footer_text = Text()
        footer_text.append("    Source: ", style="dim white")
        footer_text.append(rel_path, style="underline cyan")
        footer_text.append(f" ({size_kb:.1f} KB)", style="dim white")
        if art.description:
            footer_text.append(f" • {art.description}", style="dim magenta")
        console.print(footer_text)
        console.print()
