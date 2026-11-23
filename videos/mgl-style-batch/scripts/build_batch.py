"""Compilador v2 do Motor MGL para HyperFrames (Word-Cue + Rig 2.5D + Props Dinamicos).

Uso:
  python scripts/build_batch.py            # compila todos os videos de data/batch_scripts.json
  python scripts/build_batch.py --reuse    # reutiliza mp3s ja sintetizados quando existentes
"""
from __future__ import annotations

import asyncio
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import edge_tts

from cue_engine import build_speech_envelopes, group_caption_chunks, resolve_word_cue
from mascot_rig import render_inline_mascot_rig
from props_engine import render_prop

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"
AUDIO_GEN_DIR = ASSETS_DIR / "audio" / "generated"
COMPOSITIONS_DIR = PROJECT_ROOT / "compositions"

THEMES = {
    "light": {
        "wall": "#EAEBEE",
        "floor": "#D4D8E0",
        "horizon": "#14161D",
        "text": "#11131A",
        "muted": "#4A5060",
        "divider": "rgba(20, 22, 29, 0.18)",
        "hl_bg": "#D0EB2F",
        "hl_text": "#11131A",
    },
    "dark": {
        "wall": "#0F1017",
        "floor": "#171821",
        "horizon": "#FFFFFF",
        "text": "#FFFFFF",
        "muted": "#B5BAC9",
        "divider": "rgba(255, 255, 255, 0.20)",
        "hl_bg": "#D0EB2F",
        "hl_text": "#11131A",
    },
    "lime": {
        "wall": "#D0EB2F",
        "floor": "#B8D71A",
        "horizon": "#14161D",
        "text": "#11131A",
        "muted": "#232810",
        "divider": "rgba(20, 22, 29, 0.22)",
        "hl_bg": "#11131A",
        "hl_text": "#FFFFFF",
    },
}

_DURATION_CACHE: dict[Path, float] = {}


