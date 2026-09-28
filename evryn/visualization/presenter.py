# evryn view <image_path>
# evryn view <image_path> --ascii

import os
import sys
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from rich.text import Text
from rich.panel import Panel
from rich.align import Align

from .terminal_graphics import (
    TerminalGraphicsRenderer,
    get_terminal_geometry,
    detect_native_graphics_protocol,
    render_native_protocol,
)
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

    protocol = detect_native_graphics_protocol()
    renderer = TerminalGraphicsRenderer(target_width=max_width)

    for art in artifacts:
        if not verbose and art.role not in ("primary", "diagnostic"):
            continue

        rel_path = os.path.relpath(art.path) if os.path.isabs(art.path) else art.path

        if protocol:
            native_str = render_native_protocol(art.path, protocol)
            if native_str:
                title_text = Text()
                title_text.append("  ◆ ", style="bold magenta")
                title_text.append(f"{art.title} ", style="bold cyan")
                title_text.append(f"[{art.role.upper()}]", style="dim magenta")
                console.print(title_text)
                sys.stdout.write(native_str)
                sys.stdout.flush()
                continue

        card = renderer.render_fallback_card(
            rel_path,
            title=art.title,
            reason=art.description or "",
        )
        console.print(card)
