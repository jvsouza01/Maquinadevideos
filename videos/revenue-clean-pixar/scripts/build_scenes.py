"""Compoe os 10 planos 3D estilo Pixar (Video-first + Image fallback) em 4 sub-composicoes HyperFrames + audio/legendas."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
AUDIO_MANIFEST = ROOT / "assets" / "audio" / "generated" / "audio_manifest.json"
COMPS_DIR = ROOT / "compositions"
CLIPS_DIR = ROOT / "assets" / "clips"
SHOTS_DIR = ROOT / "assets" / "shots"

SHOT_ASSETS: dict[str, dict[str, str]] = {
    "shot_1a": {
        "video": "shot_1a.mp4",
        "image": "shot_1a_elevator_wide.jpg",
        "alt": "Elevador comercial com Marina e colegas",
    },
    "shot_1b": {
        "video": "shot_1b.mp4",
        "image": "shot_1b_marina_bag_close.jpg",
        "alt": "Marina apertando a alca da bolsa caramelo",
    },
    "shot_2a": {
        "video": "shot_2a.mp4",
        "image": "shot_2a_office_desk.jpg",
        "alt": "Marina no escritorio fim de tarde",
    },
    "shot_2b": {
        "video": "shot_2b.mp4",
        "image": "shot_2b_phone_ots.jpg",
        "alt": "Marina olhando celular no escritorio",
    },
    "shot_2c": {
        "video": "shot_2c.mp4",
        "image": "shot_2c_empty_chair_glass.jpg",
        "alt": "Cadeira vazia atraves da divisoria de vidro",
    },
    "shot_3a": {
        "video": "shot_3a.mp4",
        "image": "shot_3a_pantry_bia_enter.jpg",
        "alt": "Copa iluminada com Marina e Bia",
    },
    "shot_3b": {
        "video": "shot_3b.mp4",
        "image": "shot_3b_marina_pantry_close.jpg",
        "alt": "Close em Marina na copa",
    },
    "shot_3c": {
        "video": "shot_3c.mp4",
        "image": "shot_3c_pantry_two_cups.jpg",
        "alt": "Marina e Bia com duas xicaras na mesa",
    },
    "shot_4a": {
        "video": "shot_4a.mp4",
        "image": "shot_4a_unboxing_coat.jpg",
        "alt": "Marina abrindo caixa de entrega com casaco nos ombros",
    },
    "shot_4b": {
        "video": "shot_4b.mp4",
        "image": "shot_4b_product_hero.jpg",
        "alt": "Marina segurando Revenue Clean",
    },
}


def render_shot_media(
    shot_id: str,
    slot_start: float,
    slot_duration: float,
    playback_rate: float = 1.0,
    track_index: int = 1,
    clips_dir: Path | None = None,
) -> tuple[str, bool]:
    """Renderiza `<video>` (Video-first) se `<shot_id>.mp4` existir, ou `<img>` fallback."""
    meta = SHOT_ASSETS[shot_id]
    cdir = clips_dir if clips_dir is not None else CLIPS_DIR
    clip_path = cdir / meta["video"]
    if clip_path.exists():
        rate_attr = f' data-playback-rate="{playback_rate}"' if abs(playback_rate - 1.0) > 1e-4 else ""
        tag = (
            f'<video id="vid-{shot_id}" class="shot-media" '
            f'src="assets/clips/{meta["video"]}" '
            f'data-start="{slot_start}" data-duration="{slot_duration}"'
            f'{rate_attr} data-track-index="{track_index}" '
            f'muted playsinline preload="auto"></video>'
        )
        return tag, True

    tag = (
        f'<img class="shot-media" src="assets/shots/{meta["image"]}" '
        f'alt="{html.escape(meta["alt"])}" />'
    )
    return tag, False


def _subcomp_shell(comp_id: str, duration: float, styles: str, body: str, script: str) -> str:
    return f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
  </head>
  <body>
    <template>
      <style>
        #root {{
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          overflow: hidden;
          font-family: "Sora", sans-serif;
          background: #0E1016;
        }}
        .shot {{
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          overflow: hidden;
        }}
        .shot-cam {{
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          transform-origin: 50% 42%;
        }}
        .shot-media {{
          width: 100%;
          height: 100%;
          object-fit: cover;
          display: block;
        }}
        .cinematic-vignette {{
          position: absolute;
          inset: 0;
          background: radial-gradient(circle at 50% 44%, rgba(0,0,0,0) 54%, rgba(8,10,15,0.48) 100%);
          pointer-events: none;
        }}
        {styles}
      </style>

      <div id="root" data-composition-id="{comp_id}" data-width="1080" data-height="1920">
        {body}
      </div>

      <script>
        (function () {{
          var tl = gsap.timeline({{ paused: true }});
          {script}
          tl.set({{}}, {{}}, {duration});
          window.__timelines["{comp_id}"] = tl;
        }})();
      </script>
    </template>
  </body>
</html>
"""


