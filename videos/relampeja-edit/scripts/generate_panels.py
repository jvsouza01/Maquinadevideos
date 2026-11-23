from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw

from common import CANVAS_SIZE, PALETTE, PANELS_DIR, get_font

PANEL_SPECS = [
    ("PROF. ANDERSON CLAYTON", "⚡ RELAMPEJA • MENTORIA & CONCURSOS", "⚡ MENTORIA", "panel_1.png"),
    ("O SEGREDO DA APROVAÇÃO", "MÉTODO DIRECIONADO PARA SUA VAGA", "🎯 ESTRATÉGIA", "panel_2.png"),
    ("INÍCIO: 10/11 ÀS 19H", "AULA INAUGURAL AO VIVO", "📅 DATA & HORA", "panel_3.png"),
    ("AULAS HÍBRIDAS", "PRESENCIAL + TRANSMISSÃO ONLINE", "🌐 FORMATO", "panel_4.png"),
    ("CONCURSOS ABERTOS & PREVISTOS", "GMS • CATU • LAURO DE FREITAS • PRF", "📋 EDITAIS", "panel_5.png"),
    ("O SEGREDO DA APROVAÇÃO", "⚡ RELAMPEJA! A SUA VEZ CHEGOU", "⚡ VEM COMIGO", "panel_6.png"),
]


def create_top_panel(title: str, subtitle: str, badge_text: str, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pw, ph = 880, 140
    px = (CANVAS_SIZE[0] - pw) // 2
    py = 100
    r = 26

    draw.rounded_rectangle([px, py + 8, px + pw, py + ph + 8], radius=r, fill=PALETTE["panel_shadow"])
    draw.rounded_rectangle(
        [px, py, px + pw, py + ph],
        radius=r,
        fill=PALETTE["navy_panel"],
        outline=PALETTE["gold"],
        width=3,
    )

    font_badge = get_font(18, bold=True)
    bw, bh = 170, 32
    bx, by = px + 40, py - 16
    draw.rounded_rectangle(
        [bx, by, bx + bw, by + bh],
        radius=10,
        fill=PALETTE["gold"],
        outline=PALETTE["navy"],
        width=2,
    )
    draw.text((bx + bw // 2, by + bh // 2), badge_text, fill=PALETTE["navy"], font=font_badge, anchor="mm")

    font_title = get_font(34, bold=True)
    font_sub = get_font(21, bold=True)
    tx = px + pw // 2
    draw.text((tx, py + 52), title, fill=PALETTE["white"], font=font_title, anchor="mm")
    draw.text((tx, py + 98), subtitle, fill=PALETTE["gold"], font=font_sub, anchor="mm")

    img.save(out_path, "PNG")
    return out_path


def main() -> None:
    for title, subtitle, badge_text, filename in PANEL_SPECS:
        out = create_top_panel(title, subtitle, badge_text, PANELS_DIR / filename)
        print(f"Saved panel: {out}")


if __name__ == "__main__":
    main()
