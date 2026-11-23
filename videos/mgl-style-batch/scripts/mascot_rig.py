"""Rig 2.5D articulado do mascote chibi sticker em camadas SVG/DOM animaveis.

Suporta:
- Renderizacao inline multi-camadas (.mascot-shadow, .mascot-body-rig, .mascot-torso,
  .mascot-head-rig, .mascot-brows, .mascot-eyes, .mascot-eyelids, .mascot-mouth,
  .mascot-arm-l, .mascot-arm-r, .mascot-prop)
- Acabamento 2.5D volumetrico (gradientes de pele/roupa, rim light, sombras de dobras)
- Suporte opcional a PNGs externos por pose (assets/mascot/<pose>.png) quando o usuario
  quiser substituir pelo proprio personagem.
"""
from __future__ import annotations

from pathlib import Path

POSES = [
    "confident",
    "broke",
    "peek",
    "magnify",
    "point",
    "laptop",
    "shock",
    "celebrate",
    "marina_neutral",
    "marina_clutch",
    "marina_sad",
    "marina_phone",
    "marina_coffee",
    "marina_relieved",
    "marina_confident",
]


def _marina_pose_parts(pose: str, fid: str) -> dict[str, str]:
    skin_ref = f"url(#{fid}-skin)"
    bag_ref = f"url(#{fid}-bag)"
    prop = ""
    if pose == "marina_clutch":
        brows = """
        <path d="M150 158 Q170 148 188 160" fill="none" stroke="#2B160E" stroke-width="5.5" stroke-linecap="round"/>
        <path d="M232 160 Q250 148 270 158" fill="none" stroke="#2B160E" stroke-width="5.5" stroke-linecap="round"/>"""
        eyes = """
        <ellipse cx="170" cy="192" rx="20" ry="20" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.2"/>
        <circle cx="173" cy="192" r="10.5" fill="#2A1710"/>
        <circle cx="168" cy="186" r="4" fill="#FFFFFF"/>
        <path d="M148 184 Q156 172 176 174" fill="none" stroke="#1E130D" stroke-width="4" stroke-linecap="round"/>
        <ellipse cx="250" cy="192" rx="20" ry="20" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.2"/>
        <circle cx="247" cy="192" r="10.5" fill="#2A1710"/>
        <circle cx="242" cy="186" r="4" fill="#FFFFFF"/>
        <path d="M244 174 Q264 172 272 184" fill="none" stroke="#1E130D" stroke-width="4" stroke-linecap="round"/>"""
        mouth = """
        <path d="M196 248 Q210 242 224 248" fill="none" stroke="#B85B60" stroke-width="4.5" stroke-linecap="round"/>"""
        # Arms hugging handbag tightly to chest
        arm_l = f"""
        <path d="M152 324 C124 344 134 374 176 376" fill="none" stroke="{skin_ref}" stroke-width="20" stroke-linecap="round"/>
        <circle cx="180" cy="376" r="13" fill="{skin_ref}" stroke="#1E130D" stroke-width="3"/>"""
        arm_r = f"""
        <path d="M268 324 C296 344 286 374 244 376" fill="none" stroke="{skin_ref}" stroke-width="20" stroke-linecap="round"/>
        <circle cx="240" cy="376" r="13" fill="{skin_ref}" stroke="#1E130D" stroke-width="3"/>"""
        prop = f"""
        <!-- Bolsa apertada contra o corpo -->
        <path d="M174 334 Q210 310 246 334" fill="none" stroke="#2D1B17" stroke-width="7"/>
        <rect x="164" y="348" width="92" height="66" rx="16" fill="{bag_ref}" stroke="#1E130D" stroke-width="3.5"/>
        <path d="M164 368 Q210 384 256 368" fill="none" stroke="#1E130D" stroke-width="3"/>
        <rect x="202" y="370" width="16" height="12" rx="4" fill="#E8C27A" stroke="#1E130D" stroke-width="2"/>"""
    elif pose == "marina_sad":
        brows = """
        <path d="M150 164 Q170 158 188 166" fill="none" stroke="#2B160E" stroke-width="5.2" stroke-linecap="round"/>
        <path d="M232 166 Q250 158 270 164" fill="none" stroke="#2B160E" stroke-width="5.2" stroke-linecap="round"/>"""
        eyes = """
        <ellipse cx="170" cy="195" rx="18" ry="15" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.2"/>
        <circle cx="170" cy="198" r="10" fill="#2A1710"/>
        <circle cx="166" cy="194" r="3.5" fill="#FFFFFF"/>
        <path d="M150 185 Q170 178 188 186" fill="none" stroke="#1E130D" stroke-width="4" stroke-linecap="round"/>
        <ellipse cx="250" cy="195" rx="18" ry="15" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.2"/>
        <circle cx="250" cy="198" r="10" fill="#2A1710"/>
        <circle cx="246" cy="194" r="3.5" fill="#FFFFFF"/>
        <path d="M232 186 Q250 178 270 185" fill="none" stroke="#1E130D" stroke-width="4" stroke-linecap="round"/>"""
        mouth = """
        <path d="M196 250 Q210 242 224 250" fill="none" stroke="#B85B60" stroke-width="4.2" stroke-linecap="round"/>"""
        arm_l = f"""
        <path d="M152 324 C132 356 134 388 156 404" fill="none" stroke="{skin_ref}" stroke-width="20" stroke-linecap="round"/>
        <circle cx="160" cy="406" r="13" fill="{skin_ref}" stroke="#1E130D" stroke-width="3"/>"""
        arm_r = f"""
        <path d="M268 324 C288 356 286 388 264 404" fill="none" stroke="{skin_ref}" stroke-width="20" stroke-linecap="round"/>
        <circle cx="260" cy="406" r="13" fill="{skin_ref}" stroke="#1E130D" stroke-width="3"/>"""
    elif pose == "marina_phone":
        brows = """
        <path d="M150 162 Q170 154 188 162" fill="none" stroke="#2B160E" stroke-width="5.2" stroke-linecap="round"/>
        <path d="M232 162 Q250 154 270 162" fill="none" stroke="#2B160E" stroke-width="5.2" stroke-linecap="round"/>"""
        eyes = """
        <ellipse cx="170" cy="194" rx="18" ry="16" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.2"/>
        <circle cx="166" cy="196" r="10" fill="#2A1710"/>
        <circle cx="162" cy="192" r="3.5" fill="#FFFFFF"/>
        <path d="M150 184 Q170 176 188 184" fill="none" stroke="#1E130D" stroke-width="4" stroke-linecap="round"/>
        <ellipse cx="250" cy="194" rx="18" ry="16" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.2"/>
        <circle cx="246" cy="196" r="10" fill="#2A1710"/>
        <circle cx="242" cy="192" r="3.5" fill="#FFFFFF"/>
        <path d="M232 184 Q250 176 270 184" fill="none" stroke="#1E130D" stroke-width="4" stroke-linecap="round"/>"""
        mouth = """
        <path d="M196 247 Q210 245 224 247" fill="none" stroke="#B85B60" stroke-width="4.2" stroke-linecap="round"/>"""
        arm_l = f"""
        <path d="M152 324 C126 352 132 374 166 370" fill="none" stroke="{skin_ref}" stroke-width="20" stroke-linecap="round"/>
        <circle cx="170" cy="368" r="13" fill="{skin_ref}" stroke="#1E130D" stroke-width="3"/>"""
        arm_r = f"""
        <path d="M268 324 C290 354 276 382 232 374" fill="none" stroke="{skin_ref}" stroke-width="20" stroke-linecap="round"/>
        <circle cx="228" cy="374" r="13" fill="{skin_ref}" stroke="#1E130D" stroke-width="3"/>"""
        prop = """
        <rect x="176" y="334" width="48" height="72" rx="10" fill="#181B24" stroke="#0E0F14" stroke-width="3.5" transform="rotate(-10 200 370)"/>
        <rect x="182" y="342" width="36" height="54" rx="6" fill="#E9EEF6" transform="rotate(-10 200 370)"/>"""
    elif pose == "marina_coffee":
        brows = """
        <path d="M150 160 Q170 150 188 162" fill="none" stroke="#2B160E" stroke-width="5.2" stroke-linecap="round"/>
        <path d="M232 162 Q250 150 270 160" fill="none" stroke="#2B160E" stroke-width="5.2" stroke-linecap="round"/>"""
        eyes = """
        <ellipse cx="170" cy="193" rx="18" ry="17" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.2"/>
        <circle cx="168" cy="194" r="10.5" fill="#2A1710"/>
        <circle cx="164" cy="189" r="3.6" fill="#FFFFFF"/>
        <path d="M150 182 Q170 174 188 182" fill="none" stroke="#1E130D" stroke-width="4" stroke-linecap="round"/>
        <ellipse cx="250" cy="193" rx="18" ry="17" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.2"/>
        <circle cx="248" cy="194" r="10.5" fill="#2A1710"/>
        <circle cx="244" cy="189" r="3.6" fill="#FFFFFF"/>
        <path d="M232 182 Q250 174 270 182" fill="none" stroke="#1E130D" stroke-width="4" stroke-linecap="round"/>"""
        mouth = """
        <ellipse cx="210" cy="248" rx="11" ry="8" fill="#8C363C" stroke="#1E130D" stroke-width="2.5"/>"""
        arm_l = f"""
        <path d="M152 324 C122 348 128 378 168 374" fill="none" stroke="{skin_ref}" stroke-width="20" stroke-linecap="round"/>
        <circle cx="172" cy="374" r="13" fill="{skin_ref}" stroke="#1E130D" stroke-width="3"/>"""
        arm_r = f"""
        <path d="M268 324 C294 348 288 378 248 374" fill="none" stroke="{skin_ref}" stroke-width="20" stroke-linecap="round"/>
        <circle cx="244" cy="374" r="13" fill="{skin_ref}" stroke="#1E130D" stroke-width="3"/>"""
        prop = """
        <!-- Xicara de cafe frio -->
        <path d="M184 352 L236 352 L230 392 Q210 398 190 392 Z" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5" stroke-linejoin="round"/>
        <path d="M235 358 Q252 358 252 372 Q252 384 233 384" fill="none" stroke="#1E130D" stroke-width="4" stroke-linecap="round"/>
        <ellipse cx="210" cy="352" rx="26" ry="7" fill="#4A2E20" stroke="#1E130D" stroke-width="3"/>"""
    elif pose == "marina_relieved":
        brows = """
        <path d="M150 158 Q170 148 188 158" fill="none" stroke="#2B160E" stroke-width="5.2" stroke-linecap="round"/>
        <path d="M232 158 Q250 148 270 158" fill="none" stroke="#2B160E" stroke-width="5.2" stroke-linecap="round"/>"""
        eyes = """
        <ellipse cx="170" cy="193" rx="18" ry="17" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.2"/>
        <circle cx="171" cy="193" r="10.5" fill="#2A1710"/>
        <circle cx="166" cy="188" r="3.8" fill="#FFFFFF"/>
        <path d="M150 182 Q170 173 188 182" fill="none" stroke="#1E130D" stroke-width="4" stroke-linecap="round"/>
        <ellipse cx="250" cy="193" rx="18" ry="17" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.2"/>
        <circle cx="249" cy="193" r="10.5" fill="#2A1710"/>
        <circle cx="244" cy="188" r="3.8" fill="#FFFFFF"/>
        <path d="M232 182 Q250 173 270 182" fill="none" stroke="#1E130D" stroke-width="4" stroke-linecap="round"/>"""
        mouth = """
        <path d="M190 245 Q210 262 230 245" fill="none" stroke="#C85D68" stroke-width="4.5" stroke-linecap="round"/>"""
        arm_l = f"""
        <path d="M152 324 C122 346 116 376 132 396" fill="none" stroke="{skin_ref}" stroke-width="20" stroke-linecap="round"/>
        <circle cx="134" cy="400" r="13" fill="{skin_ref}" stroke="#1E130D" stroke-width="3"/>"""
        arm_r = f"""
        <path d="M268 324 C296 348 292 380 272 396" fill="none" stroke="{skin_ref}" stroke-width="20" stroke-linecap="round"/>
        <circle cx="268" cy="400" r="13" fill="{skin_ref}" stroke="#1E130D" stroke-width="3"/>"""
    elif pose == "marina_confident":
        brows = """
        <path d="M150 156 Q170 144 188 156" fill="none" stroke="#2B160E" stroke-width="5.5" stroke-linecap="round"/>
        <path d="M232 156 Q250 144 270 156" fill="none" stroke="#2B160E" stroke-width="5.5" stroke-linecap="round"/>"""
        eyes = """
        <ellipse cx="170" cy="192" rx="19" ry="18" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.2"/>
        <circle cx="171" cy="192" r="11" fill="#2A1710"/>
        <circle cx="166" cy="186" r="4" fill="#FFFFFF"/>
        <path d="M148 180 Q170 170 190 180" fill="none" stroke="#1E130D" stroke-width="4.2" stroke-linecap="round"/>
        <ellipse cx="250" cy="192" rx="19" ry="18" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.2"/>
        <circle cx="249" cy="192" r="11" fill="#2A1710"/>
        <circle cx="244" cy="186" r="4" fill="#FFFFFF"/>
        <path d="M230 180 Q250 170 272 180" fill="none" stroke="#1E130D" stroke-width="4.2" stroke-linecap="round"/>"""
        mouth = """
        <path d="M188 243 Q210 268 232 243 Z" fill="#FFFFFF" stroke="#B8525D" stroke-width="3.5" stroke-linejoin="round"/>"""
        arm_l = f"""
        <path d="M152 324 C112 318 100 282 108 248" fill="none" stroke="{skin_ref}" stroke-width="20" stroke-linecap="round"/>
        <circle cx="110" cy="242" r="14" fill="{skin_ref}" stroke="#1E130D" stroke-width="3"/>"""
        arm_r = f"""
        <path d="M268 324 C306 336 318 312 318 282" fill="none" stroke="{skin_ref}" stroke-width="20" stroke-linecap="round"/>
        <circle cx="318" cy="276" r="14" fill="{skin_ref}" stroke="#1E130D" stroke-width="3"/>"""
    else:  # marina_neutral
        brows = """
        <path d="M150 158 Q170 148 188 158" fill="none" stroke="#2B160E" stroke-width="5.2" stroke-linecap="round"/>
        <path d="M232 158 Q250 148 270 158" fill="none" stroke="#2B160E" stroke-width="5.2" stroke-linecap="round"/>"""
        eyes = """
        <ellipse cx="170" cy="193" rx="18" ry="17" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.2"/>
        <circle cx="171" cy="193" r="10.5" fill="#2A1710"/>
        <circle cx="166" cy="188" r="3.8" fill="#FFFFFF"/>
        <path d="M150 182 Q170 173 188 182" fill="none" stroke="#1E130D" stroke-width="4" stroke-linecap="round"/>
        <ellipse cx="250" cy="193" rx="18" ry="17" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.2"/>
        <circle cx="249" cy="193" r="10.5" fill="#2A1710"/>
        <circle cx="244" cy="188" r="3.8" fill="#FFFFFF"/>
        <path d="M232 182 Q250 173 270 182" fill="none" stroke="#1E130D" stroke-width="4" stroke-linecap="round"/>"""
        mouth = """
        <path d="M194 247 Q210 256 226 247" fill="none" stroke="#C85D68" stroke-width="4.2" stroke-linecap="round"/>"""
        arm_l = f"""
        <path d="M152 324 C128 348 122 374 134 398" fill="none" stroke="{skin_ref}" stroke-width="20" stroke-linecap="round"/>
        <circle cx="136" cy="402" r="13" fill="{skin_ref}" stroke="#1E130D" stroke-width="3"/>"""
        arm_r = f"""
        <path d="M268 324 C294 348 298 378 286 400" fill="none" stroke="{skin_ref}" stroke-width="20" stroke-linecap="round"/>
        <circle cx="284" cy="404" r="13" fill="{skin_ref}" stroke="#1E130D" stroke-width="3"/>"""
        prop = f"""
        <!-- Bolsa no ombro esquerdo -->
        <line x1="158" y1="300" x2="128" y2="394" stroke="#2D1B17" stroke-width="6"/>
        <rect x="92" y="388" width="64" height="54" rx="14" fill="{bag_ref}" stroke="#1E130D" stroke-width="3.5"/>"""

    return {
        "brows": brows,
        "eyes": eyes,
        "mouth": mouth,
        "arm_l": arm_l,
        "arm_r": arm_r,
        "prop": prop,
    }


