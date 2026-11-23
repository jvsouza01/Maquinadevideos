from __future__ import annotations

from pathlib import Path
from PIL import ImageFont

SCRIPTS_DIR = Path(__file__).resolve().parent
RELAMPEJA_DIR = SCRIPTS_DIR.parent
WORKSPACE_ROOT = RELAMPEJA_DIR.parent.parent
ASSETS_DIR = RELAMPEJA_DIR / "assets"
CARDS_DIR = ASSETS_DIR / "cards"
PANELS_DIR = ASSETS_DIR / "panels"
SCRATCH_DIR = WORKSPACE_ROOT / "scratch"

PALETTE = {
    "navy": (11, 25, 44, 255),
    "navy_panel": (11, 25, 44, 245),
    "navy_badge_bg": (11, 25, 44, 230),
    "gold": (255, 204, 0, 255),
    "white": (255, 255, 255, 255),
    "shadow": (0, 0, 0, 160),
    "panel_shadow": (5, 10, 20, 170),
}

CANVAS_SIZE = (1080, 1920)


def get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for font_path in candidates:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()


def resolve_asset(relative_or_name: str, fallback_to_scratch: bool = True) -> Path:
    """Resolve an asset inside relampeja-edit/assets first, falling back to workspace/scratch."""
    direct = Path(relative_or_name)
    if direct.is_absolute() and direct.exists():
        return direct

    candidates = [
        ASSETS_DIR / relative_or_name,
        RELAMPEJA_DIR / relative_or_name,
        WORKSPACE_ROOT / relative_or_name,
    ]
    if fallback_to_scratch:
        candidates.append(SCRATCH_DIR / Path(relative_or_name).name)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]
