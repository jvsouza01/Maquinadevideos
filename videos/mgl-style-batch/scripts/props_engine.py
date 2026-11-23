"""Motor de artes componiveis e cue-driven (Props Engine v2) para HyperFrames.

Suporta componentes dinamicos configuraveis via JSON da cena:
- cards_stack / checklist / spy-table / split-wheel-checklist
- comparison_doors / versus_grid / doors-platforms / door-crowd
- flow_steps / flow-nodes
- bar_chart / metrics_board / bar-chart-cta
- product_shelf / offer_showcase

Cada sub-elemento emite atributos `data-cue-step`, `data-cue-word`, `data-cue-anim`
e `data-cue-sfx` para que o Word-Cue Engine dispare no instante exato da fala.
"""
from __future__ import annotations

import html
from typing import Any


def _cue_attrs(
    step: int,
    cue_word: str | None = None,
    anim: str = "pop-overshoot",
    sfx: str | None = None,
    fallback_ratio: float = 0.25,
) -> str:
    parts = [
        f'data-cue-step="{step}"',
        f'data-cue-anim="{html.escape(anim)}"',
        f'data-cue-fallback="{fallback_ratio:.2f}"',
    ]
    if cue_word:
        parts.append(f'data-cue-word="{html.escape(str(cue_word))}"')
    if sfx:
        parts.append(f'data-cue-sfx="{html.escape(str(sfx))}"')
    return " ".join(parts)


def _platform_icon_svg(kind: str, x: int, y: int) -> str:
    if kind == "flame":
        return f"""
        <rect x="{x}" y="{y}" width="104" height="104" rx="22" fill="#FFFFFF" stroke="#14161D" stroke-width="5"/>
        <path d="M{x+54} {y+26} C{x+70} {y+42} {x+72} {y+70} {x+52} {y+78} C{x+34} {y+78} {x+32} {y+52} {x+46} {y+40} C{x+48} {y+50} {x+56} {y+52} {x+54} {y+26} Z" fill="#FF5A26"/>
        <circle cx="{x+52}" cy="{y+62}" r="8" fill="#FFFFFF"/>"""
    if kind == "arc":
        return f"""
        <rect x="{x}" y="{y}" width="104" height="104" rx="22" fill="#FFFFFF" stroke="#14161D" stroke-width="5"/>
        <path d="M{x+28} {y+48} A26 26 0 1 0 {x+78} {y+48}" fill="none" stroke="#12B886" stroke-width="11" stroke-linecap="round"/>
        <circle cx="{x+52}" cy="{y+54}" r="6" fill="#12B886"/>"""
    if kind == "cactus":
        return f"""
        <rect x="{x}" y="{y}" width="104" height="104" rx="22" fill="#FFFFFF" stroke="#14161D" stroke-width="5"/>
        <rect x="{x+15}" y="{y+15}" width="74" height="74" rx="14" fill="#23654B"/>
        <path d="M{x+52} {y+31} L{x+52} {y+75} M{x+52} {y+49} L{x+38} {y+49} L{x+38} {y+39} M{x+52} {y+59} L{x+66} {y+59} L{x+66} {y+47}" fill="none" stroke="#FFFFFF" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>"""
    if kind == "check":
        return f"""
        <rect x="{x}" y="{y}" width="104" height="104" rx="22" fill="#D0EB2F" stroke="#14161D" stroke-width="5"/>
        <path d="M{x+32} {y+54} L{x+46} {y+68} L{x+74} {y+36}" fill="none" stroke="#14161D" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>"""
    # default bolt/spark
    return f"""
    <rect x="{x}" y="{y}" width="104" height="104" rx="22" fill="#FFFFFF" stroke="#14161D" stroke-width="5"/>
    <polygon points="{x+56},{y+24} {x+34},{y+56} {x+52},{y+56} {x+46},{y+82} {x+70},{y+48} {x+52},{y+48}" fill="#D0EB2F" stroke="#14161D" stroke-width="3.5" stroke-linejoin="round"/>"""