def _render_marina_rig(pose: str, uid: str) -> str:
    fid = f"st-{uid}"
    parts = _marina_pose_parts(pose, fid)
    return f"""
    <div class="mascot-pose-slot" data-pose="{pose}">
      <svg class="mascot-svg" viewBox="0 0 420 580" width="420" height="580">
        <defs>
          <linearGradient id="{fid}-skin" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#FAD0B4"/>
            <stop offset="70%" stop-color="#F2B892"/>
            <stop offset="100%" stop-color="#E29E74"/>
          </linearGradient>
          <linearGradient id="{fid}-blouse" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#FFFFFF"/>
            <stop offset="70%" stop-color="#F1ECE6"/>
            <stop offset="100%" stop-color="#DED5CB"/>
          </linearGradient>
          <linearGradient id="{fid}-hair" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#4A2B1D"/>
            <stop offset="100%" stop-color="#27140B"/>
          </linearGradient>
          <linearGradient id="{fid}-bag" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#5B382E"/>
            <stop offset="100%" stop-color="#351E18"/>
          </linearGradient>
          <filter id="{fid}-outline" x="-22%" y="-22%" width="144%" height="144%">
            <feMorphology in="SourceAlpha" result="DILATED" operator="dilate" radius="10"/>
            <feFlood flood-color="#FFFFFF" flood-opacity="1" result="WHITE"/>
            <feComposite in="WHITE" in2="DILATED" operator="in" result="OUTLINE"/>
            <feDropShadow dx="0" dy="12" stdDeviation="9" flood-color="#000000" flood-opacity="0.28" result="SHADOW"/>
            <feMerge>
              <feMergeNode in="SHADOW"/>
              <feMergeNode in="OUTLINE"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        <ellipse class="mascot-shadow" cx="210" cy="548" rx="108" ry="15" fill="rgba(0,0,0,0.22)"/>

        <g class="mascot-body-rig" filter="url(#{fid}-outline)" style="transform-origin: 210px 526px;">
          <!-- Camada traseira do cabelo longo ondulado -->
          <path d="M96 144 C76 226 84 318 112 368 Q154 348 164 316 L256 316 Q266 348 308 368 C336 318 344 226 324 144 Z" fill="url(#{fid}-hair)" stroke="#1C0E08" stroke-width="4" stroke-linejoin="round"/>

          <!-- Calca elegante + Tenis branco -->
          <path d="M158 386 L262 386 L270 492 L222 492 L210 434 L198 492 L150 492 Z" fill="#1F222C" stroke="#0E0F14" stroke-width="3.5" stroke-linejoin="round"/>
          <path d="M144 508 Q144 490 166 488 L196 490 Q204 498 202 516 L146 516 Z" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
          <rect x="142" y="512" width="62" height="12" rx="6" fill="#F2F3F7" stroke="#1E130D" stroke-width="3.2"/>
          <path d="M218 516 Q216 498 224 490 L254 488 Q276 490 276 508 L274 516 Z" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
          <rect x="216" y="512" width="62" height="12" rx="6" fill="#F2F3F7" stroke="#1E130D" stroke-width="3.2"/>

          <!-- Bracos articulados -->
          <g class="mascot-arm-l" style="transform-origin: 152px 324px;">
            {parts["arm_l"]}
          </g>
          <g class="mascot-arm-r" style="transform-origin: 268px 324px;">
            {parts["arm_r"]}
          </g>

          <!-- Blusa elegante -->
          <g class="mascot-torso" style="transform-origin: 210px 388px;">
            <path d="M152 298 Q210 288 268 298 L286 340 L264 350 L264 392 L156 392 L156 350 L134 340 Z" fill="url(#{fid}-blouse)" stroke="#1E130D" stroke-width="3.5" stroke-linejoin="round"/>
            <path d="M186 298 Q210 322 234 298" fill="none" stroke="#CBBFB2" stroke-width="3.5"/>
          </g>

          <!-- Cabeca Articulada -->
          <g class="mascot-head-rig" style="transform-origin: 210px 282px;">
            <rect x="194" y="270" width="32" height="32" rx="10" fill="#E8AC84" stroke="#1E130D" stroke-width="3"/>
            <ellipse cx="108" cy="196" rx="15" ry="22" fill="#EDAF86" stroke="#1E130D" stroke-width="3.2"/>
            <ellipse cx="312" cy="196" rx="15" ry="22" fill="#EDAF86" stroke="#1E130D" stroke-width="3.2"/>
            <!-- Brincos discretos -->
            <circle cx="108" cy="214" r="5" fill="#F4D392" stroke="#1E130D" stroke-width="2"/>
            <circle cx="312" cy="214" r="5" fill="#F4D392" stroke="#1E130D" stroke-width="2"/>

            <path d="M114 162 C114 96 306 96 306 162 C306 230 282 276 210 276 C138 276 114 230 114 162 Z" fill="url(#{fid}-skin)" stroke="#1E130D" stroke-width="3.8"/>
            <ellipse cx="148" cy="216" rx="18" ry="9" fill="#F08A82" opacity="0.28"/>
            <ellipse cx="272" cy="216" rx="18" ry="9" fill="#F08A82" opacity="0.28"/>

            <!-- Franja + Topo cabelo feminino -->
            <path d="M104 186 C98 100 138 52 210 52 C282 52 322 100 316 186 C306 144 282 114 238 118 C218 122 204 110 184 114 C144 122 116 146 104 186 Z" fill="url(#{fid}-hair)" stroke="#1C0E08" stroke-width="4" stroke-linejoin="round"/>
            <path d="M148 80 Q180 64 214 74 M228 74 Q260 66 282 88" fill="none" stroke="#6E4431" stroke-width="4.5" stroke-linecap="round"/>

            <path d="M204 206 Q210 220 217 212" fill="none" stroke="#D1885B" stroke-width="3.6" stroke-linecap="round"/>

            <g class="mascot-brows" style="transform-origin: 210px 158px;">
              {parts["brows"]}
            </g>
            <g class="mascot-eyes" style="transform-origin: 210px 193px;">
              {parts["eyes"]}
              <g class="mascot-eyelids" opacity="0">
                <path d="M150 193 Q170 202 190 193" fill="none" stroke="#1E130D" stroke-width="4.8" stroke-linecap="round"/>
                <path d="M230 193 Q250 202 270 193" fill="none" stroke="#1E130D" stroke-width="4.8" stroke-linecap="round"/>
              </g>
            </g>
            <g class="mascot-mouth" style="transform-origin: 210px 248px;">
              {parts["mouth"]}
            </g>
          </g>

          <!-- Prop na mao (bolsa / celular / xicara) -->
          <g class="mascot-prop" style="transform-origin: 210px 368px;">
            {parts["prop"]}
          </g>
        </g>
      </svg>
    </div>"""