def build_scene_01(dur: float, clips_dir: Path | None = None) -> str:
    # Cena 1 (0 - 7.5s): Elevador
    # 0 - 5.4s: shot_1a (duracao origem 5.03s -> rate 0.90 => 4.86s consumidos)
    # 5.4 - 7.5s: shot_1b (duracao origem 7.93s -> rate 1.0 => 2.10s consumidos)
    m1a, v1a = render_shot_media("shot_1a", 0.0, 5.4, playback_rate=0.90, clips_dir=clips_dir)
    m1b, v1b = render_shot_media("shot_1b", 5.4, round(dur - 5.4, 3), playback_rate=1.0, clips_dir=clips_dir)

    styles = """
      .elev-door-edge-l, .elev-door-edge-r {
        position: absolute;
        top: 0;
        bottom: 0;
        width: 50.5%;
        background: linear-gradient(90deg, #323A47 0%, #586375 55%, #2D3440 100%);
        z-index: 25;
        pointer-events: none;
      }
      .elev-door-edge-l { left: 0; border-right: 5px solid #161A22; }
      .elev-door-edge-r { right: 0; border-left: 5px solid #161A22; }
      .elev-cool-glow {
        position: absolute;
        top: 0;
        left: 120px;
        right: 120px;
        height: 360px;
        background: radial-gradient(ellipse at 50% 0%, rgba(196,222,250,0.28) 0%, rgba(196,222,250,0) 75%);
        pointer-events: none;
        z-index: 12;
      }
      .filaments-layer {
        position: absolute;
        left: 390px;
        top: 1120px;
        width: 300px;
        height: 380px;
        z-index: 16;
        pointer-events: none;
        filter: blur(5px);
      }
    """

    fake_doors_html = (
        ""
        if v1a
        else """
        <!-- Portas metalicas fallback caso nao haja video -->
        <div id="s1-door-l" class="elev-door-edge-l" data-layout-ignore="true"></div>
        <div id="s1-door-r" class="elev-door-edge-r" data-layout-ignore="true"></div>
        """
    )

    body = f"""
      <div id="s1-wide" class="shot">
        <div id="s1-wide-cam" class="shot-cam">
          {m1a}
        </div>
        <div class="elev-cool-glow"></div>
        <!-- Dois filamentos cinza-esverdeados muito transparentes junto a calca de Marina -->
        <div id="s1-filaments" class="filaments-layer" data-layout-ignore="true">
          <svg viewBox="0 0 300 380" width="300" height="380">
            <path d="M122 340 C96 270 156 220 126 146 C106 96 138 56 130 22" fill="none" stroke="rgba(148, 176, 156, 0.34)" stroke-width="18" stroke-linecap="round"/>
            <path d="M178 350 C206 276 154 228 188 156 C208 112 172 70 186 30" fill="none" stroke="rgba(136, 164, 145, 0.28)" stroke-width="14" stroke-linecap="round"/>
          </svg>
        </div>
        {fake_doors_html}
        <div class="cinematic-vignette"></div>
      </div>

      <div id="s1-close" class="shot">
        <div id="s1-close-cam" class="shot-cam">
          {m1b}
        </div>
        <div class="elev-cool-glow"></div>
        <div class="cinematic-vignette"></div>
      </div>
    """

    doors_script = (
        ""
        if v1a
        else """
      tl.fromTo("#s1-door-l", { xPercent: -78 }, { xPercent: -102, duration: 0.85, ease: "power2.inOut" }, 0);
      tl.fromTo("#s1-door-r", { xPercent: 78 }, { xPercent: 102, duration: 0.85, ease: "power2.inOut" }, 0);
        """
    )

    cam_1a = (
        'tl.fromTo("#s1-wide-cam", { scale: 1.12, yPercent: 4 }, { scale: 1.15, yPercent: 3, duration: 5.4, ease: "sine.inOut" }, 0);'
        if v1a
        else 'tl.fromTo("#s1-wide-cam", { scale: 1.12, yPercent: 4 }, { scale: 1.19, yPercent: 2, duration: 5.4, ease: "sine.inOut" }, 0);'
    )
    cam_1b = (
        'tl.fromTo("#s1-close-cam", { scale: 1.0 }, { scale: 1.02, duration: 2.1, ease: "sine.out" }, 5.4);'
        if v1b
        else 'tl.fromTo("#s1-close-cam", { scale: 1.0, y: 8 }, { scale: 1.09, y: -10, duration: 2.1, ease: "power2.out" }, 5.4);'
    )

    script = f"""
      {doors_script}
      // Enquadramento acima dos joelhos
      {cam_1a}

      // Dois filamentos cinza-esverdeados sobem discretamente e se dissipam (1.0 -> 3.05s)
      tl.fromTo("#s1-filaments",
        {{ y: 42, x: 0, opacity: 0, scaleY: 0.85 }},
        {{ y: -44, x: 14, opacity: 0.85, scaleY: 1.05, duration: 1.1, ease: "sine.out" }},
        1.0
      );
      tl.to("#s1-filaments", {{ y: -115, x: 34, opacity: 0, scaleX: 1.18, duration: 0.95, ease: "sine.in" }}, 2.1);

      // Corte para Plano 1B (5.4s): close em Marina apertando a bolsa caramelo
      tl.set("#s1-close", {{ opacity: 0 }}, 0);
      tl.set("#s1-close", {{ opacity: 1 }}, 5.4);
      tl.set("#s1-wide", {{ opacity: 0 }}, 5.4);
      {cam_1b}
    """
    return _subcomp_shell("scene-01-elevator", dur, styles, body, script)


