"""Exporta poses SVG estaticas de referencia em assets/mascot/ a partir de mascot_rig.py."""
from pathlib import Path
import re

from mascot_rig import POSES, render_inline_mascot_rig

ASSETS_MASCOT_DIR = Path(__file__).resolve().parent.parent / "assets" / "mascot"


def main() -> None:
    ASSETS_MASCOT_DIR.mkdir(parents=True, exist_ok=True)
    for pose in POSES:
        block = render_inline_mascot_rig(pose, uid=pose)
        m = re.search(r"<svg[\s\S]*</svg>", block)
        if not m:
            continue
        svg_text = m.group(0).replace('<svg class="mascot-svg"', '<svg xmlns="http://www.w3.org/2000/svg"')
        out = ASSETS_MASCOT_DIR / f"{pose}.svg"
        out.write_text(svg_text, encoding="utf-8")
        print(f"Generated {out}")


if __name__ == "__main__":
    main()
