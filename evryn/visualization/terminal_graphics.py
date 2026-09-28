# evryn view <image_path>

import os
import sys
from typing import Optional, Tuple
from PIL import Image


class TerminalGraphicsRenderer:

    def __init__(self, target_width: int = 76):
        self.target_width = target_width
        self.mode = self._detect_terminal_capability()

    def _detect_terminal_capability(self) -> str:
        term = os.environ.get("TERM", "").lower()
        colorterm = os.environ.get("COLORTERM", "").lower()

        if "KITTY_WINDOW_ID" in os.environ or "kitty" in term:
            return "kitty"
        if "sixel" in term:
            return "sixel"
        if colorterm in ("truecolor", "24bit") or "alacritty" in term or "xterm" in term:
            return "truecolor_blocks"
        return "unicode_blocks"

    def render_image(self, image_path: str, max_width: Optional[int] = None) -> str:
        if not os.path.exists(image_path):
            return f"[Error: Image file not found at '{image_path}']"

        width = max_width or self.target_width

        if self.mode == "kitty":
            return self._render_truecolor_blocks(image_path, width)
        elif self.mode == "sixel":
            return self._render_truecolor_blocks(image_path, width)
        elif self.mode in ("truecolor_blocks", "unicode_blocks"):
            return self._render_truecolor_blocks(image_path, width)
        else:
            return self._render_ascii_fallback(image_path, width)

    def _render_truecolor_blocks(self, image_path: str, width: int) -> str:
        try:
            img = Image.open(image_path).convert("RGB")
            orig_w, orig_h = img.size
            aspect_ratio = orig_h / orig_w
            target_h = int(width * aspect_ratio * 0.5)
            target_h = max(4, target_h if target_h % 2 == 0 else target_h + 1)

            img_resized = img.resize((width, target_h), Image.Resampling.BILINEAR)
            pixels = img_resized.load()

            lines = []
            for y in range(0, target_h, 2):
                row_str = ""
                for x in range(width):
                    r_top, g_top, b_top = pixels[x, y]
                    if y + 1 < target_h:
                        r_bot, g_bot, b_bot = pixels[x, y + 1]
                    else:
                        r_bot, g_bot, b_bot = (0, 0, 0)
                    row_str += f"\033[38;2;{r_top};{g_top};{b_top}m\033[48;2;{r_bot};{g_bot};{b_bot}m▀\033[0m"
                lines.append(row_str)
            return "\n".join(lines)
        except Exception as e:
            return f"[Render fallback: {e}]"

    def _render_ascii_fallback(self, image_path: str, width: int) -> str:
        try:
            img = Image.open(image_path).convert("L")
            orig_w, orig_h = img.size
            aspect_ratio = orig_h / orig_w
            target_h = int(width * aspect_ratio * 0.45)
            img_resized = img.resize((width, target_h))

            chars = [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@"]
            lines = []
            for y in range(target_h):
                row = ""
                for x in range(width):
                    val = img_resized.getpixel((x, y))
                    idx = int(val / 256.0 * len(chars))
                    row += chars[min(idx, len(chars) - 1)]
                lines.append(row)
            return "\n".join(lines)
        except Exception as e:
            return f"[ASCII fallback error: {e}]"