def probe_duration(media_path: Path) -> float:
    if media_path in _DURATION_CACHE:
        return _DURATION_CACHE[media_path]
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(media_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    dur = float(res.stdout.strip())
    _DURATION_CACHE[media_path] = dur
    return dur


def ensure_looped_bgm(src_bgm: Path, target_dur: float, out_bgm: Path) -> Path:
    real_dur = probe_duration(src_bgm)
    if real_dur >= target_dur:
        return src_bgm
    out_bgm.parent.mkdir(parents=True, exist_ok=True)
    if out_bgm.exists() and abs(probe_duration(out_bgm) - target_dur) < 0.25:
        return out_bgm
    cmd = [
        "ffmpeg",
        "-y",
        "-stream_loop",
        "-1",
        "-i",
        str(src_bgm),
        "-t",
        f"{target_dur:.3f}",
        "-c:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(out_bgm),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    _DURATION_CACHE.pop(out_bgm, None)
    return out_bgm


async def _synthesize_utterance(
    text: str,
    voice: str,
    rate: str,
    pitch: str,
    out_mp3: Path,
) -> tuple[float, list[dict[str, Any]]]:
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch,
        boundary="WordBoundary",
    )
    words: list[dict[str, Any]] = []
    audio_bytes = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes.extend(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            start_s = chunk["offset"] / 10_000_000.0
            dur_s = chunk["duration"] / 10_000_000.0
            words.append(
                {
                    "text": chunk["text"],
                    "start": round(start_s, 3),
                    "end": round(start_s + max(dur_s, 0.08), 3),
                }
            )
    out_mp3.write_bytes(bytes(audio_bytes))
    dur = round(probe_duration(out_mp3), 3)
    return dur, words


async def synthesize_scene(
    scene: dict[str, Any],
    default_voice: str,
    default_rate: str,
    out_mp3: Path,
    meta_json: Path,
    reuse: bool = False,
) -> tuple[float, list[dict[str, Any]]]:
    if reuse and out_mp3.exists() and meta_json.exists():
        meta = json.loads(meta_json.read_text(encoding="utf-8"))
        return float(meta["duration"]), meta["words"]

    dialogue = scene.get("dialogue")
    if not dialogue:
        dur, words = await _synthesize_utterance(
            text=scene["narration"],
            voice=scene.get("voice", default_voice),
            rate=scene.get("rate", default_rate),
            pitch=scene.get("pitch", "+0Hz"),
            out_mp3=out_mp3,
        )
        meta_json.write_text(json.dumps({"duration": dur, "words": words}, ensure_ascii=False), encoding="utf-8")
        return dur, words

    # Multi-speaker dialogue in one scene: synthesize parts & concat via ffmpeg
    part_files: list[Path] = []
    merged_words: list[dict[str, Any]] = []
    cursor = 0.0
    gap = 0.08
    filter_inputs: list[str] = []
    filter_parts: list[str] = []
    for p_idx, turn in enumerate(dialogue):
        part_mp3 = out_mp3.with_name(f"{out_mp3.stem}_p{p_idx}.mp3")
        p_dur, p_words = await _synthesize_utterance(
            text=turn["text"],
            voice=turn.get("voice", default_voice),
            rate=turn.get("rate", default_rate),
            pitch=turn.get("pitch", "+0Hz"),
            out_mp3=part_mp3,
        )
        part_files.append(part_mp3)
        for w in p_words:
            merged_words.append(
                {
                    "text": w["text"],
                    "start": round(cursor + w["start"], 3),
                    "end": round(cursor + w["end"], 3),
                }
            )
        filter_inputs.extend(["-i", str(part_mp3)])
        if p_idx + 1 < len(dialogue):
            filter_parts.append(f"[{p_idx}:a]apad=pad_dur={gap}[a{p_idx}]")
            cursor = round(cursor + p_dur + gap, 3)
        else:
            filter_parts.append(f"[{p_idx}:a]anull[a{p_idx}]")
            cursor = round(cursor + p_dur, 3)

    concat_labels = "".join(f"[a{i}]" for i in range(len(dialogue)))
    fc = ";".join(filter_parts) + f";{concat_labels}concat=n={len(dialogue)}:v=0:a=1[aout]"
    cmd = ["ffmpeg", "-y", *filter_inputs, "-filter_complex", fc, "-map", "[aout]", "-c:a", "libmp3lame", "-q:a", "4", str(out_mp3)]
    subprocess.run(cmd, capture_output=True, check=True)
    _DURATION_CACHE.pop(out_mp3, None)
    real_dur = round(probe_duration(out_mp3), 3)
    meta_json.write_text(json.dumps({"duration": real_dur, "words": merged_words}, ensure_ascii=False), encoding="utf-8")
    return real_dur, merged_words


def _render_sweep_pill(
    text_escaped: str,
    bg_color: str,
    fg_color: str,
    cue_time: float,
    round_pill: bool = False,
) -> str:
    extra_cls = " hl-pill-round" if round_pill else ""
    return (
        f'<span class="hl-sweep-wrap{extra_cls}" data-hl-cue-time="{cue_time}" data-layout-allow-overlap="true">'
        f'<span class="hl-sweep-base">{text_escaped}</span>'
        f'<span class="hl-sweep-bar" style="background:{bg_color};"></span>'
        f'<span class="hl-sweep-fg" style="color:{fg_color};" aria-hidden="true" data-layout-ignore="true">{text_escaped}</span>'
        f"</span>"
    )


def render_headline_html(
    headline: dict[str, Any],
    theme_key: str,
    words: list[dict[str, Any]],
    scene_start: float,
    scene_dur: float,
) -> str:
    mode = headline.get("mode", "stack")
    t = THEMES[theme_key]
    hl_cue_word = headline.get("highlightCue")
    hl_cue_time = resolve_word_cue(words, hl_cue_word, 0.25, scene_start, scene_dur)

    if mode == "split":
        left_lines = "".join(
            f'<div class="hl-line anim-hl">{html.escape(line)}</div>'
            for line in headline.get("left", [])
        )
        right_hi = headline.get("rightHighlightLine", 0)
        right_parts = []
        for idx, line in enumerate(headline.get("right", [])):
            esc = html.escape(line)
            if idx == right_hi:
                sweep = _render_sweep_pill(esc, t["hl_bg"], t["hl_text"], hl_cue_time)
                right_parts.append(f'<div class="hl-line anim-hl">{sweep}</div>')
            else:
                right_parts.append(f'<div class="hl-line anim-hl">{esc}</div>')
        return f"""
        <div class="headline-split">
          <div class="split-col">{left_lines}</div>
          <div class="split-divider" style="background:{t['divider']};"></div>
          <div class="split-col">{''.join(right_parts)}</div>
        </div>"""

    badge = headline.get("badge")
    lines = headline.get("lines", [])
    html_parts: list[str] = []
    for idx, line_obj in enumerate(lines):
        txt = html.escape(line_obj["text"])
        hi = line_obj.get("highlight", False)
        line_cue_w = line_obj.get("cue_word")
        line_time_attr = ""
        if line_cue_w:
            lt = resolve_word_cue(words, line_cue_w, 0.2 + idx * 0.22, scene_start, scene_dur)
            line_time_attr = f' data-line-cue-time="{lt}"'

        if hi == "dark-pill":
            ct = resolve_word_cue(words, line_cue_w or hl_cue_word, 0.55, scene_start, scene_dur)
            inner = _render_sweep_pill(txt, "#11131A", "#FFFFFF", ct, round_pill=True)
        elif hi:
            ct = resolve_word_cue(words, line_cue_w or hl_cue_word, 0.28, scene_start, scene_dur)
            inner = _render_sweep_pill(txt, t["hl_bg"], t["hl_text"], ct)
        else:
            inner = txt

        if idx == 0 and badge:
            badge_bg = "#11131A" if theme_key == "lime" else "#D0EB2F"
            badge_fg = "#FFFFFF" if theme_key == "lime" else "#11131A"
            html_parts.append(
                f'<div class="hl-row anim-hl"{line_time_attr}><span class="rank-badge" style="background:{badge_bg};color:{badge_fg};">{html.escape(badge)}</span><span class="hl-inline">{inner}</span></div>'
            )
        else:
            html_parts.append(f'<div class="hl-row anim-hl"{line_time_attr}>{inner}</div>')
    return f'<div class="headline-stack">{"".join(html_parts)}</div>'


def inject_cue_times_into_prop(
    prop_svg: str,
    words: list[dict[str, Any]],
    scene_start: float,
    scene_dur: float,
) -> tuple[str, list[dict[str, Any]]]:
    """Resolve `data-cue-word` -> `data-cue-time` direto no SVG e coleta micro-SFX."""
    cue_sfx_events: list[dict[str, Any]] = []
    pattern = re.compile(r'(<[^>]+data-cue-step="[^"]+"[^>]*>)')

    def _repl(match: re.Match[str]) -> str:
        tag = match.group(1)
        m_word = re.search(r'data-cue-word="([^"]*)"', tag)
        m_fb = re.search(r'data-cue-fallback="([^"]*)"', tag)
        m_sfx = re.search(r'data-cue-sfx="([^"]*)"', tag)
        cue_word = html.unescape(m_word.group(1)) if m_word else None
        fb = float(m_fb.group(1)) if m_fb else 0.25
        ct = resolve_word_cue(words, cue_word, fb, scene_start, scene_dur)
        if m_sfx:
            cue_sfx_events.append({"time": ct, "sfx": m_sfx.group(1)})
        if tag.endswith("/>"):
            return tag[:-2] + f' data-cue-time="{ct}" />'
        return tag[:-1] + f' data-cue-time="{ct}">'

    updated = pattern.sub(_repl, prop_svg)
    return updated, cue_sfx_events


def compile_video_html(
    video: dict[str, Any],
    scene_timings: list[dict[str, Any]],
    total_duration: float,
    bgm_rel: str,
    path_prefix: str = "",
) -> str:
    slug = video["slug"]
    title = html.escape(video.get("title", slug))

    scenes_html: list[str] = []
    audio_html: list[str] = []
    captions_html: list[str] = []
    timeline_js_blocks: list[str] = []

    # Alocador sem sobreposicao para SFX (tracks 12..15)
    sfx_tracks: dict[int, float] = {12: 0.0, 13: 0.0, 14: 0.0, 15: 0.0}
    sfx_counter = 0

    def _add_sfx(sfx_name: str, at_time: float, volume: float = 0.22) -> None:
        nonlocal sfx_counter
        sfx_file = ASSETS_DIR / "sfx" / f"{sfx_name}.mp3"
        if not sfx_file.exists():
            return
        real_dur = probe_duration(sfx_file)
        slot_dur = round(min(real_dur, 0.85, max(0.2, total_duration - at_time)), 3)
        if slot_dur < 0.15 or at_time >= total_duration - 0.1:
            return
        chosen_track = None
        for tr in (12, 13, 14, 15):
            if sfx_tracks[tr] <= at_time + 0.01:
                chosen_track = tr
                break
        if chosen_track is None:
            return
        sfx_tracks[chosen_track] = round(at_time + slot_dur + 0.02, 3)
        sfx_counter += 1
        audio_html.append(
            f"""
      <audio
        id="sfx-ev-{sfx_counter}"
        src="{path_prefix}assets/sfx/{sfx_name}.mp3"
        data-start="{round(at_time, 3)}"
        data-duration="{slot_dur}"
        data-track-index="{chosen_track}"
        data-volume="{volume}"
      ></audio>"""
        )

    for idx, st in enumerate(scene_timings):
        sc = st["scene"]
        t_key = sc.get("theme", "light")
        t = THEMES.get(t_key, THEMES["light"])
        s_start = st["start"]
        s_dur = st["duration"]
        sid = sc["id"]
        words = st["words"]

        base_pose = sc.get("pose", "confident")
        pose_cues_cfg = sc.get("pose_cues", [])
        resolved_pose_cues: list[dict[str, Any]] = []
        last_pt = s_start + 0.25
        poses_to_mount = [base_pose]
        for pc in pose_cues_cfg:
            pt = resolve_word_cue(words, pc.get("word"), 0.5, s_start, s_dur, after_time=last_pt)
            pt = min(pt, round(s_start + s_dur - 0.35, 3))
            if pt > last_pt + 0.12:
                resolved_pose_cues.append({"time": pt, "pose": pc["pose"]})
                poses_to_mount.append(pc["pose"])
                last_pt = pt
                _add_sfx("whoosh-short", pt, volume=0.16)

        mascot_slots_html = "".join(
            render_inline_mascot_rig(
                pose=p_name,
                uid=f"{idx}-{p_idx}-{p_name}",
                assets_dir=ASSETS_DIR,
                path_prefix=path_prefix,
            )
            for p_idx, p_name in enumerate(poses_to_mount)
        )

        raw_prop_svg = render_prop(sc.get("prop", "bar_chart"), t_key, sc.get("propData"))
        prop_svg, cue_sfx_events = inject_cue_times_into_prop(raw_prop_svg, words, s_start, s_dur)
        headline_html = render_headline_html(sc.get("headline", {}), t_key, words, s_start, s_dur)

        # Speech envelopes para lip-sync e balanco de cabeca
        speech_envs = build_speech_envelopes(words, s_start)
        speech_json = json.dumps(speech_envs)
        pose_cues_json = json.dumps(resolved_pose_cues)

        emphasis_time = (
            resolve_word_cue(words, sc.get("emphasis"), 0.55, s_start, s_dur)
            if sc.get("emphasis")
            else None
        )
        shake_flag = "true" if sc.get("shake") else "false"

        scenes_html.append(
            f"""
      <section
        id="scene-{idx}-{sid}"
        class="clip scene theme-{t_key}"
        data-start="{s_start}"
        data-duration="{s_dur}"
        data-track-index="0"
        style="--wall:{t['wall']};--floor:{t['floor']};--horizon:{t['horizon']};--ink:{t['text']};"
      >
        <div class="scene-curtain">
          <div class="scene-camera">
            <div class="layer-bg">
              <div class="scene-bg-wall"></div>
              <div class="scene-bg-floor"></div>
              <div class="scene-horizon"></div>
            </div>
            <div class="headline-zone">
              {headline_html}
            </div>
            <div class="stage-prop layer-prop" data-layout-ignore="true">
              {prop_svg}
            </div>
            <div class="mascot-wrap layer-mascot" data-layout-ignore="true">
              {mascot_slots_html}
            </div>
          </div>
        </div>
      </section>"""
        )

        # Voiceover audio
        audio_html.append(
            f"""
      <audio
        id="vo-{idx}-{sid}"
        src="{st['audio_rel']}"
        data-audio-group="voiceover"
        data-start="{s_start}"
        data-duration="{st['audio_dur']}"
        data-track-index="10"
        data-volume="1.15"
      ></audio>"""
        )

        if sc.get("sfx"):
            _add_sfx(sc["sfx"], s_start, volume=0.24)
        for ev in cue_sfx_events:
            _add_sfx(ev["sfx"], ev["time"], volume=0.18)

        # Captions pill
        for c_idx, chunk in enumerate(st["chunks"]):
            words_spans = "".join(
                f'<span class="cap-word" data-w-start="{w["start"]}" data-w-end="{w["end"]}">{html.escape(w["text"])}</span>'
                for w in chunk["words"]
            )
            captions_html.append(
                f"""
        <div
          id="cap-{idx}-{c_idx}"
          class="clip caption-slot"
          data-start="{chunk['start']}"
          data-duration="{chunk['duration']}"
          data-track-index="5"
          data-layout-allow-caption-zone="true"
        >
          <div class="caption-pill">{words_spans}</div>
        </div>"""
            )

        # Scene GSAP v2 Choreography
        timeline_js_blocks.append(
            f"""
        // Scene {idx}: {sid}
        (function() {{
          var sc = document.getElementById("scene-{idx}-{sid}");
          var curtain = sc.querySelector(".scene-curtain");
          var cam = sc.querySelector(".scene-camera");
          var layerProp = sc.querySelector(".layer-prop");
          var layerMascot = sc.querySelector(".layer-mascot");
          var t0 = {s_start};
          var sdur = {s_dur};

          // 1) Transicao cortina vertical (cenas >= 1)
          if ({idx} > 0 && curtain) {{
            tl.fromTo(curtain,
              {{ clipPath: "inset(0% 0% 100% 0%)" }},
              {{ clipPath: "inset(0% 0% 0% 0%)", duration: 0.24, ease: "power3.out" }},
              t0
            );
          }}

          // 2) Camera virtual + parallax em 3 camadas
          if (cam) {{
            tl.fromTo(cam, {{ scale: 1, x: 0, y: 0 }}, {{ scale: 1.028, duration: Math.max(sdur - 0.1, 0.5), ease: "sine.inOut" }}, t0);
            if ({shake_flag}) {{
              tl.to(cam, {{
                keyframes: [
                  {{ x: -7, y: 4, duration: 0.04 }},
                  {{ x: 6, y: -4, duration: 0.04 }},
                  {{ x: -4, y: 2, duration: 0.04 }},
                  {{ x: 0, y: 0, duration: 0.06 }}
                ],
                ease: "none"
              }}, t0 + 0.06);
            }}
            var empT = {json.dumps(emphasis_time)};
            if (empT !== null) {{
              tl.to(cam, {{ scale: 1.055, duration: 0.18, ease: "back.out(1.6)" }}, empT);
              tl.to(cam, {{ scale: 1.025, duration: 0.26, ease: "power2.out" }}, empT + 0.22);
            }}
          }}
          if (layerProp) {{
            tl.fromTo(layerProp, {{ x: -10 }}, {{ x: 4, duration: Math.max(sdur - 0.1, 0.5), ease: "none" }}, t0);
          }}
          if (layerMascot) {{
            tl.fromTo(layerMascot, {{ x: 10 }}, {{ x: -4, duration: Math.max(sdur - 0.1, 0.5), ease: "none" }}, t0);
          }}

          // 3) Headline lines + Highlight Sweep sincronizado
          var hls = sc.querySelectorAll(".anim-hl");
          hls.forEach(function (el, hIdx) {{
            var customT = el.getAttribute("data-line-cue-time");
            var ht = customT ? parseFloat(customT) : (t0 + 0.05 + hIdx * 0.14);
            tl.fromTo(el,
              {{ y: 24, opacity: 0, scale: 0.94 }},
              {{ y: 0, opacity: 1, scale: 1, duration: 0.24, ease: "back.out(1.6)" }},
              ht
            );
          }});

          var sweeps = sc.querySelectorAll("[data-hl-cue-time]");
          sweeps.forEach(function (sw) {{
            var stime = parseFloat(sw.getAttribute("data-hl-cue-time"));
            var bar = sw.querySelector(".hl-sweep-bar");
            var fg = sw.querySelector(".hl-sweep-fg");
            if (bar) {{
              tl.fromTo(bar, {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.26, ease: "power3.out" }}, stime);
            }}
            if (fg) {{
              tl.fromTo(fg, {{ clipPath: "inset(0% 100% 0% 0%)" }}, {{ clipPath: "inset(0% 0% 0% 0%)", duration: 0.26, ease: "power3.out" }}, stime);
            }}
          }});

          // 4) Props base (doors drop staggered, wheel spin, idle float)
          var drops = sc.querySelectorAll(".prop-stagger-drop");
          if (drops.length) {{
            tl.fromTo(drops,
              {{ y: -110, opacity: 0, scaleY: 1.06 }},
              {{ y: 0, opacity: 1, scaleY: 1, duration: 0.30, stagger: 0.08, ease: "back.out(1.4)" }},
              t0 + 0.04
            );
          }}
          var bases = sc.querySelectorAll(".prop-base");
          if (bases.length) {{
            tl.fromTo(bases,
              {{ y: 34, opacity: 0, scale: 0.92 }},
              {{ y: 0, opacity: 1, scale: 1, duration: 0.30, stagger: 0.06, ease: "back.out(1.5)" }},
              t0 + 0.06
            );
          }}
          var wheel = sc.querySelector(".prop-wheel");
          if (wheel) {{
            tl.to(wheel, {{ rotation: 360, duration: Math.max(sdur - 0.1, 0.5), ease: "none" }}, t0);
          }}

          // 5) Word-Cue Sub-Elementos (pop-overshoot, pop-spin, grow-y, slide, stroke-draw, count-up)
          var cueEls = sc.querySelectorAll("[data-cue-step]");
          cueEls.forEach(function (el) {{
            var ct = parseFloat(el.getAttribute("data-cue-time")) || (t0 + 0.3);
            var anim = el.getAttribute("data-cue-anim") || "pop-overshoot";
            if (anim === "stroke-draw" && typeof el.getTotalLength === "function") {{
              var len = el.getTotalLength();
              gsap.set(el, {{ strokeDasharray: len, strokeDashoffset: len }});
              tl.to(el, {{ strokeDashoffset: 0, duration: 0.34, ease: "power2.out" }}, ct);
            }} else if (anim === "grow-y") {{
              tl.fromTo(el, {{ scaleY: 0, opacity: 0 }}, {{ scaleY: 1, opacity: 1, duration: 0.32, ease: "back.out(1.7)" }}, ct);
            }} else if (anim === "pop-spin") {{
              tl.fromTo(el, {{ scale: 0, rotation: -18, opacity: 0 }}, {{ scale: 1, rotation: 0, opacity: 1, duration: 0.30, ease: "back.out(2.0)" }}, ct);
            }} else if (anim === "slide-left") {{
              tl.fromTo(el, {{ x: -32, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.24, ease: "power3.out" }}, ct);
            }} else if (anim === "slide-up") {{
              tl.fromTo(el, {{ y: 42, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.28, ease: "back.out(1.5)" }}, ct);
            }} else if (anim === "door-swing") {{
              tl.fromTo(el, {{ scaleX: 0.18 }}, {{ scaleX: 1, duration: 0.32, ease: "back.out(1.6)" }}, ct);
            }} else {{
              tl.fromTo(el, {{ scale: 0.3, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.28, ease: "back.out(2.1)" }}, ct);
            }}

            // Count-up numerico deterministico dentro do cue
            var counters = el.querySelectorAll(".cue-count-up");
            counters.forEach(function (cEl) {{
              var target = parseInt(cEl.getAttribute("data-count-target") || "0", 10);
              var pref = cEl.getAttribute("data-count-prefix") || "";
              var suff = cEl.getAttribute("data-count-suffix") || "";
              var proxy = {{ v: 0 }};
              tl.fromTo(proxy, {{ v: 0 }}, {{
                v: target,
                duration: 0.55,
                ease: "power2.out",
                onUpdate: function () {{
                  var formatted = Math.round(proxy.v).toLocaleString("pt-BR");
                  cEl.textContent = pref + formatted + suff;
                }}
              }}, ct);
            }});
          }});

          // 6) Rig 2.5D do Mascote: Squash & Stretch + Trocas Intra-Cena + Blink + Lip-Sync
          var slots = sc.querySelectorAll(".mascot-pose-slot");
          var poseCues = {pose_cues_json};
          var speechEnvs = {speech_json};

          slots.forEach(function (slot, sIdx) {{
            var bodyRig = slot.querySelector(".mascot-body-rig");
            var shadow = slot.querySelector(".mascot-shadow");
            var head = slot.querySelector(".mascot-head-rig");
            var eyelids = slot.querySelector(".mascot-eyelids");
            var mouth = slot.querySelector(".mascot-mouth");
            var armL = slot.querySelector(".mascot-arm-l");
            var armR = slot.querySelector(".mascot-arm-r");

            if (sIdx === 0) {{
              tl.set(slot, {{ opacity: 1 }}, t0);
              if (bodyRig) {{
                tl.fromTo(bodyRig,
                  {{ y: 48, scaleX: 1.18, scaleY: 0.80, svgOrigin: "210 526" }},
                  {{
                    keyframes: [
                      {{ y: -12, scaleX: 0.94, scaleY: 1.07, duration: 0.16, ease: "power2.out" }},
                      {{ y: 0, scaleX: 1, scaleY: 1, duration: 0.18, ease: "back.out(1.8)" }}
                    ],
                    ease: "none"
                  }},
                  t0
                );
              }}
              if (shadow) {{
                tl.fromTo(shadow,
                  {{ scaleX: 1.24, opacity: 0.18, transformOrigin: "50% 50%" }},
                  {{ scaleX: 1, opacity: 0.26, duration: 0.34, ease: "power2.out" }},
                  t0
                );
              }}
            }} else {{
              gsap.set(slot, {{ opacity: 0 }});
            }}

            // Piscada natural a cada 2.1s (finita)
            if (eyelids) {{
              for (var bt = t0 + 0.8; bt < t0 + sdur - 0.3; bt += 2.1) {{
                tl.to(eyelids, {{ opacity: 1, duration: 0.05, ease: "power1.in" }}, bt);
                tl.to(eyelids, {{ opacity: 0, duration: 0.07, ease: "power1.out" }}, bt + 0.06);
              }}
            }}

            // Lip-Sync & Head-Nodding no WordBoundary
            speechEnvs.forEach(function (env, eIdx) {{
              var wdur = Math.max(0.06, env.end - env.start);
              var half = wdur * 0.5;
              if (mouth) {{
                tl.to(mouth, {{ scaleY: 1 + 0.28 * env.strength, scaleX: 0.95, transformOrigin: "50% 50%", duration: half, ease: "power1.out" }}, env.start);
                tl.to(mouth, {{ scaleY: 1, scaleX: 1, transformOrigin: "50% 50%", duration: half, ease: "power1.in" }}, env.start + half);
              }}
              if (head && eIdx % 2 === 0) {{
                var tilt = (eIdx % 4 === 0) ? 2.4 : -2.2;
                tl.to(head, {{ rotation: tilt, y: -2.5, svgOrigin: "210 282", duration: half, ease: "sine.out" }}, env.start);
                tl.to(head, {{ rotation: 0, y: 0, svgOrigin: "210 282", duration: half, ease: "sine.in" }}, env.start + half);
              }}
            }});

            // Braco acompanha os cues da cena
            if (armL || armR) {{
              cueEls.forEach(function (ce, cIdx) {{
                var ct = parseFloat(ce.getAttribute("data-cue-time")) || (t0 + 0.4);
                var isLeft = (cIdx % 2 === 0 && armL);
                var targetArm = isLeft ? armL : armR;
                var armOrigin = isLeft ? "152 324" : "268 324";
                if (targetArm) {{
                  tl.to(targetArm, {{ rotation: -7, svgOrigin: armOrigin, duration: 0.14, ease: "power2.out" }}, ct);
                  tl.to(targetArm, {{ rotation: 0, svgOrigin: armOrigin, duration: 0.20, ease: "power2.inOut" }}, ct + 0.15);
                }}
              }});
            }}
          }});

          // Troca de pose intra-cena com squash & stretch
          poseCues.forEach(function (pc, pcIdx) {{
            var prevSlot = slots[pcIdx];
            var nextSlot = slots[pcIdx + 1];
            if (!prevSlot || !nextSlot) return;
            var prevRig = prevSlot.querySelector(".mascot-body-rig");
            var nextRig = nextSlot.querySelector(".mascot-body-rig");
            if (prevRig) {{
              tl.to(prevRig, {{ scaleX: 1.15, scaleY: 0.82, svgOrigin: "210 526", duration: 0.08, ease: "power2.in" }}, pc.time - 0.06);
            }}
            tl.set(prevSlot, {{ opacity: 0 }}, pc.time);
            tl.set(nextSlot, {{ opacity: 1 }}, pc.time);
            if (nextRig) {{
              tl.fromTo(nextRig,
                {{ scaleX: 1.20, scaleY: 0.78, y: 12, svgOrigin: "210 526" }},
                {{
                  keyframes: [
                    {{ scaleX: 0.94, scaleY: 1.07, y: -8, duration: 0.12, ease: "power2.out" }},
                    {{ scaleX: 1, scaleY: 1, y: 0, duration: 0.16, ease: "back.out(1.8)" }}
                  ],
                  ease: "none"
                }},
                pc.time
              );
            }}
          }});
        }})();"""
        )

    # Dynamic BGM envelope per scene (supports bgm_vol on scene)
    bgm_points: list[dict[str, Any]] = []
    for st in scene_timings:
        sc_vol = float(st["scene"].get("bgm_vol", 0.13))
        t_s = st["start"]
        t_e = round(st["start"] + st["duration"] - 0.06, 3)
        bgm_points.append({"t": t_s, "v": sc_vol})
        if t_e > t_s + 0.1:
            bgm_points.append({"t": t_e, "v": sc_vol})
    bgm_points.append({"t": round(total_duration, 3), "v": 0.02})
    bgm_automation = json.dumps(
        {
            "version": 1,
            "lanes": [
                {
                    "target": "volume",
                    "points": bgm_points,
                }
            ],
        }
    )

    return f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>{title}</title>
    <script src="{path_prefix}assets/vendor/gsap.min.js"></script>
    <style>
      @font-face {{
        font-family: "Sora";
        src: url("{path_prefix}assets/fonts/sora-400-latin.woff2") format("woff2");
        font-weight: 400;
        font-style: normal;
        font-display: swap;
      }}
      @font-face {{
        font-family: "Sora";
        src: url("{path_prefix}assets/fonts/sora-600-latin.woff2") format("woff2");
        font-weight: 600;
        font-style: normal;
        font-display: swap;
      }}
      @font-face {{
        font-family: "Sora";
        src: url("{path_prefix}assets/fonts/sora-700-latin.woff2") format("woff2");
        font-weight: 700;
        font-style: normal;
        font-display: swap;
      }}
      @font-face {{
        font-family: "Sora";
        src: url("{path_prefix}assets/fonts/sora-800-latin.woff2") format("woff2");
        font-weight: 800;
        font-style: normal;
        font-display: swap;
      }}
      * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }}
      html, body {{
        width: 100%;
        height: 100%;
        overflow: hidden;
        background: #0F1017;
        font-family: "Sora", sans-serif;
      }}
      #root {{
        position: relative;
        width: 100%;
        height: 100%;
        overflow: hidden;
        background: #0F1017;
      }}
      .scene {{
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        color: var(--ink);
      }}
      .scene-curtain, .scene-camera, .layer-bg {{
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
      }}
      .scene-camera {{
        transform-origin: 50% 48%;
      }}
      .scene-bg-wall {{
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 61.5%;
        background: var(--wall);
      }}
      .scene-bg-floor {{
        position: absolute;
        top: 61.5%;
        left: 0;
        right: 0;
        bottom: 0;
        background: var(--floor);
      }}
      .scene-horizon {{
        position: absolute;
        top: 61.5%;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--horizon);
        z-index: 5;
      }}
      .headline-zone {{
        position: absolute;
        top: 300px;
        left: 120px;
        right: 120px;
        z-index: 15;
      }}
      .headline-split {{
        display: flex;
        align-items: flex-start;
        gap: 24px;
      }}
      .split-col {{
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 10px;
      }}
      .split-divider {{
        width: 3px;
        height: 210px;
        border-radius: 2px;
        flex-shrink: 0;
      }}
      .hl-line, .hl-row {{
        font-size: 54px;
        font-weight: 800;
        line-height: 1.16;
        letter-spacing: -0.04em;
        color: var(--ink);
      }}
      .headline-split .hl-line {{
        font-size: 44px;
      }}
      .headline-stack {{
        display: flex;
        flex-direction: column;
        gap: 12px;
      }}
      .hl-row {{
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 14px;
      }}
      .rank-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 4px 20px;
        border-radius: 14px;
        font-size: 60px;
        font-weight: 800;
        line-height: 1.08;
      }}
      .hl-sweep-wrap {{
        position: relative;
        display: inline-block;
        padding: 4px 18px;
        border-radius: 14px;
        overflow: hidden;
        line-height: 1.14;
      }}
      .hl-pill-round {{
        border-radius: 999px;
        padding: 10px 28px;
        font-size: 44px;
      }}
      .hl-sweep-base {{
        position: relative;
        z-index: 1;
        display: inline-block;
      }}
      .hl-sweep-bar {{
        position: absolute;
        inset: 0;
        z-index: 2;
        border-radius: inherit;
        transform-origin: left center;
      }}
      .hl-sweep-fg {{
        position: absolute;
        inset: 0;
        z-index: 3;
        padding: inherit;
        display: inline-block;
        white-space: nowrap;
      }}
      .stage-prop {{
        position: absolute;
        left: 68px;
        top: 675px;
        width: 510px;
        height: 440px;
        z-index: 10;
        display: flex;
        align-items: flex-end;
        justify-content: center;
      }}
      .prop-svg {{
        width: 100%;
        height: 100%;
        overflow: visible;
      }}
      .mascot-wrap {{
        position: absolute;
        right: 44px;
        top: 678px;
        width: 460px;
        height: 620px;
        z-index: 20;
      }}
      .mascot-pose-slot {{
        position: absolute;
        inset: 0;
        display: flex;
        align-items: flex-end;
        justify-content: center;
      }}
      .mascot-svg, .mascot-png-sticker {{
        width: 100%;
        height: 100%;
        object-fit: contain;
        object-position: bottom center;
        overflow: visible;
      }}
      #captions-layer {{
        position: absolute;
        top: 1035px;
        left: 64px;
        right: 110px;
        height: 110px;
        z-index: 50;
        pointer-events: none;
      }}
      .caption-slot {{
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
      }}
      .caption-pill {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 12px 22px;
        border-radius: 20px;
        background: rgba(17, 19, 26, 0.94);
        border: 2px solid rgba(255, 255, 255, 0.16);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.34);
      }}
      .cap-word {{
        display: inline-block;
        font-size: 40px;
        font-weight: 700;
        line-height: 1.15;
        letter-spacing: -0.02em;
        color: #E2E6F0;
        padding: 4px 10px;
        border-radius: 10px;
      }}
    </style>
  </head>
  <body>
    <div
      id="root"
      data-composition-id="mgl-style"
      data-start="0"
      data-duration="{total_duration}"
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

      {''.join(scenes_html)}

      <div id="captions-layer" data-layout-allow-caption-zone="true">
        {''.join(captions_html)}
      </div>

      <audio
        id="bgm"
        src="{bgm_rel}"
        data-start="0"
        data-duration="{total_duration}"
        data-track-index="11"
        data-volume="0.14"
        data-automation='{bgm_automation}'
      ></audio>
      {''.join(audio_html)}
    </div>

    <script>
      (function () {{
        var tl = gsap.timeline({{ paused: true }});
        {''.join(timeline_js_blocks)}

        // Legenda dinamica palavra por palavra sincronizada com WordBoundary
        var capWords = document.querySelectorAll(".cap-word");
        capWords.forEach(function (el) {{
          var ws = parseFloat(el.getAttribute("data-w-start"));
          var we = parseFloat(el.getAttribute("data-w-end"));
          tl.to(el, {{
            backgroundColor: "#D0EB2F",
            color: "#11131A",
            scale: 1.07,
            duration: 0.05,
            ease: "power2.out"
          }}, ws);
          tl.to(el, {{
            backgroundColor: "rgba(208, 235, 47, 0)",
            color: "#E2E6F0",
            scale: 1,
            duration: 0.05,
            ease: "power2.in"
          }}, we);
        }});

        tl.set({{}}, {{}}, {total_duration});
        window.__timelines["mgl-style"] = tl;
      }})();
    </script>
  </body>
