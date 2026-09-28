# pytest tests/test_terminal_graphics.py

import os
import tempfile
import pytest
import numpy as np
from PIL import Image

from evryn.visualization.terminal_graphics import (
    TerminalGraphicsRenderer,
    get_terminal_geometry,
)
from evryn.visualization.presenter import VisualArtifact, present_artifacts


def _create_dummy_image(path: str, width: int = 400, height: int = 200, color=(100, 150, 200)):
    img = Image.new("RGB", (width, height), color=color)
    img.save(path)
    return path


def test_terminal_geometry_detection():
    cols, rows = get_terminal_geometry()
    assert isinstance(cols, int)
    assert isinstance(rows, int)
    assert cols >= 20
    assert rows >= 8


def test_aspect_ratio_preservation_widescreen():
    renderer = TerminalGraphicsRenderer()
    orig_w, orig_h = 3000, 1500
    true_aspect = orig_h / orig_w

    cols, pixel_h, char_lines = renderer.compute_render_dimensions(
        orig_w=orig_w,
        orig_h=orig_h,
        max_cols=60,
    )
    visual_aspect = (char_lines * 2.0) / float(cols)
    assert abs(visual_aspect - true_aspect) <= 0.08
    assert cols <= 60


def test_aspect_ratio_preservation_square():
    renderer = TerminalGraphicsRenderer()
    orig_w, orig_h = 800, 800
    true_aspect = 1.0

    cols, pixel_h, char_lines = renderer.compute_render_dimensions(
        orig_w=orig_w,
        orig_h=orig_h,
        max_cols=50,
        max_lines=20,
    )
    visual_aspect = (char_lines * 2.0) / float(cols)
    assert abs(visual_aspect - true_aspect) <= 0.08
    assert char_lines <= 20


def test_aspect_ratio_preservation_portrait():
    renderer = TerminalGraphicsRenderer()
    orig_w, orig_h = 400, 800
    true_aspect = 2.0

    cols, pixel_h, char_lines = renderer.compute_render_dimensions(
        orig_w=orig_w,
        orig_h=orig_h,
        max_cols=60,
        max_lines=15,
    )
    visual_aspect = (char_lines * 2.0) / float(cols)
    assert abs(visual_aspect - true_aspect) <= 0.15
    assert char_lines <= 15


def test_explicit_width_override():
    renderer = TerminalGraphicsRenderer(target_width=52)
    cols, pixel_h, char_lines = renderer.compute_render_dimensions(
        orig_w=1000,
        orig_h=500,
    )
    assert cols == 52
    assert char_lines == int(round(52 * 0.5 / 2.0))


def test_render_image_truecolor(tmp_path):
    renderer = TerminalGraphicsRenderer()
    img_path = str(tmp_path / "test_fig.png")
    _create_dummy_image(img_path, width=200, height=100)

    rendered = renderer.render_image(img_path, max_width=40)
    assert "▀" in rendered
    assert "\033[" in rendered
    lines = rendered.split("\n")
    assert len(lines) >= 4


def test_render_missing_image_graceful():
    renderer = TerminalGraphicsRenderer()
    result = renderer.render_image("/nonexistent/path/to/missing_image.png")
    assert "FIGURE" in result or "missing_image.png" in result
    assert "VIEW" in result


def test_fallback_card():
    card = TerminalGraphicsRenderer.render_fallback_card(
        "outputs/confusion_matrix.png",
        title="Test Confusion Matrix",
        reason="Test diagnostic message",
    )
    assert "confusion_matrix.png" in card
    assert "evryn view outputs/confusion_matrix.png" in card
    assert "Test diagnostic message" in card


def test_present_artifacts_filtering(tmp_path, capsys):
    img_path = str(tmp_path / "art.png")
    _create_dummy_image(img_path, width=100, height=50)

    art_pri = VisualArtifact(path=img_path, title="Primary Art", role="primary")
    art_sec = VisualArtifact(path=img_path, title="Secondary Art", role="secondary")

    present_artifacts([art_pri, art_sec], verbose=False)
    captured = capsys.readouterr()
    assert "Primary Art" in captured.out
    assert "Secondary Art" not in captured.out

    present_artifacts([art_pri, art_sec], verbose=True)
    captured_verbose = capsys.readouterr()
    assert "Primary Art" in captured_verbose.out
    assert "Secondary Art" in captured_verbose.out
