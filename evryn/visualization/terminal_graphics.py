# evryn view <image_path>
# evryn view <image_path> --ascii

import os
import sys
import shutil
import base64
import subprocess
from typing import Optional, Tuple
from PIL import Image


def detect_native_graphics_protocol() -> Optional[str]:
    term = os.environ.get("TERM", "").lower()
    term_prog = os.environ.get("TERM_PROGRAM", "")

    if "KITTY_WINDOW_ID" in os.environ or "kitty" in term:
        return "kitty"
    if term_prog in ("iTerm.app", "WezTerm"):
        return "iterm2"
    if "sixel" in term:
        return "sixel"
    return None


def render_native_protocol(image_path: str, protocol: str) -> Optional[str]:
    if not os.path.exists(image_path):
        return None

    try:
        with open(image_path, "rb") as f:
            raw_bytes = f.read()
        b64_data = base64.b64encode(raw_bytes).decode("ascii")

        if protocol == "kitty":
            chunks = [b64_data[i:i + 4096] for i in range(0, len(b64_data), 4096)]
            out = []
            for idx, chunk in enumerate(chunks):
                m = 0 if idx == len(chunks) - 1 else 1
                if idx == 0:
                    out.append(f"\033_Gf=100,a=T,m={m};{chunk}\033\\")
                else:
                    out.append(f"\033_Gm={m};{chunk}\033\\")
            return "".join(out) + "\n"

        elif protocol == "iterm2":
            size = len(raw_bytes)
            return f"\033]1337;File=inline=1;size={size}:{b64_data}\a\n"

        return None
    except Exception:
        return None


def find_available_viewer() -> Optional[str]:
    viewers = ["imv", "sxiv", "nsxiv", "feh", "xdg-open"]
    for v in viewers:
        if shutil.which(v):
            return v
    return None