def build_scene_02(dur: float, clips_dir: Path | None = None) -> str:
    # Cena 2 (dur = 10.1s):
    # 0.0 - 3.0s: shot_2a (3.0s <= 5.03s)
    # 3.0 - 7.3s: shot_2b (4.3s <= 5.03s) + overlay de chat
    # 7.3 - 10.1s: shot_2c (2.8s <= 5.03s)
    m2a, v2a = render_shot_media("shot_2a", 0.0, 3.0, playback_rate=1.0, clips_dir=clips_dir)
    m2b, v2b = render_shot_media("shot_2b", 3.0, 4.3, playback_rate=1.0, clips_dir=clips_dir)
    m2c, v2c = render_shot_media("shot_2c", 7.3, round(dur - 7.3, 3), playback_rate=1.0, clips_dir=clips_dir)

    styles = """
      .warm-sunset-wash {
        position: absolute;
        inset: 0;
        background: linear-gradient(125deg, rgba(255,190,115,0.16) 0%, rgba(255,190,115,0) 60%);
        pointer-events: none;
        z-index: 8;
      }
      .chat-overlay-card {
        position: absolute;
        left: 72px;
        top: 1090px;
        width: 560px;
        padding: 24px 26px;
        border-radius: 26px;
        background: rgba(18, 22, 31, 0.88);
        border: 2px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 22px 48px rgba(0, 0, 0, 0.48);
        z-index: 22;
        display: flex;
        flex-direction: column;
        gap: 14px;
      }
      .chat-header {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 26px;
        font-weight: 800;
        color: #D4E6D6;
        padding-bottom: 10px;
        border-bottom: 1.5px solid rgba(255,255,255,0.12);
      }
      .chat-dot {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: #9EB8A0;
      }
      .bubble-in {
        align-self: flex-start;
        background: #FFFFFF;
        color: #14171F;
        padding: 14px 22px;
        border-radius: 18px 18px 18px 4px;
        font-size: 30px;
        font-weight: 700;
      }
      .bubble-row-out {
        position: relative;
        align-self: flex-end;
        min-height: 62px;
      }
      .bubble-draft {
        position: relative;
        background: #DCF8C6;
        color: #14171F;
        padding: 14px 24px;
        border-radius: 18px 18px 4px 18px;
        font-size: 30px;
        font-weight: 700;
      }
      .draft-strike {
        position: absolute;
        left: 16px;
        right: 16px;
        top: 50%;
        height: 5px;
        background: #EF4444;
        border-radius: 4px;
        transform-origin: left center;
      }
      .bubble-final {
        position: absolute;
        right: 0;
        top: 0;
        white-space: nowrap;
        background: #2C3446;
        color: #FFFFFF;
        border: 1.5px solid rgba(255,255,255,0.22);
        padding: 14px 24px;
        border-radius: 18px 18px 4px 18px;
        font-size: 30px;
        font-weight: 700;
      }
    """

    body = f"""
      <div id="s2-desk" class="shot">
        <div id="s2-desk-cam" class="shot-cam">
          {m2a}
        </div>
        <div class="warm-sunset-wash"></div>
        <div class="cinematic-vignette"></div>
      </div>

      <div id="s2-ots" class="shot">
        <div id="s2-ots-cam" class="shot-cam">
          {m2b}
        </div>
        <div class="warm-sunset-wash"></div>

        <!-- Overlay de edicao do chat sincronizado -->
        <div id="s2-chat-card" class="chat-overlay-card">
          <div class="chat-header">
            <span class="chat-dot"></span>
            <span>Turma do Café</span>
          </div>
          <div id="s2-b-in" class="bubble-in">Café com a gente?</div>
          <div class="bubble-row-out">
            <div id="s2-b-draft" class="bubble-draft">
              Tô indo
              <span id="s2-strike" class="draft-strike"></span>
            </div>
            <div id="s2-b-final" class="bubble-final">Hoje não consigo.</div>
          </div>
        </div>
        <div class="cinematic-vignette"></div>
      </div>

      <div id="s2-glass" class="shot">
        <div id="s2-glass-cam" class="shot-cam">
          {m2c}
        </div>
        <div class="warm-sunset-wash"></div>
        <div class="cinematic-vignette"></div>
      </div>
    """

    cam_2a = (
        'tl.set("#s2-desk-cam", { scale: 1.0 }, 0);'
        if v2a
        else 'tl.fromTo("#s2-desk-cam", { scale: 1.0, x: 10 }, { scale: 1.06, x: -12, duration: 3.0, ease: "sine.inOut" }, 0);'
    )
    cam_2b = (
        'tl.set("#s2-ots-cam", { scale: 1.0 }, 3.0);'
        if v2b
        else 'tl.fromTo("#s2-ots-cam", { scale: 1.0, y: 6 }, { scale: 1.06, y: -8, duration: 4.3, ease: "sine.inOut" }, 3.0);'
    )
    cam_2c = (
        'tl.set("#s2-glass-cam", { scale: 1.0 }, 7.3);'
        if v2c
        else 'tl.fromTo("#s2-glass-cam", { scale: 1.02, x: -10 }, { scale: 1.08, x: 8, duration: 2.8, ease: "power1.out" }, 7.3);'
    )

    script = f"""
      // Plano 2A (0 -> 3.0s)
      {cam_2a}

      // Plano 2B (3.0 -> 7.3s)
      tl.set("#s2-ots", {{ opacity: 0 }}, 0);
      tl.set("#s2-ots", {{ opacity: 1 }}, 3.0);
      tl.set("#s2-desk", {{ opacity: 0 }}, 3.0);
      {cam_2b}

      tl.fromTo("#s2-chat-card", {{ y: 24, opacity: 0, scale: 0.94 }}, {{ y: 0, opacity: 1, scale: 1, duration: 0.28, ease: "back.out(1.4)" }}, 3.08);
      tl.fromTo("#s2-b-in", {{ x: -18, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.25, ease: "power2.out" }}, 3.22);
      tl.fromTo("#s2-b-draft", {{ scale: 0.85, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.24, ease: "back.out(1.6)" }}, 4.2);
      tl.fromTo("#s2-strike", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.22, ease: "power2.out" }}, 5.05);
      tl.to("#s2-b-draft", {{ opacity: 0, scale: 0.88, duration: 0.18, ease: "power2.in" }}, 5.42);
      tl.fromTo("#s2-b-final", {{ y: 14, opacity: 0, scale: 0.9 }}, {{ y: 0, opacity: 1, scale: 1, duration: 0.28, ease: "back.out(1.5)" }}, 5.65);

      // Plano 2C (7.3 -> 10.1s)
      tl.set("#s2-glass", {{ opacity: 0 }}, 0);
      tl.set("#s2-glass", {{ opacity: 1 }}, 7.3);
      tl.set("#s2-ots", {{ opacity: 0 }}, 7.3);
      {cam_2c}
    """
    return _subcomp_shell("scene-02-office", dur, styles, body, script)