def _pose_parts(pose: str, fid: str) -> dict[str, str]:
    skin_ref = f"url(#{fid}-skin)"
    if pose == "broke":
        brows = """
        <path d="M148 166 Q168 158 186 167" fill="none" stroke="#1E130D" stroke-width="6.5" stroke-linecap="round"/>
        <path d="M234 167 Q252 158 272 166" fill="none" stroke="#1E130D" stroke-width="6.5" stroke-linecap="round"/>"""
        eyes = """
        <ellipse cx="170" cy="193" rx="18" ry="17" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
        <circle cx="174" cy="191" r="10.5" fill="#23140E"/>
        <circle cx="170" cy="186" r="4" fill="#FFFFFF"/>
        <ellipse cx="250" cy="193" rx="18" ry="17" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
        <circle cx="246" cy="191" r="10.5" fill="#23140E"/>
        <circle cx="242" cy="186" r="4" fill="#FFFFFF"/>"""
        mouth = """
        <path d="M188 248 Q210 242 232 248 Q228 261 210 261 Q192 261 188 248 Z" fill="#FFFFFF" stroke="#1E130D" stroke-width="3"/>
        <line x1="192" y1="253" x2="228" y2="253" stroke="#D2D4DC" stroke-width="1.5"/>"""
        arm_l = """
        <path d="M150 404 L126 420 L144 432 Z" fill="#F2F3F5" stroke="#1B1C22" stroke-width="3.5" stroke-linejoin="round"/>
        <path d="M148 326 C122 346 112 378 122 406" fill="none" stroke="url(#skinGrad)" stroke-width="24" stroke-linecap="round"/>
        <circle cx="122" cy="412" r="15" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>"""
        arm_r = """
        <path d="M270 404 L294 420 L276 432 Z" fill="#F2F3F5" stroke="#1B1C22" stroke-width="3.5" stroke-linejoin="round"/>
        <path d="M272 326 C298 346 308 378 298 406" fill="none" stroke="url(#skinGrad)" stroke-width="24" stroke-linecap="round"/>
        <circle cx="298" cy="412" r="15" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>
        <circle cx="295" cy="396" r="9" fill="#2A2D36" stroke="#111" stroke-width="2"/>"""
        prop = ""
    elif pose == "peek":
        brows = """
        <path d="M146 164 Q168 152 188 162" fill="none" stroke="#1E130D" stroke-width="7" stroke-linecap="round"/>
        <path d="M234 162 Q254 152 276 164" fill="none" stroke="#1E130D" stroke-width="7" stroke-linecap="round"/>"""
        eyes = """
        <ellipse cx="170" cy="194" rx="17" ry="16" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
        <circle cx="170" cy="194" r="10" fill="#23140E"/>
        <circle cx="166" cy="189" r="3.6" fill="#FFFFFF"/>
        <ellipse cx="250" cy="194" rx="17" ry="16" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
        <circle cx="248" cy="194" r="10" fill="#23140E"/>
        <circle cx="244" cy="189" r="3.6" fill="#FFFFFF"/>"""
        mouth = """
        <ellipse cx="210" cy="252" rx="14" ry="10" fill="#5E1D1B" stroke="#1E130D" stroke-width="3"/>
        <path d="M201 247 Q210 245 219 247" stroke="#FFFFFF" stroke-width="3" fill="none" stroke-linecap="round"/>"""
        arm_l = """
        <path d="M148 326 C126 350 112 356 100 342" fill="none" stroke="url(#skinGrad)" stroke-width="24" stroke-linecap="round"/>
        <circle cx="96" cy="336" r="16" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>"""
        arm_r = """
        <path d="M272 326 C312 308 322 238 292 178" fill="none" stroke="url(#skinGrad)" stroke-width="23" stroke-linecap="round"/>
        <circle cx="290" cy="172" r="16" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>
        <circle cx="305" cy="242" r="9" fill="#2A2D36" stroke="#111" stroke-width="2"/>"""
        prop = """
        <path d="M104 176 Q178 195 294 152 L298 176 Q182 222 102 204 Z" fill="#1F222A" stroke="#0E0F14" stroke-width="3.5"/>
        <path d="M104 198 L92 226 L112 222 Z" fill="#1F222A" stroke="#0E0F14" stroke-width="3"/>"""
    elif pose == "magnify":
        brows = """
        <path d="M146 158 Q170 144 190 158" fill="none" stroke="#1E130D" stroke-width="7.5" stroke-linecap="round"/>
        <path d="M234 170 Q254 162 276 170" fill="none" stroke="#1E130D" stroke-width="7" stroke-linecap="round"/>"""
        eyes = """
        <ellipse cx="170" cy="193" rx="25" ry="24" fill="#FFFFFF" stroke="#1E130D" stroke-width="4"/>
        <circle cx="172" cy="193" r="15" fill="#23140E"/>
        <circle cx="166" cy="186" r="5" fill="#FFFFFF"/>
        <path d="M232 194 Q252 183 270 194" fill="none" stroke="#1E130D" stroke-width="5.5" stroke-linecap="round"/>"""
        mouth = """
        <path d="M196 250 Q210 246 224 250" fill="none" stroke="#1E130D" stroke-width="4.5" stroke-linecap="round"/>"""
        arm_l = """
        <path d="M148 328 C118 332 114 294 134 260" fill="none" stroke="url(#skinGrad)" stroke-width="23" stroke-linecap="round"/>
        <circle cx="134" cy="264" r="15" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>"""
        arm_r = """
        <path d="M272 328 C298 354 300 392 276 418" fill="none" stroke="url(#skinGrad)" stroke-width="23" stroke-linecap="round"/>
        <circle cx="274" cy="422" r="15" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>
        <circle cx="290" cy="378" r="9" fill="#2A2D36" stroke="#111" stroke-width="2"/>"""
        prop = """
        <line x1="138" y1="262" x2="152" y2="232" stroke="#2D313C" stroke-width="11" stroke-linecap="round"/>
        <circle cx="170" cy="193" r="44" fill="rgba(220,242,255,0.22)" stroke="#2D313C" stroke-width="8"/>
        <circle cx="170" cy="193" r="39" fill="none" stroke="#B6C0D4" stroke-width="2.5"/>
        <path d="M146 172 Q156 160 172 160" fill="none" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round" opacity="0.85"/>"""
    elif pose == "point":
        brows = """
        <path d="M146 164 Q168 154 188 164" fill="none" stroke="#1E130D" stroke-width="7.5" stroke-linecap="round"/>
        <path d="M234 156 Q254 146 276 158" fill="none" stroke="#1E130D" stroke-width="7.5" stroke-linecap="round"/>"""
        eyes = """
        <ellipse cx="170" cy="193" rx="18" ry="17" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
        <circle cx="172" cy="193" r="11" fill="#23140E"/>
        <circle cx="167" cy="188" r="4" fill="#FFFFFF"/>
        <ellipse cx="250" cy="193" rx="18" ry="17" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
        <circle cx="248" cy="193" r="11" fill="#23140E"/>
        <circle cx="243" cy="188" r="4" fill="#FFFFFF"/>"""
        mouth = """
        <path d="M194 249 Q210 261 226 249" fill="none" stroke="#1E130D" stroke-width="4.5" stroke-linecap="round"/>"""
        arm_l = """
        <path d="M148 326 C112 330 96 290 100 250" fill="none" stroke="url(#skinGrad)" stroke-width="23" stroke-linecap="round"/>
        <rect x="93" y="206" width="14" height="36" rx="7" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>
        <circle cx="102" cy="248" r="16" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>"""
        arm_r = """
        <path d="M272 326 C296 352 298 386 284 410" fill="none" stroke="url(#skinGrad)" stroke-width="23" stroke-linecap="round"/>
        <circle cx="284" cy="414" r="15" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>
        <circle cx="291" cy="382" r="9" fill="#2A2D36" stroke="#111" stroke-width="2"/>"""
        prop = ""
    elif pose == "laptop":
        brows = """
        <path d="M146 158 Q168 148 188 158" fill="none" stroke="#1E130D" stroke-width="7.5" stroke-linecap="round"/>
        <path d="M234 158 Q254 148 276 158" fill="none" stroke="#1E130D" stroke-width="7.5" stroke-linecap="round"/>"""
        eyes = """
        <ellipse cx="170" cy="192" rx="19" ry="18" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
        <circle cx="171" cy="193" r="11" fill="#23140E"/>
        <circle cx="166" cy="187" r="4" fill="#FFFFFF"/>
        <ellipse cx="250" cy="192" rx="19" ry="18" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
        <circle cx="249" cy="193" r="11" fill="#23140E"/>
        <circle cx="244" cy="187" r="4" fill="#FFFFFF"/>"""
        mouth = """
        <path d="M190 245 Q210 272 230 245 Z" fill="#5E1D1B" stroke="#1E130D" stroke-width="3.5"/>
        <path d="M195 246 Q210 250 225 246" stroke="#FFFFFF" stroke-width="4" fill="none" stroke-linecap="round"/>"""
        arm_l = """
        <path d="M148 328 C126 346 132 374 158 378" fill="none" stroke="url(#skinGrad)" stroke-width="22" stroke-linecap="round"/>
        <circle cx="164" cy="378" r="15" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>"""
        arm_r = """
        <path d="M272 326 C318 292 326 202 284 152" fill="none" stroke="url(#skinGrad)" stroke-width="22" stroke-linecap="round"/>
        <circle cx="280" cy="148" r="16" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>
        <circle cx="308" cy="230" r="9" fill="#2A2D36" stroke="#111" stroke-width="2"/>"""
        prop = """
        <polygon points="140,350 280,350 270,418 150,418" fill="#2B2E38" stroke="#11131A" stroke-width="4" stroke-linejoin="round"/>
        <circle cx="210" cy="384" r="7" fill="#D0EB2F"/>"""
    elif pose in ("shock", "celebrate"):
        brows = """
        <path d="M146 154 Q168 140 188 154" fill="none" stroke="#1E130D" stroke-width="7.5" stroke-linecap="round"/>
        <path d="M234 154 Q254 140 276 154" fill="none" stroke="#1E130D" stroke-width="7.5" stroke-linecap="round"/>"""
        eyes = """
        <ellipse cx="170" cy="190" rx="22" ry="22" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
        <circle cx="171" cy="190" r="12" fill="#23140E"/>
        <circle cx="166" cy="184" r="4.2" fill="#FFFFFF"/>
        <ellipse cx="250" cy="190" rx="22" ry="22" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
        <circle cx="249" cy="190" r="12" fill="#23140E"/>
        <circle cx="244" cy="184" r="4.2" fill="#FFFFFF"/>"""
        mouth = """
        <ellipse cx="210" cy="255" rx="16" ry="15" fill="#5E1D1B" stroke="#1E130D" stroke-width="3.5"/>
        <path d="M199 246 Q210 249 221 246" stroke="#FFFFFF" stroke-width="3.5" fill="none" stroke-linecap="round"/>
        <ellipse cx="210" cy="263" rx="9" ry="5" fill="#E06D6D"/>"""
        if pose == "celebrate":
            arm_l = """
            <path d="M148 326 C106 300 94 242 108 200" fill="none" stroke="url(#skinGrad)" stroke-width="22" stroke-linecap="round"/>
            <circle cx="110" cy="194" r="17" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>"""
            arm_r = """
            <path d="M272 326 C314 300 326 242 312 200" fill="none" stroke="url(#skinGrad)" stroke-width="22" stroke-linecap="round"/>
            <circle cx="310" cy="194" r="17" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>
            <circle cx="316" cy="258" r="9" fill="#2A2D36" stroke="#111" stroke-width="2"/>"""
        else:
            arm_l = """
            <path d="M148 328 C114 316 112 270 132 246" fill="none" stroke="url(#skinGrad)" stroke-width="22" stroke-linecap="round"/>
            <circle cx="134" cy="242" r="17" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>"""
            arm_r = """
            <path d="M272 328 C306 316 308 270 288 246" fill="none" stroke="url(#skinGrad)" stroke-width="22" stroke-linecap="round"/>
            <circle cx="286" cy="242" r="17" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>
            <circle cx="294" cy="278" r="9" fill="#2A2D36" stroke="#111" stroke-width="2"/>"""
        prop = ""
    else:  # confident
        brows = """
        <path d="M148 162 Q168 154 188 164" fill="none" stroke="#1E130D" stroke-width="7.5" stroke-linecap="round"/>
        <path d="M234 164 Q254 154 274 162" fill="none" stroke="#1E130D" stroke-width="7.5" stroke-linecap="round"/>"""
        eyes = """
        <ellipse cx="170" cy="193" rx="18" ry="17" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
        <circle cx="172" cy="193" r="10.5" fill="#23140E"/>
        <circle cx="167" cy="188" r="4" fill="#FFFFFF"/>
        <ellipse cx="250" cy="193" rx="18" ry="17" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
        <circle cx="248" cy="193" r="10.5" fill="#23140E"/>
        <circle cx="243" cy="188" r="4" fill="#FFFFFF"/>"""
        mouth = """
        <path d="M192 248 Q210 264 228 248" fill="none" stroke="#1E130D" stroke-width="4.5" stroke-linecap="round"/>"""
        arm_l = """
        <path d="M148 326 C122 350 116 376 130 398" fill="none" stroke="url(#skinGrad)" stroke-width="23" stroke-linecap="round"/>
        <circle cx="132" cy="402" r="15" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>"""
        arm_r = """
        <path d="M272 326 C302 346 318 332 326 306" fill="none" stroke="url(#skinGrad)" stroke-width="23" stroke-linecap="round"/>
        <circle cx="328" cy="300" r="16" fill="url(#skinGrad)" stroke="#1E130D" stroke-width="3"/>
        <circle cx="312" cy="332" r="9" fill="#2A2D36" stroke="#111" stroke-width="2"/>"""
        prop = ""

    return {
        k: v.replace("url(#skinGrad)", skin_ref)
        for k, v in {
            "brows": brows,
            "eyes": eyes,
            "mouth": mouth,
            "arm_l": arm_l,
            "arm_r": arm_r,
            "prop": prop,
        }.items()
    }