def render_prop(prop: str, theme_key: str, prop_data: dict[str, Any] | None = None) -> str:
    data = prop_data or {}
    stroke_col = "#14161D"

    # 1) SPLIT WHEEL + CHECKLIST
    if prop in ("split-wheel-checklist", "wheel_checklist"):
        cues = data.get("cues", [])
        c1 = cues[0] if len(cues) > 0 else "vende"
        c2 = cues[1] if len(cues) > 1 else "modela"
        c3 = cues[2] if len(cues) > 2 else "funciona"
        return f"""
        <svg class="prop-svg" viewBox="0 0 500 420" width="500" height="420">
          <g class="prop-base prop-wheel" style="transform-origin: 120px 248px;">
            <circle cx="120" cy="248" r="88" fill="#8C93A3" stroke="{stroke_col}" stroke-width="6"/>
            <circle cx="120" cy="248" r="64" fill="#B5BBC8" stroke="{stroke_col}" stroke-width="4"/>
            <line x1="120" y1="184" x2="120" y2="312" stroke="{stroke_col}" stroke-width="5"/>
            <line x1="56" y1="248" x2="184" y2="248" stroke="{stroke_col}" stroke-width="5"/>
            <line x1="75" y1="203" x2="165" y2="293" stroke="{stroke_col}" stroke-width="5"/>
            <line x1="165" y1="203" x2="75" y2="293" stroke="{stroke_col}" stroke-width="5"/>
            <circle cx="120" cy="248" r="18" fill="#14161D"/>
          </g>
          <g class="prop-base" style="transform-origin: 290px 260px;">
            <circle cx="290" cy="182" r="36" fill="#14161D"/>
            <path d="M234 328 C234 252 346 252 346 328 Z" fill="#14161D"/>
          </g>
          <g class="prop-base prop-float-idle" style="transform-origin: 402px 187px;">
            <rect x="330" y="76" width="144" height="222" rx="20" fill="#FFFFFF" stroke="{stroke_col}" stroke-width="5"/>
            <rect x="380" y="64" width="44" height="20" rx="8" fill="#14161D"/>
            <rect x="352" y="106" width="84" height="14" rx="7" fill="#14161D"/>
            <rect x="352" y="132" width="100" height="14" rx="7" fill="#14161D"/>
            <rect x="352" y="158" width="68" height="14" rx="7" fill="#14161D"/>
            <g {_cue_attrs(1, c1, 'pop-overshoot', 'pop', 0.35)} style="transform-origin: 402px 201px;">
              <rect x="352" y="192" width="100" height="18" rx="9" fill="#D0EB2F" stroke="{stroke_col}" stroke-width="3"/>
            </g>
            <g {_cue_attrs(2, c2, 'pop-overshoot', 'click', 0.55)} style="transform-origin: 395px 229px;">
              <rect x="352" y="220" width="86" height="18" rx="9" fill="#D0EB2F" stroke="{stroke_col}" stroke-width="3"/>
            </g>
            <g {_cue_attrs(3, c3, 'pop-overshoot', None, 0.72)} style="transform-origin: 399px 257px;">
              <rect x="352" y="248" width="94" height="18" rx="9" fill="#D0EB2F" stroke="{stroke_col}" stroke-width="3"/>
            </g>
          </g>
        </svg>"""

    # 2) COMPARISON DOORS / PLATFORMS
    if prop in ("doors-platforms", "comparison_doors"):
        doors = data.get(
            "doors",
            [
                {"icon": "flame", "cue_word": "chute", "stamp": "cash"},
                {"icon": "arc", "cue_word": "plataformas", "stamp": "cash"},
                {"icon": "cactus", "cue_word": "torra", "stamp": "cash"},
            ],
        )
        doors_svg = []
        badges_svg = []
        for idx, d in enumerate(doors[:3]):
            dx = 36 + idx * 126
            cx = dx + 57
            cue_w = d.get("cue_word")
            icon_k = d.get("icon", ["flame", "arc", "cactus"][idx % 3])
            stamp_k = d.get("stamp", "cash")
            ratio = 0.22 + idx * 0.22
            # Door itself falls in staggered at scene start
            doors_svg.append(
                f"""
            <g class="prop-stagger-drop" style="transform-origin: {cx}px 289px;">
              <rect x="{dx}" y="176" width="114" height="226" rx="10" fill="#EAEBEE" stroke="#14161D" stroke-width="5"/>
              <rect x="{dx+16}" y="194" width="82" height="78" rx="6" fill="#D4D8E0"/>
              <rect x="{dx+16}" y="290" width="82" height="92" rx="6" fill="#D4D8E0"/>
              <circle cx="{dx+96}" cy="282" r="7" fill="#14161D"/>
            </g>"""
            )
            # Badge + bill/stamp pop in at exact cue_word
            stamp_svg = ""
            if stamp_k == "cash":
                stamp_svg = f'<rect x="{dx+14}" y="294" width="76" height="40" rx="8" fill="#18A957" stroke="#14161D" stroke-width="3.5" transform="rotate(-12 {dx+52} 314)"/><circle cx="{dx+52}" cy="314" r="10" fill="#8CE99A"/>'
            elif stamp_k == "x":
                stamp_svg = f'<circle cx="{cx}" cy="285" r="28" fill="#EF4444" stroke="#14161D" stroke-width="4"/><path d="M{cx-11} 274 L{cx+11} 296 M{cx+11} 274 L{cx-11} 296" stroke="#FFFFFF" stroke-width="6" stroke-linecap="round"/>'
            elif stamp_k == "ok":
                stamp_svg = f'<circle cx="{cx}" cy="285" r="28" fill="#D0EB2F" stroke="#14161D" stroke-width="4"/><path d="M{cx-12} 285 L{cx-3} 294 L{cx+14} 275" fill="none" stroke="#14161D" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'

            badges_svg.append(
                f"""
            <g {_cue_attrs(idx + 1, cue_w, 'pop-spin', 'pop' if idx == 0 else 'click', ratio)} style="transform-origin: {cx}px 106px;">
              {_platform_icon_svg(icon_k, dx + 5, 54)}
              {stamp_svg}
            </g>"""
            )
        return f"""
        <svg class="prop-svg" viewBox="0 0 500 420" width="500" height="420">
          {''.join(doors_svg)}
          {''.join(badges_svg)}
        </svg>"""

    # 3) VERSUS GRID
    if prop == "versus_grid":
        left_title = html.escape(str(data.get("leftTitle", "SEM MÉTODO")))
        right_title = html.escape(str(data.get("rightTitle", "COM ESCALA")))
        c_left = data.get("leftCue")
        c_right = data.get("rightCue")
        return f"""
        <svg class="prop-svg" viewBox="0 0 500 420" width="500" height="420">
          <g {_cue_attrs(1, c_left, 'slide-left', 'click', 0.25)} style="transform-origin: 124px 230px;">
            <rect x="24" y="100" width="200" height="260" rx="24" fill="#FFFFFF" stroke="#14161D" stroke-width="5"/>
            <text x="124" y="152" text-anchor="middle" fill="#14161D" font-family="Sora, sans-serif" font-weight="800" font-size="22">{left_title}</text>
            <circle cx="124" cy="245" r="44" fill="#EF4444" stroke="#14161D" stroke-width="4"/>
            <path d="M106 227 L142 263 M142 227 L106 263" stroke="#FFFFFF" stroke-width="8" stroke-linecap="round"/>
          </g>
          <g {_cue_attrs(2, c_right, 'pop-overshoot', 'pop', 0.55)} style="transform-origin: 356px 230px;">
            <rect x="256" y="84" width="212" height="284" rx="24" fill="#D0EB2F" stroke="#14161D" stroke-width="5"/>
            <text x="362" y="140" text-anchor="middle" fill="#14161D" font-family="Sora, sans-serif" font-weight="800" font-size="22">{right_title}</text>
            <circle cx="362" cy="242" r="48" fill="#14161D"/>
            <path d="M340 242 L355 257 L386 224" fill="none" stroke="#D0EB2F" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>
          </g>
        </svg>"""

    # 4) DOOR CROWD
    if prop == "door-crowd":
        c_open = data.get("openCue", "espia")
        c_crowd = data.get("crowdCue", "gente")
        return f"""
        <svg class="prop-svg" viewBox="0 0 500 420" width="500" height="420">
          <g class="prop-base" style="transform-origin: 110px 260px;">
            <circle cx="110" cy="168" r="40" fill="#14161D"/>
            <path d="M36 374 C36 244 184 244 184 374 Z" fill="#14161D"/>
          </g>
          <g class="prop-base" style="transform-origin: 340px 248px;">
            <rect x="260" y="122" width="160" height="252" rx="14" fill="#FFFFFF" stroke="#14161D" stroke-width="5"/>
            <g {_cue_attrs(1, c_crowd, 'slide-up', 'pop', 0.45)} style="transform-origin: 354px 310px;">
              <circle cx="322" cy="264" r="20" fill="#14161D"/>
              <path d="M292 368 C292 308 352 308 352 368 Z" fill="#14161D"/>
              <circle cx="364" cy="258" r="18" fill="#3A3F4B"/>
              <path d="M338 368 C338 314 390 314 390 368 Z" fill="#3A3F4B"/>
              <circle cx="394" cy="266" r="16" fill="#636B7C"/>
              <path d="M372 368 C372 322 416 322 416 368 Z" fill="#636B7C"/>
            </g>
            <g {_cue_attrs(2, c_open, 'door-swing', None, 0.20)} style="transform-origin: 260px 248px;">
              <polygon points="260,122 192,102 192,386 260,374" fill="#EAEBEE" stroke="#14161D" stroke-width="5" stroke-linejoin="round"/>
              <circle cx="206" cy="252" r="6" fill="#14161D"/>
            </g>
          </g>
        </svg>"""

    # 5) CARDS STACK / CHECKLIST / SPY-TABLE
    if prop in ("spy-table", "cards_stack", "checklist"):
        items = data.get("items") or [
            {"title": "TOP #1 IA", "badge": "23.2k", "active": True, "cue_word": "três"},
            {"title": "TOP #2 IA", "badge": "10.3k", "active": False, "cue_word": "inteligência"},
            {"title": "TOP #3 IA", "badge": "8.7k", "active": False, "cue_word": "acessados"},
            {"title": "TOP #4 IA", "badge": "6.1k", "active": False, "cue_word": "momento"},
        ]
        rows_svg = []
        for idx, item in enumerate(items[:4]):
            ry = 192 + idx * 44
            is_act = item.get("active", idx == 0)
            dot_fill = "#D0EB2F" if is_act else "#D4D8E0"
            bar_fill = "#14161D" if is_act else "#646D80"
            pill_fill = "#D0EB2F" if is_act else "#D4D8E0"
            title_txt = html.escape(str(item.get("title", f"ITEM #{idx+1}")))
            badge_txt = html.escape(str(item.get("badge", "")))
            cue_w = item.get("cue_word")
            rows_svg.append(
                f"""
            <g {_cue_attrs(idx + 1, cue_w, 'slide-left', 'click' if idx == 0 else None, 0.22 + idx * 0.16)} style="transform-origin: 241px {ry+18}px;">
              <rect x="52" y="{ry}" width="378" height="36" rx="11" fill="#F6F7FA" stroke="#D4D8E0" stroke-width="2.5"/>
              <circle cx="72" cy="{ry+18}" r="8" fill="{dot_fill}" stroke="#14161D" stroke-width="2.5"/>
              <text x="92" y="{ry+23}" fill="{bar_fill}" font-family="Sora, sans-serif" font-weight="700" font-size="16">{title_txt}</text>
              <rect x="336" y="{ry+6}" width="80" height="24" rx="8" fill="{pill_fill}"/>
              <text x="376" y="{ry+23}" text-anchor="middle" fill="#14161D" font-family="Sora, sans-serif" font-weight="800" font-size="14">{badge_txt}</text>
            </g>"""
            )
        return f"""
        <svg class="prop-svg" viewBox="0 0 500 420" width="500" height="420">
          <g class="prop-base" style="transform-origin: 241px 210px;">
            <rect x="26" y="42" width="430" height="338" rx="26" fill="#FFFFFF" stroke="#14161D" stroke-width="5"/>
            <rect x="52" y="64" width="44" height="44" rx="12" fill="#D0EB2F" stroke="#14161D" stroke-width="4"/>
            <rect x="114" y="76" width="120" height="20" rx="10" fill="#14161D"/>
            <rect x="336" y="78" width="94" height="16" rx="8" fill="#D4D8E0"/>
            <line x1="26" y1="126" x2="456" y2="126" stroke="#E2E5EC" stroke-width="3"/>
            <rect x="52" y="144" width="112" height="32" rx="16" fill="#D4D8E0"/>
            <rect x="180" y="144" width="112" height="32" rx="16" fill="#D4D8E0"/>
            <rect x="308" y="144" width="112" height="32" rx="16" fill="#D4D8E0"/>
          </g>
          {''.join(rows_svg)}
        </svg>"""

    # 6) PRODUCT SHELF / OFFER SHOWCASE
    if prop in ("product-shelf", "offer_showcase"):
        tag_text = html.escape(str(data.get("tag", "R$ 197")))
        label_text = html.escape(str(data.get("label", "PRODUTO IA")))
        bumps = int(data.get("bumps", 2))
        tag_cue = data.get("tagCue", "nove")
        bump_cue = data.get("bumpCue", "order")
        bump_rects = []
        for idx in range(min(bumps, 3)):
            bx = 248 + idx * 54
            bump_rects.append(
                f"""
            <g {_cue_attrs(2 + idx, bump_cue, 'pop-overshoot', 'pop' if idx == 0 else None, 0.56 + idx * 0.08)} style="transform-origin: {bx+22}px 242px;">
              <rect x="{bx}" y="220" width="44" height="44" rx="10" fill="#D0EB2F" stroke="#14161D" stroke-width="4"/>
            </g>"""
            )
        return f"""
        <svg class="prop-svg" viewBox="0 0 500 420" width="500" height="420">
          <g class="prop-base" style="transform-origin: 239px 305px;">
            <rect x="44" y="274" width="390" height="22" rx="11" fill="#FFFFFF" stroke="#14161D" stroke-width="4"/>
            <rect x="76" y="296" width="326" height="42" rx="6" fill="#1B1E28" stroke="#363B4D" stroke-width="3"/>
          </g>
          <g class="prop-base" style="transform-origin: 142px 206px;">
            <rect x="64" y="138" width="156" height="136" rx="22" fill="#151824" stroke="#FFFFFF" stroke-width="5"/>
            <rect x="82" y="156" width="120" height="48" rx="10" fill="#23283B"/>
            <text x="142" y="187" text-anchor="middle" fill="#D0EB2F" font-family="Sora, sans-serif" font-weight="800" font-size="17">{label_text}</text>
            <rect x="82" y="218" width="76" height="12" rx="6" fill="#FFFFFF"/>
            <rect x="82" y="238" width="108" height="10" rx="5" fill="#7D8596"/>
          </g>
          <g {_cue_attrs(1, tag_cue, 'pop-spin', 'click', 0.36)} style="transform-origin: 252px 152px;">
            <g transform="rotate(14 252 152)">
              <rect x="194" y="124" width="118" height="58" rx="14" fill="#D0EB2F" stroke="#14161D" stroke-width="4"/>
              <circle cx="212" cy="153" r="6" fill="#14161D"/>
              <text x="262" y="160" text-anchor="middle" fill="#11131A" font-family="Sora, sans-serif" font-weight="800" font-size="20">{tag_text}</text>
            </g>
          </g>
          {''.join(bump_rects)}
        </svg>"""

    # 7) FLOW STEPS / FLOW-NODES
    if prop in ("flow-nodes", "flow_steps"):
        steps = data.get("steps") or [
            {"label": "INPUT", "active": False, "cue_word": "segundo"},
            {"label": "IA CORE", "active": True, "cue_word": "Fluxo"},
            {"label": "AUTOMAÇÃO", "active": False, "cue_word": "dez"},
        ]
        s0 = html.escape(str(steps[0]["label"])) if len(steps) > 0 else "PASSO 1"
        s1 = html.escape(str(steps[1]["label"])) if len(steps) > 1 else "PASSO 2"
        s2 = html.escape(str(steps[2]["label"])) if len(steps) > 2 else "PASSO 3"
        c0 = steps[0].get("cue_word") if len(steps) > 0 else None
        c1 = steps[1].get("cue_word") if len(steps) > 1 else None
        c2 = steps[2].get("cue_word") if len(steps) > 2 else None
        c_out = data.get("outCue", "código")
        return f"""
        <svg class="prop-svg" viewBox="0 0 500 420" width="500" height="420">
          <!-- Paths desenhados via stroke-dashoffset no cue -->
          <path class="cue-stroke-draw" {_cue_attrs(1, c0, 'stroke-draw', None, 0.20)} d="M138 220 C190 220 190 128 246 128" fill="none" stroke="#8C93A3" stroke-width="5" stroke-linecap="round"/>
          <path class="cue-stroke-draw" {_cue_attrs(2, c1, 'stroke-draw', None, 0.38)} d="M138 220 L246 220" fill="none" stroke="#D0EB2F" stroke-width="6" stroke-linecap="round"/>
          <path class="cue-stroke-draw" {_cue_attrs(3, c2, 'stroke-draw', None, 0.54)} d="M138 220 C190 220 190 312 246 312" fill="none" stroke="#8C93A3" stroke-width="5" stroke-linecap="round"/>
          <path class="cue-stroke-draw" {_cue_attrs(4, c_out, 'stroke-draw', None, 0.72)} d="M380 220 L406 220" fill="none" stroke="#D0EB2F" stroke-width="6" stroke-linecap="round"/>

          <g class="prop-base" style="transform-origin: 92px 220px;">
            <rect x="44" y="176" width="96" height="88" rx="20" fill="#1F2330" stroke="#FFFFFF" stroke-width="4"/>
            <circle cx="92" cy="212" r="18" fill="#D0EB2F"/>
            <rect x="66" y="240" width="52" height="8" rx="4" fill="#FFFFFF"/>
          </g>
          <g {_cue_attrs(1, c0, 'pop-overshoot', 'click', 0.22)} style="transform-origin: 312px 128px;">
            <rect x="244" y="92" width="136" height="72" rx="18" fill="#FFFFFF" stroke="#14161D" stroke-width="4"/>
            <text x="312" y="134" text-anchor="middle" fill="#14161D" font-family="Sora, sans-serif" font-weight="800" font-size="14">{s0}</text>
          </g>
          <g {_cue_attrs(2, c1, 'pop-overshoot', 'pop', 0.40)} style="transform-origin: 312px 220px;">
            <rect x="244" y="184" width="136" height="72" rx="18" fill="#D0EB2F" stroke="#14161D" stroke-width="4"/>
            <text x="312" y="226" text-anchor="middle" fill="#14161D" font-family="Sora, sans-serif" font-weight="800" font-size="14">{s1}</text>
          </g>
          <g {_cue_attrs(3, c2, 'pop-overshoot', None, 0.56)} style="transform-origin: 312px 312px;">
            <rect x="244" y="276" width="136" height="72" rx="18" fill="#FFFFFF" stroke="#14161D" stroke-width="4"/>
            <text x="312" y="318" text-anchor="middle" fill="#14161D" font-family="Sora, sans-serif" font-weight="800" font-size="14">{s2}</text>
          </g>
          <g {_cue_attrs(4, c_out, 'pop-spin', 'click', 0.74)} style="transform-origin: 444px 220px;">
            <rect x="406" y="172" width="76" height="96" rx="20" fill="#1F2330" stroke="#D0EB2F" stroke-width="4"/>
            <path d="M428 220 L440 232 L460 206" fill="none" stroke="#D0EB2F" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
          </g>
        </svg>"""

    # 8) METRICS BOARD
    if prop == "metrics_board":
        kpis = data.get("kpis") or [
            {"label": "VISITAS", "target": 23206, "prefix": "", "cue_word": "vinte"},
            {"label": "CONV.", "target": 14, "prefix": "", "suffix": "%", "cue_word": "checkout"},
        ]
        cards = []
        for idx, k in enumerate(kpis[:2]):
            kx = 34 + idx * 218
            lbl = html.escape(str(k.get("label", "KPI")))
            tgt = int(k.get("target", 100))
            pref = html.escape(str(k.get("prefix", "")))
            suff = html.escape(str(k.get("suffix", "")))
            cue_w = k.get("cue_word")
            cards.append(
                f"""
            <g {_cue_attrs(idx + 1, cue_w, 'pop-overshoot', 'pop', 0.25 + idx * 0.25)} style="transform-origin: {kx+98}px 220px;">
              <rect x="{kx}" y="120" width="196" height="200" rx="24" fill="#FFFFFF" stroke="#14161D" stroke-width="5"/>
              <rect x="{kx+20}" y="144" width="108" height="28" rx="14" fill="#D0EB2F"/>
              <text x="{kx+74}" y="163" text-anchor="middle" fill="#14161D" font-family="Sora, sans-serif" font-weight="800" font-size="14">{lbl}</text>
              <text class="cue-count-up" data-count-target="{tgt}" data-count-prefix="{pref}" data-count-suffix="{suff}" x="{kx+98}" y="252" text-anchor="middle" fill="#14161D" font-family="Sora, sans-serif" font-weight="800" font-size="38" style="font-variant-numeric: tabular-nums;">{pref}{tgt}{suff}</text>
            </g>"""
            )
        return f"""<svg class="prop-svg" viewBox="0 0 500 420" width="500" height="420">{''.join(cards)}</svg>"""

    # 8.1) ELEVATOR INCIDENT (Cena 1 - Hook)
    if prop == "elevator_incident":
        c_quote = data.get("quoteCue", "cheiro")
        c_alert = data.get("alertCue", "sentindo")
        return f"""
        <svg class="prop-svg" viewBox="0 0 500 420" width="500" height="420">
          <!-- Moldura Elevador -->
          <g class="prop-base" style="transform-origin: 210px 235px;">
            <rect x="64" y="96" width="290" height="284" rx="18" fill="#1E222E" stroke="#14161D" stroke-width="5"/>
            <rect x="172" y="62" width="76" height="24" rx="8" fill="#14161D"/>
            <circle cx="198" cy="74" r="5" fill="#D0EB2F"/>
            <polygon points="218,79 224,69 230,79" fill="#D0EB2F"/>
            <!-- Silhuetas colegas dentro -->
            <circle cx="152" cy="216" r="26" fill="#3B4154"/>
            <path d="M104 358 C104 268 200 268 200 358 Z" fill="#3B4154"/>
            <circle cx="258" cy="222" r="24" fill="#4E556B"/>
            <path d="M214 358 C214 276 302 276 302 358 Z" fill="#4E556B"/>
            <!-- Portas metalicas fechando -->
            <rect x="82" y="114" width="126" height="248" rx="6" fill="#C7CCD8" stroke="#14161D" stroke-width="4" opacity="0.92"/>
            <rect x="210" y="114" width="126" height="248" rx="6" fill="#B5BBC9" stroke="#14161D" stroke-width="4" opacity="0.92"/>
            <line x1="209" y1="114" x2="209" y2="362" stroke="#14161D" stroke-width="4"/>
          </g>
          <!-- Ondas de alerta / cheiro -->
          <g {_cue_attrs(1, c_alert, 'pop-overshoot', None, 0.35)} style="transform-origin: 390px 230px;">
            <path d="M378 210 Q396 190 380 170 Q366 150 386 130" fill="none" stroke="#D0EB2F" stroke-width="6" stroke-linecap="round"/>
            <path d="M406 218 Q424 196 408 176 Q394 156 414 136" fill="none" stroke="#D0EB2F" stroke-width="5" stroke-linecap="round" opacity="0.8"/>
          </g>
          <!-- Balao de fala do colega -->
          <g {_cue_attrs(2, c_quote, 'pop-spin', 'pop', 0.55)} style="transform-origin: 250px 76px;">
            <rect x="74" y="18" width="356" height="84" rx="24" fill="#D0EB2F" stroke="#14161D" stroke-width="5"/>
            <polygon points="184,102 204,126 224,102" fill="#D0EB2F" stroke="#14161D" stroke-width="4" stroke-linejoin="round"/>
            <text x="252" y="54" text-anchor="middle" fill="#11131A" font-family="Sora, sans-serif" font-weight="800" font-size="21">“Vocês tão sentindo</text>
            <text x="252" y="82" text-anchor="middle" fill="#11131A" font-family="Sora, sans-serif" font-weight="800" font-size="22">esse cheiro?”</text>
          </g>
        </svg>"""

    # 8.2) OFFICE CLOCK + THOUGHT (Cena 2 - Hook em off)
    if prop == "office_clock_thought":
        c_day = data.get("dayCue", "resto")
        c_thought = data.get("thoughtCue", "sido")
        return f"""
        <svg class="prop-svg" viewBox="0 0 500 420" width="500" height="420">
          <!-- Relogio do dia passando -->
          <g {_cue_attrs(1, c_day, 'pop-overshoot', 'click', 0.28)} style="transform-origin: 150px 210px;">
            <circle cx="150" cy="210" r="102" fill="#FFFFFF" stroke="#14161D" stroke-width="6"/>
            <circle cx="150" cy="210" r="84" fill="#F4F6FA" stroke="#D4D8E0" stroke-width="3"/>
            <line x1="150" y1="142" x2="150" y2="154" stroke="#14161D" stroke-width="5" stroke-linecap="round"/>
            <line x1="150" y1="266" x2="150" y2="278" stroke="#14161D" stroke-width="5" stroke-linecap="round"/>
            <line x1="82" y1="210" x2="94" y2="210" stroke="#14161D" stroke-width="5" stroke-linecap="round"/>
            <line x1="206" y1="210" x2="218" y2="210" stroke="#14161D" stroke-width="5" stroke-linecap="round"/>
            <g class="prop-wheel" style="transform-origin: 150px 210px;">
              <line x1="150" y1="210" x2="150" y2="154" stroke="#14161D" stroke-width="7" stroke-linecap="round"/>
            </g>
            <line x1="150" y1="210" x2="192" y2="210" stroke="#D0EB2F" stroke-width="7" stroke-linecap="round"/>
            <circle cx="150" cy="210" r="10" fill="#14161D"/>
          </g>
          <!-- Olhares + Balao de duvida -->
          <g {_cue_attrs(2, c_thought, 'pop-spin', 'pop', 0.62)} style="transform-origin: 344px 168px;">
            <rect x="220" y="96" width="248" height="114" rx="26" fill="#FFFFFF" stroke="#14161D" stroke-width="5"/>
            <circle cx="256" cy="226" r="12" fill="#FFFFFF" stroke="#14161D" stroke-width="4"/>
            <circle cx="240" cy="252" r="8" fill="#FFFFFF" stroke="#14161D" stroke-width="3.5"/>
            <rect x="242" y="114" width="204" height="34" rx="10" fill="#D0EB2F"/>
            <text x="344" y="138" text-anchor="middle" fill="#11131A" font-family="Sora, sans-serif" font-weight="800" font-size="18">“Devia ter</text>
            <text x="344" y="182" text-anchor="middle" fill="#11131A" font-family="Sora, sans-serif" font-weight="800" font-size="22">sido eu?”</text>
          </g>
        </svg>"""

    # 8.3) CHAT REWRITE (Cena 3 - Digita "to indo", apaga e envia "hoje nao consigo")
    if prop == "chat_rewrite":
        c_in = data.get("inCue", "mensagem")
        c_draft = data.get("draftCue", "indo")
        c_del = data.get("deleteCue", "apaga")
        c_final = data.get("finalCue", "hoje")
        return f"""
        <svg class="prop-svg" viewBox="0 0 500 420" width="500" height="420">
          <!-- Moldura Celular -->
          <g class="prop-base" style="transform-origin: 240px 210px;">
            <rect x="74" y="34" width="332" height="360" rx="34" fill="#14161D" stroke="#FFFFFF" stroke-width="4"/>
            <rect x="90" y="50" width="300" height="328" rx="24" fill="#ECE5DD"/>
            <!-- Header WhatsApp -->
            <rect x="90" y="50" width="300" height="54" rx="24" fill="#075E54"/>
            <rect x="90" y="80" width="300" height="24" fill="#075E54"/>
            <circle cx="122" cy="78" r="15" fill="#D0EB2F"/>
            <text x="148" y="84" fill="#FFFFFF" font-family="Sora, sans-serif" font-weight="800" font-size="16">Amigas do Trabalho</text>
          </g>
          <!-- Msg recebida -->
          <g {_cue_attrs(1, c_in, 'slide-left', 'notification', 0.18)} style="transform-origin: 205px 144px;">
            <rect x="106" y="118" width="218" height="54" rx="16" fill="#FFFFFF" stroke="#D4D8E0" stroke-width="2.5"/>
            <text x="122" y="151" fill="#14161D" font-family="Sora, sans-serif" font-weight="700" font-size="17">Almoço com a gente?</text>
          </g>
          <!-- Rascunho digitado "to indo" -->
          <g {_cue_attrs(2, c_draft, 'pop-overshoot', 'click', 0.42)} style="transform-origin: 294px 214px;">
            <rect x="210" y="186" width="164" height="50" rx="16" fill="#DCF8C6" stroke="#A7D489" stroke-width="2.5"/>
            <text x="292" y="217" text-anchor="middle" fill="#14161D" font-family="Sora, sans-serif" font-weight="700" font-size="18">tô indo!</text>
          </g>
          <!-- Risco vermelho / X ao apagar -->
          <g {_cue_attrs(3, c_del, 'pop-spin', 'pop', 0.58)} style="transform-origin: 292px 211px;">
            <line x1="218" y1="211" x2="364" y2="211" stroke="#EF4444" stroke-width="6" stroke-linecap="round"/>
            <circle cx="368" cy="192" r="16" fill="#EF4444" stroke="#FFFFFF" stroke-width="2.5"/>
            <path d="M362 186 L374 198 M374 186 L362 198" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>
          </g>
          <!-- Resposta final enviada -->
          <g {_cue_attrs(4, c_final, 'pop-overshoot', 'pop', 0.74)} style="transform-origin: 266px 294px;">
            <rect x="150" y="260" width="224" height="58" rx="18" fill="#14161D"/>
            <text x="262" y="295" text-anchor="middle" fill="#D0EB2F" font-family="Sora, sans-serif" font-weight="800" font-size="18">hoje não consigo</text>
          </g>
        </svg>"""

    # 8.4) COPA COFFEE TALK (Cena 5 - Amiga encontra Marina com cafe frio)
    if prop == "copa_coffee_talk":
        c_q = data.get("questionCue", "fugindo")
        c_ans = data.get("answerCue", "medo")
        return f"""
        <svg class="prop-svg" viewBox="0 0 500 420" width="500" height="420">
          <!-- Balcao da copa + Xicara fria -->
          <g class="prop-base" style="transform-origin: 240px 330px;">
            <rect x="44" y="308" width="390" height="22" rx="11" fill="#FFFFFF" stroke="#14161D" stroke-width="4"/>
            <rect x="74" y="330" width="330" height="42" rx="6" fill="#1E222E" stroke="#363B4D" stroke-width="3"/>
            <path d="M98 242 L156 242 L149 306 Q127 312 105 306 Z" fill="#FFFFFF" stroke="#14161D" stroke-width="4.5"/>
            <path d="M155 252 Q174 252 174 270 Q174 286 152 286" fill="none" stroke="#14161D" stroke-width="5" stroke-linecap="round"/>
            <ellipse cx="127" cy="242" rx="29" ry="7" fill="#523324" stroke="#14161D" stroke-width="3"/>
            <text x="127" y="282" text-anchor="middle" fill="#64748B" font-family="Sora, sans-serif" font-weight="800" font-size="13">FRIO</text>
          </g>
          <!-- Balao Amiga -->
          <g {_cue_attrs(1, c_q, 'slide-left', 'pop', 0.16)} style="transform-origin: 240px 92px;">
            <rect x="44" y="42" width="368" height="72" rx="22" fill="#D0EB2F" stroke="#14161D" stroke-width="4.5"/>
            <text x="228" y="85" text-anchor="middle" fill="#11131A" font-family="Sora, sans-serif" font-weight="800" font-size="21">“Você tá fugindo de mim?”</text>
          </g>
          <!-- Balao Marina -->
          <g {_cue_attrs(2, c_ans, 'pop-overshoot', 'click', 0.56)} style="transform-origin: 270px 184px;">
            <rect x="92" y="136" width="374" height="84" rx="22" fill="#14161D" stroke="#FFFFFF" stroke-width="4"/>
            <text x="279" y="172" text-anchor="middle" fill="#FFFFFF" font-family="Sora, sans-serif" font-weight="700" font-size="18">“Medo de alguém</text>
            <text x="279" y="198" text-anchor="middle" fill="#D0EB2F" font-family="Sora, sans-serif" font-weight="800" font-size="20">sentir meu cheiro.”</text>
          </g>
        </svg>"""

    # 8.5) COPA CHAIRS SUPPORT (Cena 6 - Amiga puxa cadeira e acolhe)
    if prop == "copa_chairs_support":
        c_chair = data.get("chairCue", "cadeira")
        c_sit = data.get("sitCue", "sentar")
        return f"""
        <svg class="prop-svg" viewBox="0 0 500 420" width="500" height="420">
          <!-- Mesa + Cadeira fixa -->
          <g class="prop-base" style="transform-origin: 220px 290px;">
            <rect x="148" y="246" width="168" height="18" rx="9" fill="#FFFFFF" stroke="#14161D" stroke-width="4.5"/>
            <rect x="224" y="264" width="16" height="114" rx="6" fill="#14161D"/>
            <rect x="178" y="366" width="108" height="14" rx="7" fill="#14161D"/>
            <!-- Cadeira esquerda -->
            <path d="M68 202 L68 378 M68 292 L134 292 L134 378" fill="none" stroke="#14161D" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
          </g>
          <!-- Cadeira da amiga deslizando para perto -->
          <g {_cue_attrs(1, c_chair, 'slide-left', 'whoosh-short', 0.20)} style="transform-origin: 374px 290px;">
            <path d="M402 202 L402 378 M402 292 L336 292 L336 378" fill="none" stroke="#D0EB2F" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M402 202 L402 378 M402 292 L336 292 L336 378" fill="none" stroke="#14161D" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
          </g>
          <!-- Balao acolhedor -->
          <g {_cue_attrs(2, c_sit, 'pop-overshoot', 'sparkle', 0.56)} style="transform-origin: 250px 112px;">
            <rect x="64" y="56" width="372" height="90" rx="24" fill="#FFFFFF" stroke="#14161D" stroke-width="5"/>
            <text x="250" y="96" text-anchor="middle" fill="#14161D" font-family="Sora, sans-serif" font-weight="800" font-size="21">“Posso sentar aqui</text>
            <text x="250" y="124" text-anchor="middle" fill="#14161D" font-family="Sora, sans-serif" font-weight="800" font-size="21">com você?”</text>
          </g>
        </svg>"""

    # 8.6) REVENUE CLEAN SHOWCASE (Cena 7 - Embalagem 2.5D Premium + Mensagem + CTA)
    if prop == "revenue_clean_showcase":
        c_msg = data.get("msgCue", "indo")
        c_prod = data.get("prodCue", "Revenue")
        c_cta = data.get("ctaCue", "Saiba")
        return f"""
        <svg class="prop-svg" viewBox="0 0 500 420" width="500" height="420">
          <defs>
            <linearGradient id="rc-bottle-body" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#FDF8F5"/>
              <stop offset="32%" stop-color="#FFFFFF"/>
              <stop offset="75%" stop-color="#F1E5DF"/>
              <stop offset="100%" stop-color="#DCC7BE"/>
            </linearGradient>
            <linearGradient id="rc-rosegold" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#C88B7A"/>
              <stop offset="35%" stop-color="#F5D0C5"/>
              <stop offset="70%" stop-color="#B97867"/>
              <stop offset="100%" stop-color="#8C5345"/>
            </linearGradient>
            <linearGradient id="rc-label" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stop-color="#1A1D28"/>
              <stop offset="100%" stop-color="#0E1017"/>
            </linearGradient>
          </defs>

          <!-- Mini chat "to indo!" no topo esquerdo -->
          <g {_cue_attrs(1, c_msg, 'slide-left', 'notification', 0.14)} style="transform-origin: 146px 68px;">
            <rect x="24" y="34" width="236" height="58" rx="18" fill="#14161D" stroke="#FFFFFF" stroke-width="3.5"/>
            <circle cx="54" cy="63" r="14" fill="#D0EB2F"/>
            <path d="M48 63 L52 67 L61 58" fill="none" stroke="#14161D" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
            <text x="80" y="69" fill="#FFFFFF" font-family="Sora, sans-serif" font-weight="800" font-size="19">tô indo! 💚</text>
          </g>

          <!-- Embalagem 2.5D Premium Revenue Clean -->
          <g {_cue_attrs(2, c_prod, 'pop-overshoot', 'sparkle', 0.42)} style="transform-origin: 280px 230px;">
            <!-- Glow radial suave atras do frasco -->
            <circle cx="280" cy="236" r="134" fill="rgba(255,255,255,0.42)"/>
            <!-- Sombra na base -->
            <ellipse cx="280" cy="376" rx="84" ry="14" fill="rgba(0,0,0,0.22)"/>

            <!-- Caixa / Embalagem secundaria ao lado -->
            <rect x="132" y="148" width="106" height="224" rx="14" fill="#F9F4F1" stroke="#14161D" stroke-width="4.5"/>
            <rect x="144" y="164" width="82" height="192" rx="8" fill="#FFFFFF" stroke="#E5D5CE" stroke-width="2"/>
            <rect x="152" y="196" width="66" height="44" rx="8" fill="#14161D"/>
            <text x="185" y="216" text-anchor="middle" fill="#FFFFFF" font-family="Sora, sans-serif" font-weight="800" font-size="11">REVENUE</text>
            <text x="185" y="231" text-anchor="middle" fill="#D0EB2F" font-family="Sora, sans-serif" font-weight="800" font-size="12">CLEAN</text>
            <text x="185" y="268" text-anchor="middle" fill="#7C5348" font-family="Sora, sans-serif" font-weight="700" font-size="10">AROMA ÍNTIMO</text>
            <circle cx="185" cy="316" r="16" fill="#D0EB2F" stroke="#14161D" stroke-width="2.5"/>
            <path d="M179 316 L184 321 L192 311" fill="none" stroke="#14161D" stroke-width="3.5" stroke-linecap="round"/>

            <!-- Frasco Principal 2.5D -->
            <!-- Tampa Spray / Valvula Rose Gold -->
            <rect x="260" y="88" width="48" height="46" rx="10" fill="url(#rc-rosegold)" stroke="#14161D" stroke-width="4"/>
            <rect x="250" y="128" width="68" height="16" rx="6" fill="url(#rc-rosegold)" stroke="#14161D" stroke-width="4"/>
            <!-- Corpo do frasco -->
            <path d="M234 156 Q234 144 250 144 L318 144 Q334 144 334 156 L338 358 Q338 374 320 374 L248 374 Q230 374 230 358 Z" fill="url(#rc-bottle-body)" stroke="#14161D" stroke-width="5"/>
            <!-- Reflexo especular vertical -->
            <rect x="242" y="156" width="14" height="202" rx="7" fill="rgba(255,255,255,0.85)"/>
            <!-- Rotulo frontal premium -->
            <rect x="242" y="192" width="84" height="132" rx="12" fill="url(#rc-label)" stroke="#D0EB2F" stroke-width="2.5"/>
            <text x="284" y="228" text-anchor="middle" fill="#FFFFFF" font-family="Sora, sans-serif" font-weight="800" font-size="13" letter-spacing="1">REVENUE</text>
            <text x="284" y="248" text-anchor="middle" fill="#D0EB2F" font-family="Sora, sans-serif" font-weight="800" font-size="16" letter-spacing="1">CLEAN</text>
            <line x1="258" y1="262" x2="310" y2="262" stroke="rgba(255,255,255,0.28)" stroke-width="2"/>
            <text x="284" y="284" text-anchor="middle" fill="#F5D0C5" font-family="Sora, sans-serif" font-weight="700" font-size="10">AROMA ÍNTIMO</text>
            <text x="284" y="302" text-anchor="middle" fill="#9AA3B5" font-family="Sora, sans-serif" font-weight="600" font-size="9">USO DIÁRIO</text>

            <!-- Sparkles -->
            <path d="M366 130 L372 146 L388 152 L372 158 L366 174 L360 158 L344 152 L360 146 Z" fill="#FFFFFF" stroke="#14161D" stroke-width="2.5"/>
            <path d="M122 288 L126 298 L136 302 L126 306 L122 316 L118 306 L108 302 L118 298 Z" fill="#D0EB2F" stroke="#14161D" stroke-width="2"/>
          </g>

          <!-- Badge CTA pulsante -->
          <g {_cue_attrs(3, c_cta, 'pop-overshoot', 'pop', 0.72)} style="transform-origin: 368px 63px;">
            <rect x="286" y="37" width="164" height="52" rx="26" fill="#14161D" stroke="#FFFFFF" stroke-width="3.5"/>
            <text x="368" y="69" text-anchor="middle" fill="#D0EB2F" font-family="Sora, sans-serif" font-weight="800" font-size="17">Saiba mais →</text>
          </g>
        </svg>"""

    # 9) BAR CHART / BAR-CHART-CTA (default)
    bar_bg = "#252938" if theme_key == "dark" else "rgba(20, 22, 29, 0.22)"
    winner_fill = "#FFFFFF" if theme_key == "lime" else "#D0EB2F"
    bars = data.get("bars") or [
        {"h": 130, "cue_word": None},
        {"h": 166, "cue_word": None},
        {"h": 208, "cue_word": None},
        {"h": 254, "cue_word": "primeiro"},
        {"h": 316, "winner": True, "count": 23206, "cue_word": "vinte"},
    ]
    bars_svg = []
    for idx, b in enumerate(bars[:5]):
        bx = 34 + idx * 80
        bh = int(b.get("h", 140 + idx * 40))
        by = 380 - bh
        is_win = bool(b.get("winner", idx == len(bars[:5]) - 1))
        fill = winner_fill if is_win else bar_bg
        stroke_attr = ' stroke="#14161D" stroke-width="5"' if is_win else ""
        cue_w = b.get("cue_word")
        ratio = 0.14 + idx * 0.11
        sfx = "pop" if is_win else None
        count_html = ""
        if is_win and b.get("count"):
            cnt = int(b["count"])
            count_html = f'<text class="cue-count-up" data-count-target="{cnt}" data-count-prefix="" data-count-suffix="" x="{bx+38}" y="{by-16}" text-anchor="middle" fill="#14161D" font-family="Sora, sans-serif" font-weight="800" font-size="24" style="font-variant-numeric: tabular-nums;">{cnt}</text>'
        bars_svg.append(
            f"""
        <g {_cue_attrs(idx + 1, cue_w, 'grow-y', sfx, ratio)} style="transform-origin: {bx+35}px 380px;">
          <rect x="{bx}" y="{by}" width="70" height="{bh}" rx="12" fill="{fill}"{stroke_attr}/>
          {count_html}
        </g>"""
        )

    return f"""
    <svg class="prop-svg" viewBox="0 0 500 420" width="500" height="420">
      {''.join(bars_svg)}
      <g {_cue_attrs(6, data.get("ctaCue", "ranking"), 'pop-overshoot', 'click', 0.65)} style="transform-origin: 332px 298px;">
        <circle cx="332" cy="214" r="34" fill="#14161D" stroke="{winner_fill}" stroke-width="4"/>
        <path d="M272 380 C272 276 392 276 392 380 Z" fill="#14161D" stroke="{winner_fill}" stroke-width="4"/>
      </g>
    </svg>"""