def build_scene_03(dur: float, clips_dir: Path | None = None) -> str:
    # Cena 3 (dur = 14.0s):
    # 0.0 - 4.3s: shot_3a (4.3s <= 5.03s)
    # 4.3 - 9.6s: shot_3b (5.3s * 0.92 = 4.88s <= 5.03s)
    # 9.6 - 14.0s: shot_3c (4.4s <= 5.03s)
    m3a, v3a = render_shot_media("shot_3a", 0.0, 4.3, playback_rate=1.0, clips_dir=clips_dir)
    m3b, v3b = render_shot_media("shot_3b", 4.3, 5.3, playback_rate=0.92, clips_dir=clips_dir)
    m3c, v3c = render_shot_media("shot_3c", 9.6, round(dur - 9.6, 3), playback_rate=1.0, clips_dir=clips_dir)

    styles = """
      .golden-dust {
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at 24% 24%, rgba(255,212,135,0.22) 0%, rgba(255,212,135,0) 62%);
        pointer-events: none;
        z-index: 12;
      }
    """

    body = f"""
      <div id="s3-a" class="shot">
        <div id="s3-a-cam" class="shot-cam">
          {m3a}
        </div>
        <div class="golden-dust"></div>
        <div class="cinematic-vignette"></div>
      </div>

      <div id="s3-b" class="shot">
        <div id="s3-b-cam" class="shot-cam">
          {m3b}
        </div>
        <div class="golden-dust"></div>
        <div class="cinematic-vignette"></div>
      </div>

      <div id="s3-c" class="shot">
        <div id="s3-c-cam" class="shot-cam">
          {m3c}
        </div>
        <div class="golden-dust"></div>
        <div class="cinematic-vignette"></div>
      </div>
    """

    cam_3a = (
        'tl.set("#s3-a-cam", { scale: 1.0 }, 0);'
        if v3a
        else 'tl.fromTo("#s3-a-cam", { scale: 1.0, x: -12 }, { scale: 1.06, x: 10, duration: 4.3, ease: "sine.inOut" }, 0);'
    )
    cam_3b = (
        'tl.set("#s3-b-cam", { scale: 1.0 }, 4.3);'
        if v3b
        else 'tl.fromTo("#s3-b-cam", { scale: 1.0, y: 6 }, { scale: 1.07, y: -8, duration: 5.3, ease: "sine.inOut" }, 4.3);'
    )
    cam_3c = (
        'tl.set("#s3-c-cam", { scale: 1.0 }, 9.6);'
        if v3c
        else 'tl.fromTo("#s3-c-cam", { scale: 1.04, x: 8 }, { scale: 1.0, x: 0, duration: 2.6, ease: "power2.out" }, 9.6);\n      tl.to("#s3-c-cam", { scale: 1.025, duration: 1.8, ease: "none" }, 12.2);'
    )

    script = f"""
      // 3A (0 -> 4.3s)
      {cam_3a}

      // 3B (4.3 -> 9.6s)
      tl.set("#s3-b", {{ opacity: 0 }}, 0);
      tl.set("#s3-b", {{ opacity: 1 }}, 4.3);
      tl.set("#s3-a", {{ opacity: 0 }}, 4.3);
      {cam_3b}

      // 3C (9.6 -> 14.0s)
      tl.set("#s3-c", {{ opacity: 0 }}, 0);
      tl.set("#s3-c", {{ opacity: 1 }}, 9.6);
      tl.set("#s3-b", {{ opacity: 0 }}, 9.6);
      {cam_3c}
    """
    return _subcomp_shell("scene-03-copa", dur, styles, body, script)


