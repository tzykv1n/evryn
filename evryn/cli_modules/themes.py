# evryn cli_modules themes
# pytest tests/test_cli_commands.py

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ThemePalette:
    name: str
    primary: str
    secondary: str
    accent: str
    success: str
    warning: str
    danger: str
    text: str
    muted: str
    background: str


THEMES: Dict[str, ThemePalette] = {
    "default": ThemePalette(
        name="default",
        primary="cyan",
        secondary="blue",
        accent="bright_magenta",
        success="green",
        warning="yellow",
        danger="red",
        text="white",
        muted="bright_black",
        background="#0f172a",
    ),
    "midnight": ThemePalette(
        name="midnight",
        primary="magenta",
        secondary="blue",
        accent="bright_cyan",
        success="bright_green",
        warning="yellow",
        danger="bright_red",
        text="white",
        muted="dim white",
        background="#090d16",
    ),
    "monochrome": ThemePalette(
        name="monochrome",
        primary="white",
        secondary="dim white",
        accent="bold white",
        success="white",
        warning="dim white",
        danger="bold white",
        text="white",
        muted="dim white",
        background="#000000",
    ),
    "high-contrast": ThemePalette(
        name="high-contrast",
        primary="bright_yellow",
        secondary="bright_cyan",
        accent="bright_white",
        success="bright_green",
        warning="bright_yellow",
        danger="bright_red",
        text="bright_white",
        muted="white",
        background="#000000",
    ),
}


class ThemeManager:
    def __init__(self, theme_name: str = "default"):
        self.theme_name = theme_name if theme_name in THEMES else "default"
        self.palette = THEMES[self.theme_name]

    def set_theme(self, theme_name: str):
        if theme_name in THEMES:
            self.theme_name = theme_name
            self.palette = THEMES[theme_name]

    def format_title(self, text: str) -> str:
        return f"[{self.palette.primary} bold]{text}[/{self.palette.primary} bold]"

    def format_success(self, text: str) -> str:
        return f"[{self.palette.success}]{text}[/{self.palette.success}]"

    def format_warning(self, text: str) -> str:
        return f"[{self.palette.warning}]{text}[/{self.palette.warning}]"

    def format_danger(self, text: str) -> str:
        return f"[{self.palette.danger} bold]{text}[/{self.palette.danger} bold]"

    def format_muted(self, text: str) -> str:
        return f"[{self.palette.muted}]{text}[/{self.palette.muted}]"


def get_theme(theme_name: Optional[str] = None) -> ThemePalette:
    name = (theme_name or "default").lower()
    return THEMES.get(name, THEMES["default"])
