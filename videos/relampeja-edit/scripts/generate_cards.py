from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

from common import ASSETS_DIR, CANVAS_SIZE, CARDS_DIR, PALETTE, get_font, resolve_asset

CARD_SPECS = [
    {
        "img": "estudos.jpg",
        "title": "AULAS HÍBRIDAS & ESTUDOS",
        "tag": "ONLINE + PRESENCIAL",
        "badge": None,
        "out": "card_1_estudos.png",
    },
    {
        "img": "gcm_salvador.jpg",
        "title": "GUARDA MUNICIPAL DE SALVADOR",
        "tag": "GMS • SALVADOR / BA",
        "badge": None,
        "out": "card_2_salvador.png",
    },
    {
        "img": "catu_1.jpg",
        "title": "AGENTE DE TRÂNSITO • CATU",
        "tag": "CMTT • CATU / BA",
        "badge": None,
        "out": "card_3_catu.png",
    },
    {
        "img": "lauro_1.jpg",
        "title": "AGENTE DE TRÂNSITO • LAURO DE FREITAS",
        "tag": "SEMOB • LAURO DE FREITAS",
        "badge": None,
        "out": "card_4_lauro.png",
    },
    {
        "img": "prf_2.jpg",
        "title": "POLÍCIA RODOVIÁRIA FEDERAL",
        "tag": "PRF • CARREIRA POLICIAL",
        "badge": "prf_badge.png",
        "out": "card_5_prf.png",
    },
    {
        "img": "aprovacao.jpg",
        "title": "O SEGREDO DA APROVAÇÃO",
        "tag": "SUA VAGA EM 2026",
        "badge": None,
        "out": "card_6_aprovacao.png",
    },
]


def create_card(
    img_src: Path,
    title: str,
    tag: str,
    badge_img_src: Path | None = None,
    out_path: Path = CARDS_DIR / "card.png",
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    card_w, card_h = 760, 500
    cx = (CANVAS_SIZE[0] - card_w) // 2
    cy = 660
    r = 24

    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(canvas)
    shadow_draw.rounded_rectangle(
        [cx, cy + 10, cx + card_w, cy + card_h + 10],
        radius=r,
        fill=PALETTE["shadow"],
    )

    card = Image.new("RGBA", (card_w, card_h), PALETTE["navy"])
    photo_h = 390
    photo = Image.open(img_src).convert("RGB")
    photo_fitted = ImageOps.fit(photo, (card_w, photo_h), method=Image.Resampling.LANCZOS)
    card.paste(photo_fitted, (0, 0))

    if badge_img_src and badge_img_src.exists():
        b_img = Image.open(badge_img_src).convert("RGBA")
        b_img.thumbnail((120, 120), Image.Resampling.LANCZOS)
        bx, by = card_w - b_img.width - 20, 20
        b_draw = ImageDraw.Draw(card)
        b_draw.ellipse(
            [bx - 6, by - 6, bx + b_img.width + 6, by + b_img.height + 6],
            fill=PALETTE["navy_badge_bg"],
            outline=PALETTE["gold"],
            width=2,
        )
        card.alpha_composite(b_img, (bx, by))

    banner_draw = ImageDraw.Draw(card)
    banner_draw.rectangle([0, photo_h, card_w, card_h], fill=PALETTE["navy"])
    banner_draw.line([(0, photo_h), (card_w, photo_h)], fill=PALETTE["gold"], width=3)

    font_tag = get_font(16, bold=True)
    tag_bbox = font_tag.getbbox(tag)
    tw = max(180, (tag_bbox[2] - tag_bbox[0]) + 32)
    th = 28
    tx, ty = 30, photo_h + 16
    banner_draw.rounded_rectangle([tx, ty, tx + tw, ty + th], radius=8, fill=PALETTE["gold"])
    banner_draw.text((tx + tw // 2, ty + th // 2), tag, fill=PALETTE["navy"], font=font_tag, anchor="mm")

    font_t = get_font(26, bold=True)
    banner_draw.text((32, photo_h + 74), title, fill=PALETTE["white"], font=font_t, anchor="lm")

    mask = Image.new("L", (card_w, card_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, card_w, card_h], radius=r, fill=255)

    border_draw = ImageDraw.Draw(card)
    border_draw.rounded_rectangle([0, 0, card_w - 1, card_h - 1], radius=r, outline=PALETTE["gold"], width=3)

    canvas.paste(card, (cx, cy), mask)
    canvas.save(out_path, "PNG")
    return out_path


def main() -> None:
    for spec in CARD_SPECS:
        img_path = resolve_asset(spec["img"])
        badge_path = resolve_asset(spec["badge"]) if spec["badge"] else None
        out = create_card(img_path, spec["title"], spec["tag"], badge_path, CARDS_DIR / spec["out"])
        print(f"Created card: {out} (from {ASSETS_DIR})")


if __name__ == "__main__":
    main()