def build_scene_04(dur: float, clips_dir: Path | None = None) -> str:
    # Cena 4 (dur = 13.2s):
    # 0.0 - 5.6s: shot_4a (5.6s * 0.88 = 4.928s <= 5.03s)
    # 5.6 - 13.2s: shot_4b (7.6s * 0.65 = 4.940s <= 5.03s) + rotulo tracked no frasco + CTA
    m4a, v4a = render_shot_media("shot_4a", 0.0, 5.6, playback_rate=0.88, clips_dir=clips_dir)
    m4b, v4b = render_shot_media("shot_4b", 5.6, round(dur - 5.6, 3), playback_rate=0.65, clips_dir=clips_dir)

    styles = """
      .warm-lamp-bloom {
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at 26% 24%, rgba(255,196,112,0.18) 0%, rgba(255,196,112,0) 60%);
        pointer-events: none;
        z-index: 10;
      }
      .bottle-label-overlay {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 14;
      }
      .cta-zone {
        position: absolute;
        left: 110px;
        right: 110px;
        bottom: 120px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 14px;
        z-index: 25;
      }
      .cta-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 22px 62px;
        border-radius: 999px;
        background: #9EB8A0;
        color: #101513;
        font-size: 40px;
        font-weight: 800;
        letter-spacing: -0.02em;
        box-shadow: 0 18px 42px rgba(0, 0, 0, 0.50);
      }
      .cta-sub {
        font-size: 29px;
        font-weight: 700;
        color: #F2ECE3;
        text-shadow: 0 2px 10px rgba(0,0,0,0.65);
      }
    """

    body = f"""
      <div id="s4-a" class="shot">
        <div id="s4-a-cam" class="shot-cam">
          {m4a}
        </div>
        <div class="warm-lamp-bloom"></div>
        <div class="cinematic-vignette"></div>
      </div>

      <div id="s4-b" class="shot">
        <div id="s4-b-cam" class="shot-cam">
          {m4b}
          <!-- Rotulo oficial Revenue Clean composto com sombreamento cilindrico 3D e tracking no frasco -->
          <svg class="bottle-label-overlay" viewBox="0 0 1080 1920" width="1080" height="1920" data-layout-ignore="true">
            <defs>
              <linearGradient id="rc-cyl-bg" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#222C26" stop-opacity="0.96"/>
                <stop offset="55%" stop-color="#17201B" stop-opacity="0.96"/>
                <stop offset="100%" stop-color="#0D120F" stop-opacity="0.98"/>
              </linearGradient>
              <linearGradient id="rc-cyl-sheen" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="rgba(255,255,255,0.22)"/>
                <stop offset="35%" stop-color="rgba(255,255,255,0.04)"/>
                <stop offset="100%" stop-color="rgba(0,0,0,0.28)"/>
              </linearGradient>
            </defs>
            <g id="rc-label-group">
              <rect x="-56" y="-82" width="112" height="164" rx="12" fill="url(#rc-cyl-bg)" stroke="rgba(229, 200, 146, 0.72)" stroke-width="2.2"/>
              <rect x="-56" y="-82" width="112" height="164" rx="12" fill="url(#rc-cyl-sheen)"/>
              <text x="0" y="-34" text-anchor="middle" fill="#FAF7F0" font-family="Sora, sans-serif" font-weight="800" font-size="14" letter-spacing="1.2">REVENUE</text>
              <text x="0" y="-12" text-anchor="middle" fill="#B5D1B8" font-family="Sora, sans-serif" font-weight="800" font-size="17" letter-spacing="1">CLEAN</text>
              <line x1="-34" y1="6" x2="34" y2="6" stroke="rgba(229,200,146,0.45)" stroke-width="1.5"/>
              <text x="0" y="30" text-anchor="middle" fill="#F2D8C8" font-family="Sora, sans-serif" font-weight="700" font-size="10.5">AROMA ÍNTIMO</text>
              <text x="0" y="50" text-anchor="middle" fill="#9AA89D" font-family="Sora, sans-serif" font-weight="600" font-size="8.5">CUIDADO DIÁRIO</text>
            </g>
          </svg>
        </div>
        <div class="warm-lamp-bloom"></div>
        <div class="cinematic-vignette"></div>

        <!-- Terco inferior livre para CTA Saiba mais -->
        <div id="s4-cta" class="cta-zone">
          <div class="cta-pill">Saiba mais →</div>
          <div class="cta-sub">Revenue Clean · Aroma Íntimo</div>
        </div>
      </div>
    """

    cam_4a = (
        'tl.set("#s4-a-cam", { scale: 1.0 }, 0);'
        if v4a
        else 'tl.fromTo("#s4-a-cam", { scale: 1.0, y: 10 }, { scale: 1.07, y: -12, duration: 5.6, ease: "sine.inOut" }, 0);'
    )
    cam_4b = (
        'tl.set("#s4-b-cam", { scale: 1.0 }, 5.6);'
        if v4b
        else 'tl.fromTo("#s4-b-cam", { scale: 1.02, y: 8 }, { scale: 1.07, y: -10, duration: 7.6, ease: "sine.inOut" }, 5.6);'
    )

    label_track_script = (
        """
      // Tracking preciso do rotulo sobre o cilindro verde durante o push-in do Google Flow (5.6 -> 13.2s)
      tl.set("#rc-label-group", { x: 458, y: 1052, rotation: -17.5, scale: 0.92, transformOrigin: "0px 0px" }, 0);
      tl.to("#rc-label-group", { x: 450, y: 1175, rotation: -16.5, scale: 1.06, duration: 3.85, ease: "sine.inOut" }, 5.6);
      tl.to("#rc-label-group", { x: 438, y: 1265, rotation: -15.5, scale: 1.14, duration: 3.75, ease: "sine.inOut" }, 9.45);
        """
        if v4b
        else """
      tl.set("#rc-label-group", { x: 454, y: 1054, rotation: -17.5, scale: 1.0, transformOrigin: "0px 0px" }, 0);
        """
    )

    script = f"""
      // 4A (0 -> 5.6s)
      {cam_4a}

      // 4B (5.6 -> 13.2s)
      tl.set("#s4-b", {{ opacity: 0 }}, 0);
      tl.set("#s4-b", {{ opacity: 1 }}, 5.6);
      tl.set("#s4-a", {{ opacity: 0 }}, 5.6);
      {cam_4b}
      {label_track_script}

      tl.fromTo("#s4-cta", {{ y: 26, opacity: 0, scale: 0.92 }}, {{ y: 0, opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.6)" }}, 8.6);
      tl.to("#s4-cta .cta-pill", {{ scale: 1.05, duration: 0.55, yoyo: true, repeat: 3, ease: "sine.inOut" }}, 9.6);
    """
    return _subcomp_shell("scene-04-unboxing", dur, styles, body, script)