def render_inline_mascot_rig(pose: str, uid: str, assets_dir: Path | None = None, path_prefix: str = "") -> str:
    """Retorna HTML do mascote articulado 2.5D (ou PNG sticker caso exista <pose>.png)."""
    if assets_dir is not None:
        png_path = assets_dir / "mascot" / f"{pose}.png"
        if png_path.exists():
            return f"""
            <div class="mascot-pose-slot" data-pose="{pose}">
              <div class="mascot-shadow"></div>
              <div class="mascot-body-rig">
                <img class="mascot-png-sticker" src="{path_prefix}assets/mascot/{pose}.png" alt="{pose}" />
              </div>
            </div>"""

    if pose.startswith("marina_"):
        return _render_marina_rig(pose, uid)

    parts = _pose_parts(pose, f"st-{uid}")
    fid = f"st-{uid}"
    return f"""
    <div class="mascot-pose-slot" data-pose="{pose}">
      <svg class="mascot-svg" viewBox="0 0 420 580" width="420" height="580">
        <defs>
          <linearGradient id="{fid}-skin" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#F7BA8E"/>
            <stop offset="70%" stop-color="#EEA271"/>
            <stop offset="100%" stop-color="#DC8652"/>
          </linearGradient>
          <linearGradient id="{fid}-shirt" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#383C4A"/>
            <stop offset="65%" stop-color="#252832"/>
            <stop offset="100%" stop-color="#171920"/>
          </linearGradient>
          <linearGradient id="{fid}-hair" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#3E271C"/>
            <stop offset="100%" stop-color="#20120B"/>
          </linearGradient>
          <filter id="{fid}-outline" x="-22%" y="-22%" width="144%" height="144%">
            <feMorphology in="SourceAlpha" result="DILATED" operator="dilate" radius="10"/>
            <feFlood flood-color="#FFFFFF" flood-opacity="1" result="WHITE"/>
            <feComposite in="WHITE" in2="DILATED" operator="in" result="OUTLINE"/>
            <feDropShadow dx="0" dy="12" stdDeviation="9" flood-color="#000000" flood-opacity="0.30" result="SHADOW"/>
            <feMerge>
              <feMergeNode in="SHADOW"/>
              <feMergeNode in="OUTLINE"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        <!-- Sombra independente reativa ao squash & stretch -->
        <ellipse class="mascot-shadow" cx="210" cy="548" rx="112" ry="16" fill="rgba(0,0,0,0.24)"/>

        <g class="mascot-body-rig" filter="url(#{fid}-outline)" style="transform-origin: 210px 526px;">
          <!-- Pernas + Sombreamento joelho -->
          <rect x="164" y="424" width="28" height="72" rx="12" fill="url(#{fid}-skin)" stroke="#1E130D" stroke-width="3.5"/>
          <rect x="228" y="424" width="28" height="72" rx="12" fill="url(#{fid}-skin)" stroke="#1E130D" stroke-width="3.5"/>

          <!-- Tenis 2.5D -->
          <g>
            <path d="M142 508 Q140 486 164 484 L194 486 Q204 494 202 516 L146 516 Z" fill="#F2ECE4" stroke="#1E130D" stroke-width="3.5" stroke-linejoin="round"/>
            <rect x="142" y="512" width="62" height="14" rx="6" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
            <line x1="162" y1="494" x2="180" y2="494" stroke="#B7AEA2" stroke-width="3" stroke-linecap="round"/>

            <path d="M218 516 Q216 494 226 486 L256 484 Q280 486 278 508 L274 516 Z" fill="#F2ECE4" stroke="#1E130D" stroke-width="3.5" stroke-linejoin="round"/>
            <rect x="216" y="512" width="62" height="14" rx="6" fill="#FFFFFF" stroke="#1E130D" stroke-width="3.5"/>
            <line x1="240" y1="494" x2="258" y2="494" stroke="#B7AEA2" stroke-width="3" stroke-linecap="round"/>
          </g>

          <!-- Shorts com highlight -->
          <path d="M150 388 L270 388 L276 442 L222 442 L210 422 L198 442 L144 442 Z" fill="#1D1F27" stroke="#0E0F14" stroke-width="3.5" stroke-linejoin="round"/>

          <!-- Bracos articulados independentes -->
          <g class="mascot-arm-l" style="transform-origin: 148px 326px;">
            {parts["arm_l"]}
          </g>
          <g class="mascot-arm-r" style="transform-origin: 272px 326px;">
            {parts["arm_r"]}
          </g>

          <!-- Tronco + Rim Light -->
          <g class="mascot-torso" style="transform-origin: 210px 395px;">
            <path d="M144 302 Q210 290 276 302 L292 344 L268 354 L270 398 L150 398 L152 354 L128 344 Z" fill="url(#{fid}-shirt)" stroke="#0E0F14" stroke-width="3.5" stroke-linejoin="round"/>
            <path d="M164 316 Q210 330 256 316" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="3" stroke-linecap="round"/>
            <path d="M182 300 Q210 318 238 300" fill="none" stroke="#14161D" stroke-width="4"/>
          </g>

          <!-- Cabeca Articulada (pivote no pescoco) -->
          <g class="mascot-head-rig" style="transform-origin: 210px 286px;">
            <rect x="192" y="276" width="36" height="30" rx="10" fill="#D88858" stroke="#1E130D" stroke-width="3"/>
            <ellipse cx="106" cy="196" rx="17" ry="24" fill="#E39766" stroke="#1E130D" stroke-width="3.5"/>
            <ellipse cx="314" cy="196" rx="17" ry="24" fill="#E39766" stroke="#1E130D" stroke-width="3.5"/>

            <!-- Rosto 2.5D -->
            <path d="M112 162 C112 96 308 96 308 162 C308 232 284 282 210 282 C136 282 112 232 112 162 Z" fill="url(#{fid}-skin)" stroke="#1E130D" stroke-width="4"/>
            <!-- Rubor sutil nas bochechas -->
            <ellipse cx="148" cy="216" rx="16" ry="8" fill="#E27D60" opacity="0.24"/>
            <ellipse cx="272" cy="216" rx="16" ry="8" fill="#E27D60" opacity="0.24"/>

            <!-- Cabelo volumetrico -->
            <path d="M108 172 C100 106 132 58 210 56 C288 58 320 106 312 172 C304 142 284 122 252 124 C236 114 218 126 198 120 C172 112 148 126 128 134 C116 144 112 154 108 172 Z" fill="url(#{fid}-hair)" stroke="#160B06" stroke-width="4" stroke-linejoin="round"/>
            <path d="M150 82 Q178 68 206 78 M218 76 Q246 66 270 84" fill="none" stroke="#5A3929" stroke-width="5" stroke-linecap="round"/>

            <!-- Barba -->
            <path d="M114 196 C114 252 152 284 210 284 C268 284 306 252 306 196 C298 220 278 232 252 230 C236 226 224 222 210 222 C196 222 184 226 168 230 C142 232 122 220 114 196 Z" fill="#24150E" stroke="#160B06" stroke-width="3.5" stroke-linejoin="round"/>
            <ellipse cx="210" cy="252" rx="34" ry="18" fill="#F2AB7E"/>
            <path d="M178 236 Q210 222 242 236 Q230 246 210 242 Q190 246 178 236 Z" fill="#24150E"/>
            <path d="M204 206 Q210 222 218 212" fill="none" stroke="#C47444" stroke-width="4" stroke-linecap="round"/>

            <!-- Sobrancelhas -->
            <g class="mascot-brows" style="transform-origin: 210px 160px;">
              {parts["brows"]}
            </g>

            <!-- Olhos + Palpebras para piscada natural -->
            <g class="mascot-eyes" style="transform-origin: 210px 193px;">
              {parts["eyes"]}
              <g class="mascot-eyelids" opacity="0">
                <path d="M150 193 Q170 202 190 193" fill="none" stroke="#1E130D" stroke-width="5" stroke-linecap="round"/>
                <path d="M230 193 Q250 202 270 193" fill="none" stroke="#1E130D" stroke-width="5" stroke-linecap="round"/>
              </g>
            </g>

            <!-- Boca sincronizada com WordBoundary (lip-sync) -->
            <g class="mascot-mouth" style="transform-origin: 210px 252px;">
              {parts["mouth"]}
            </g>
          </g>

          <!-- Prop do mascote (lupa / venda / laptop) -->
          <g class="mascot-prop" style="transform-origin: 210px 260px;">
            {parts["prop"]}
          </g>
        </g>
      </svg>
    </div>"""