def open_in_external_viewer(image_path: str) -> Tuple[bool, str]:
    if not os.path.exists(image_path):
        return False, "File does not exist"

    viewer = find_available_viewer()
    if viewer:
        v_path = shutil.which(viewer)
        try:
            subprocess.Popen(
                [v_path, image_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True, viewer
        except Exception:
            return False, ""
    return False, ""


def get_terminal_geometry(fallback_cols: int = 80, fallback_rows: int = 24) -> Tuple[int, int]:
    try:
        size = shutil.get_terminal_size(fallback=(fallback_cols, fallback_rows))
        return max(20, size.columns), max(8, size.lines)
    except Exception:
        return fallback_cols, fallback_rows


class TerminalGraphicsRenderer:

    def __init__(self, target_width: Optional[int] = None):
        self.explicit_width = target_width
        self.mode = self._detect_terminal_capability()

    def _detect_terminal_capability(self) -> str:
        term = os.environ.get("TERM", "").lower()
        colorterm = os.environ.get("COLORTERM", "").lower()

        if colorterm in ("truecolor", "24bit") or any(t in term for t in ("alacritty", "xterm", "tmux", "screen", "rxvt")):
            return "truecolor_blocks"
        return "unicode_blocks"

    def compute_render_dimensions(
        self,
        orig_w: int,
        orig_h: int,
        max_cols: Optional[int] = None,
        max_lines: Optional[int] = None,
        explicit_width: Optional[int] = None,
    ) -> Tuple[int, int, int]:
        term_cols, term_rows = get_terminal_geometry()
        aspect_ratio = float(orig_h) / float(max(1, orig_w))

        if explicit_width is not None or self.explicit_width is not None:
            w = int(explicit_width or self.explicit_width)
            w = max(10, min(w, term_cols))
            pixel_h = max(4, int(round(w * aspect_ratio)))
            if pixel_h % 2 != 0:
                pixel_h += 1
            char_lines = pixel_h // 2
            return w, pixel_h, char_lines

        avail_cols = max(16, term_cols - 4)
        if max_cols is not None:
            avail_cols = min(avail_cols, max_cols)
        else:
            if term_cols >= 120:
                avail_cols = min(avail_cols, 92)
            elif term_cols >= 90:
                avail_cols = min(avail_cols, 80)
            else:
                avail_cols = min(avail_cols, 72)

        avail_lines = max_lines if max_lines is not None else max(6, min(term_rows - 4, 22))

        target_w = avail_cols
        needed_lines = max(2, int(round(target_w * aspect_ratio / 2.0)))

        if needed_lines > avail_lines:
            target_w = max(12, int(round(avail_lines * 2.0 / aspect_ratio)))
            target_w = min(target_w, avail_cols)

        pixel_h = max(4, int(round(target_w * aspect_ratio)))
        if pixel_h % 2 != 0:
            pixel_h += 1
        char_lines = pixel_h // 2
        return target_w, pixel_h, char_lines

    def render_image(
        self,
        image_path: str,
        max_width: Optional[int] = None,
        max_lines: Optional[int] = None,
        center: bool = True,
    ) -> str:
        if not os.path.exists(image_path):
            return self.render_fallback_card(image_path, title="File Not Found", reason="Path does not exist on disk")

        try:
            with Image.open(image_path) as img:
                orig_w, orig_h = img.size
                cols, pixel_h, char_lines = self.compute_render_dimensions(
                    orig_w,
                    orig_h,
                    max_cols=max_width,
                    max_lines=max_lines,
                    explicit_width=max_width or self.explicit_width,
                )

            if self.mode in ("truecolor_blocks", "unicode_blocks"):
                return self._render_truecolor_blocks(image_path, cols, pixel_h, center=center)
            else:
                return self._render_ascii_fallback(image_path, cols, pixel_h, center=center)
        except Exception as e:
            return self.render_fallback_card(image_path, title="Rendering Error", reason=str(e))

    def _render_truecolor_blocks(
        self,
        image_path: str,
        width: int,
        pixel_h: int,
        center: bool = True,
    ) -> str:
        try:
            img = Image.open(image_path).convert("RGB")
            img_resized = img.resize((width, pixel_h), Image.Resampling.BILINEAR)
            pixels = img_resized.load()

            term_cols, _ = get_terminal_geometry()
            pad_len = max(0, (term_cols - width) // 2) if center else 2
            pad = " " * pad_len

            lines = []
            for y in range(0, pixel_h, 2):
                row_str = pad
                for x in range(width):
                    r_top, g_top, b_top = pixels[x, y]
                    if y + 1 < pixel_h:
                        r_bot, g_bot, b_bot = pixels[x, y + 1]
                    else:
                        r_bot, g_bot, b_bot = (0, 0, 0)
                    row_str += f"\033[38;2;{r_top};{g_top};{b_top}m\033[48;2;{r_bot};{g_bot};{b_bot}m▀\033[0m"
                lines.append(row_str)
            return "\n".join(lines)
        except Exception as e:
            return self.render_fallback_card(image_path, title="Decode Error", reason=str(e))

    def _render_ascii_fallback(
        self,
        image_path: str,
        width: int,
        pixel_h: int,
        center: bool = True,
    ) -> str:
        try:
            img = Image.open(image_path).convert("L")
            char_lines = max(2, pixel_h // 2)
            img_resized = img.resize((width, char_lines))

            term_cols, _ = get_terminal_geometry()
            pad_len = max(0, (term_cols - width) // 2) if center else 2
            pad = " " * pad_len

            chars = [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@"]
            lines = []
            for y in range(char_lines):
                row = pad
                for x in range(width):
                    val = img_resized.getpixel((x, y))
                    idx = int(val / 256.0 * len(chars))
                    row += chars[min(idx, len(chars) - 1)]
                lines.append(row)
            return "\n".join(lines)
        except Exception as e:
            return self.render_fallback_card(image_path, title="ASCII Fallback Error", reason=str(e))

    @staticmethod
    def render_fallback_card(image_path: str, title: str = "Graphic Artifact", reason: str = "") -> str:
        basename = os.path.basename(image_path)
        term_cols, _ = get_terminal_geometry()
        box_w = max(44, min(term_cols - 4, 76))
        inner_w = box_w - 4

        line_top = "╭" + "─" * (box_w - 2) + "╮"
        line_bot = "╰" + "─" * (box_w - 2) + "╯"

        lines = [line_top]
        if title and title != "Graphic Artifact":
            t_str = f"  TITLE  : {title}"[:inner_w]
            lines.append(f"│ {t_str:<{inner_w}} │")
        title_str = f"  FIGURE : {basename}"[:inner_w]
        lines.append(f"│ {title_str:<{inner_w}} │")

        view_cmd = f"  OPEN   : evryn view {image_path}"[:inner_w]
        lines.append(f"│ {view_cmd:<{inner_w}} │")

        if reason:
            r_str = f"  STATUS : {reason}"[:inner_w]
            lines.append(f"│ {r_str:<{inner_w}} │")

        lines.append(line_bot)
        return "\n".join(lines)