def _group_captions(words: list[dict[str, Any]], abs_start: float, max_words: int = 4) -> list[dict[str, Any]]:
    chunks = []
    cur = []
    for w in words:
        cur.append(w)
        if len(cur) >= max_words:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)

    res = []
    for i, grp in enumerate(chunks):
        cs = round(abs_start + grp[0]["start"], 3)
        if i + 1 < len(chunks):
            nxt = round(abs_start + chunks[i + 1][0]["start"], 3)
            ce = round(min(abs_start + grp[-1]["end"] + 0.08, nxt - 0.015), 3)
        else:
            ce = round(abs_start + grp[-1]["end"] + 0.18, 3)
        if ce <= cs:
            ce = round(cs + 0.2, 3)
        res.append(
            {
                "start": cs,
                "duration": round(ce - cs, 3),
                "text": " ".join(w["text"] for w in grp),
            }
        )
    return res


def main() -> None:
    manifest = json.loads(AUDIO_MANIFEST.read_text(encoding="utf-8"))
    voices = manifest["voices"]
    foley = manifest["foley"]

    s1_start, s1_dur = 0.0, 7.5
    s2_start, s2_dur = 7.5, 10.1
    s3_start, s3_dur = 17.6, 14.0
    s4_start, s4_dur = 31.6, 13.2
    total_dur = 44.8

    COMPS_DIR.mkdir(parents=True, exist_ok=True)
    (COMPS_DIR / "scene-01-elevator.html").write_text(build_scene_01(s1_dur), encoding="utf-8")
    (COMPS_DIR / "scene-02-office.html").write_text(build_scene_02(s2_dur), encoding="utf-8")
    (COMPS_DIR / "scene-03-copa.html").write_text(build_scene_03(s3_dur), encoding="utf-8")
    (COMPS_DIR / "scene-04-unboxing.html").write_text(build_scene_04(s4_dur), encoding="utf-8")

    voice_placements = [
        ("c1_passageira", 2.35),
        ("c2_marina_off", 7.85),
        ("c3_bia_1", 19.6),
        ("c3_marina_2", 21.9),
        ("c3_bia_3", 27.3),
        ("c4_marina_off", 31.95),
        ("c4_locucao", 37.3),
    ]

    voice_audio_tags = []
    caption_slots = []
    for vid, v_start in voice_placements:
        info = voices[vid]
        voice_audio_tags.append(
            f"""
      <audio
        id="vo-{vid}"
        src="{info['file']}"
        data-audio-group="voiceover"
        data-start="{v_start}"
        data-duration="{info['duration']}"
        data-track-index="10"
        data-volume="1.15"
      ></audio>"""
        )
        is_s4_hero = v_start >= 37.0
        for c_idx, ch in enumerate(_group_captions(info["words"], v_start, max_words=4)):
            extra_cls = " cap-high" if is_s4_hero else ""
            caption_slots.append(
                f"""
        <div
          id="cap-{vid}-{c_idx}"
          class="clip cap-slot{extra_cls}"
          data-start="{ch['start']}"
          data-duration="{ch['duration']}"
          data-track-index="5"
          data-layout-allow-caption-zone="true"
        >
          <div class="cap-pill">{html.escape(ch['text'])}</div>
        </div>"""
            )

    foley_tags = f"""
      <audio id="fx-ding" src="assets/audio/generated/foley_elevator_ding.wav" data-start="0.4" data-duration="{foley['elevator_ding']}" data-track-index="12" data-volume="0.42"></audio>
      <audio id="fx-strap" src="assets/audio/generated/foley_leather_squeeze.wav" data-start="5.45" data-duration="{foley['leather_squeeze']}" data-track-index="13" data-volume="0.52"></audio>
      <audio id="fx-chair" src="assets/audio/generated/foley_chair_slide.wav" data-start="27.0" data-duration="{foley['chair_slide']}" data-track-index="12" data-volume="0.40"></audio>
      <audio id="fx-tape" src="assets/audio/generated/foley_tape_peel.wav" data-start="32.0" data-duration="{foley['tape_peel']}" data-track-index="13" data-volume="0.48"></audio>
    """

    # BGM com abafamento real de 0.5s logo apos a pergunta no elevador (5.38s -> 5.92s)
    bgm_automation = json.dumps(
        {
            "version": 1,
            "lanes": [
                {
                    "target": "volume",
                    "points": [
                        {"t": 0.0, "v": 0.11},
                        {"t": 5.35, "v": 0.11},
                        {"t": 5.40, "v": 0.003},
                        {"t": 5.92, "v": 0.003},
                        {"t": 6.12, "v": 0.07},
                        {"t": 17.6, "v": 0.08},
                        {"t": 31.6, "v": 0.12},
                        {"t": 44.0, "v": 0.12},
                        {"t": 44.8, "v": 0.02},
                    ],
                }
            ],
        }
    )

    index_html = f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>O Comentário no Elevador — Revenue Clean (3D Pixar)</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      @font-face {{
        font-family: "Sora";
        src: url("assets/fonts/sora-600-latin.woff2") format("woff2");
        font-weight: 600;
        font-style: normal;
        font-display: swap;
      }}
      @font-face {{
        font-family: "Sora";
        src: url("assets/fonts/sora-700-latin.woff2") format("woff2");
        font-weight: 700;
        font-style: normal;
        font-display: swap;
      }}
      @font-face {{
        font-family: "Sora";
        src: url("assets/fonts/sora-800-latin.woff2") format("woff2");
        font-weight: 800;
        font-style: normal;
        font-display: swap;
      }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 100%; height: 100%; overflow: hidden; background: #0E1016; font-family: "Sora", sans-serif; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #0E1016; }}
      .scene-slot {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
      #captions-layer {{
        position: absolute;
        left: 96px;
        right: 96px;
        bottom: 340px;
        height: 120px;
        z-index: 60;
        pointer-events: none;
      }}
      .cap-slot {{
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
      }}
      .cap-slot.cap-high {{
        transform: translateY(-75px);
      }}
      .cap-pill {{
        padding: 14px 28px;
        border-radius: 18px;
        background: rgba(14, 17, 24, 0.86);
        border: 1.5px solid rgba(255, 255, 255, 0.14);
        color: #F4F6FA;
        font-size: 34px;
        font-weight: 700;
        line-height: 1.2;
        text-align: center;
        box-shadow: 0 10px 26px rgba(0,0,0,0.38);
      }}
    </style>
  </head>
  <body>
    <div
      id="root"
      data-composition-id="main"
      data-start="0"
      data-duration="{total_dur}"
      data-width="1080"
      data-height="1920"
      data-fx-chain='{{&quot;version&quot;:1,&quot;nodes&quot;:[{{&quot;type&quot;:&quot;limiter&quot;,&quot;id&quot;:&quot;m_lim&quot;,&quot;label&quot;:&quot;Master Ceiling&quot;,&quot;params&quot;:{{&quot;limit&quot;:-1,&quot;attack&quot;:5,&quot;release&quot;:50,&quot;level_out&quot;:0}}}}]}}'
    >
      <hf-audio-group
        id="voiceover"
        data-label="Voiceover"
        data-volume="1"
        data-fx-chain='{{&quot;version&quot;:1,&quot;nodes&quot;:[{{&quot;type&quot;:&quot;highpass&quot;,&quot;id&quot;:&quot;vo_hp&quot;,&quot;label&quot;:&quot;Remove Rumble&quot;,&quot;params&quot;:{{&quot;frequency&quot;:90,&quot;q&quot;:0.707,&quot;poles&quot;:&quot;2&quot;}}}},{{&quot;type&quot;:&quot;compressor&quot;,&quot;id&quot;:&quot;vo_comp&quot;,&quot;label&quot;:&quot;Voice Leveler&quot;,&quot;params&quot;:{{&quot;threshold&quot;:-18,&quot;ratio&quot;:3.2}}}}]}}'
      ></hf-audio-group>

      <div id="slot-s1" class="clip scene-slot" data-composition-id="scene-01-elevator" data-composition-src="compositions/scene-01-elevator.html" data-start="{s1_start}" data-duration="{s1_dur}" data-track-index="0" data-width="1080" data-height="1920"></div>
      <div id="slot-s2" class="clip scene-slot" data-composition-id="scene-02-office" data-composition-src="compositions/scene-02-office.html" data-start="{s2_start}" data-duration="{s2_dur}" data-track-index="0" data-width="1080" data-height="1920"></div>
      <div id="slot-s3" class="clip scene-slot" data-composition-id="scene-03-copa" data-composition-src="compositions/scene-03-copa.html" data-start="{s3_start}" data-duration="{s3_dur}" data-track-index="0" data-width="1080" data-height="1920"></div>
      <div id="slot-s4" class="clip scene-slot" data-composition-id="scene-04-unboxing" data-composition-src="compositions/scene-04-unboxing.html" data-start="{s4_start}" data-duration="{s4_dur}" data-track-index="0" data-width="1080" data-height="1920"></div>

      <div id="captions-layer" data-layout-allow-caption-zone="true">
        {''.join(caption_slots)}
      </div>

      <audio id="bgm" src="assets/audio/generated/bgm_45s.mp3" data-start="0" data-duration="{total_dur}" data-track-index="11" data-volume="0.11" data-automation='{bgm_automation}'></audio>
      {''.join(voice_audio_tags)}
      {foley_tags}
    </div>

    <script>
      (function () {{
        var tl = gsap.timeline({{ paused: true }});
        tl.set({{}}, {{}}, {total_dur});
        window.__timelines["main"] = tl;
      }})();
    </script>
  </body>
</html>
"""
    (ROOT / "index.html").write_text(index_html, encoding="utf-8")
    video_count = sum(1 for sid in SHOT_ASSETS if (CLIPS_DIR / SHOT_ASSETS[sid]["video"]).exists())
    print(f"[OK] Built Pixar 3D composition ({video_count}/{len(SHOT_ASSETS)} animated clips, {total_dur}s) at {ROOT / 'index.html'}")


if __name__ == "__main__":
    main()