</html>
"""


async def build_all(only_slug: str | None = None, reuse: bool = False) -> None:
    cfg = json.loads((DATA_DIR / "batch_scripts.json").read_text(encoding="utf-8"))
    voice = cfg.get("voice", "pt-BR-AntonioNeural")
    rate = cfg.get("rate", "+18%")
    bgm_rel = cfg.get("bgm", "assets/audio/bgm.mp3")
    bgm_src = PROJECT_ROOT / bgm_rel

    COMPOSITIONS_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []

    videos = cfg.get("videos", [])
    has_primary = any(v.get("primary") for v in videos)
    for v_idx, video in enumerate(videos):
        slug = video["slug"]
        if only_slug and slug != only_slug:
            continue

        cursor = 0.0
        scene_timings: list[dict[str, Any]] = []
        v_default_voice = video.get("voice", voice)
        v_default_rate = video.get("rate", rate)
        for s_idx, sc in enumerate(video["scenes"]):
            mp3_path = AUDIO_GEN_DIR / slug / f"{s_idx:02d}_{sc['id']}.mp3"
            meta_path = AUDIO_GEN_DIR / slug / f"{s_idx:02d}_{sc['id']}.json"
            dur, words = await synthesize_scene(sc, v_default_voice, v_default_rate, mp3_path, meta_path, reuse=reuse)
            pad = 0.14 if s_idx + 1 < len(video["scenes"]) else 0.45
            scene_dur = round(dur + pad, 3)
            scene_start = round(cursor, 3)
            scene_end = round(scene_start + scene_dur, 3)
            chunks = group_caption_chunks(words, scene_start, scene_end)

            scene_timings.append(
                {
                    "scene": sc,
                    "start": scene_start,
                    "duration": scene_dur,
                    "audio_dur": dur,
                    "audio_rel": f"assets/audio/generated/{slug}/{mp3_path.name}",
                    "words": words,
                    "chunks": chunks,
                }
            )
            cursor = scene_end

        total_duration = round(cursor, 3)
        bgm_fit = ensure_looped_bgm(bgm_src, total_duration, AUDIO_GEN_DIR / slug / "bgm_fit.mp3")
        bgm_fit_rel = bgm_fit.relative_to(PROJECT_ROOT).as_posix()

        comp_timings = []
        for st in scene_timings:
            st_copy = dict(st)
            st_copy["audio_rel"] = "../" + st["audio_rel"]
            comp_timings.append(st_copy)

        comp_html = compile_video_html(
            video=video,
            scene_timings=comp_timings,
            total_duration=total_duration,
            bgm_rel="../" + bgm_fit_rel,
            path_prefix="../",
        )
        comp_path = COMPOSITIONS_DIR / f"{slug}.html"
        comp_path.write_text(comp_html, encoding="utf-8")

        if video.get("primary") or (not has_primary and v_idx == 0) or only_slug == slug:
            root_html = compile_video_html(
                video=video,
                scene_timings=scene_timings,
                total_duration=total_duration,
                bgm_rel=bgm_fit_rel,
                path_prefix="",
            )
            (PROJECT_ROOT / "index.html").write_text(root_html, encoding="utf-8")

        manifest.append(
            {
                "slug": slug,
                "title": video.get("title", slug),
                "composition": f"compositions/{slug}.html",
                "output": f"renders/{slug}.mp4",
                "duration_s": total_duration,
                "scenes": len(scene_timings),
            }
        )
        print(f"[OK] Built v2 {slug}: {len(scene_timings)} scenes, {total_duration}s -> {comp_path}")

    (DATA_DIR / "batch_manifest.json").write_text(
        json.dumps({"videos": manifest}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    reuse = "--reuse" in sys.argv[1:]
    only_slug = args[0] if args else None
    asyncio.run(build_all(only_slug=only_slug, reuse=reuse))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
