from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Sequence

from common import ASSETS_DIR, CARDS_DIR, PANELS_DIR, RELAMPEJA_DIR, WORKSPACE_ROOT, resolve_asset

DEFAULT_SPEED_FACTOR = 1.15
DEFAULT_DURATION = 30.05

PANEL_FILENAMES = [f"panel_{i}.png" for i in range(1, 7)]
CARD_FILENAMES = [
    "card_1_estudos.png",
    "card_2_salvador.png",
    "card_3_catu.png",
    "card_4_lauro.png",
    "card_5_prf.png",
    "card_6_aprovacao.png",
]


def _escape_ffmpeg_filter_path(path: Path) -> str:
    """Escape path for FFmpeg subtitles filter on Windows/POSIX."""
    return str(path).replace("\\", "/").replace(":", "\\:")


def build_filter_complex(
    subtitles_ass: Path,
    speed_factor: float = DEFAULT_SPEED_FACTOR,
    duration: float = DEFAULT_DURATION,
) -> str:
    fc: list[str] = []

    # 1. Video and audio cuts + speed_factor
    fc.append("[0:v]trim=0.60:17.70,setpts=PTS-STARTPTS[v1];")
    fc.append("[0:a]atrim=0.60:17.70,asetpts=PTS-STARTPTS[a1];")
    fc.append("[0:v]trim=18.25:19.82,setpts=PTS-STARTPTS[v2];")
    fc.append("[0:a]atrim=18.25:19.82,asetpts=PTS-STARTPTS[a2];")
    fc.append("[0:v]trim=20.55:22.70,setpts=PTS-STARTPTS[v3];")
    fc.append("[0:a]atrim=20.55:22.70,asetpts=PTS-STARTPTS[a3];")
    fc.append("[0:v]trim=23.15:36.85,setpts=PTS-STARTPTS[v4];")
    fc.append("[0:a]atrim=23.15:36.85,asetpts=PTS-STARTPTS[a4];")
    fc.append("[v1][a1][v2][a2][v3][a3][v4][a4]concat=n=4:v=1:a=1[vcat][acat];")
    fc.append(f"[vcat]setpts=PTS/{speed_factor}[vspeed];")
    fc.append(f"[acat]atempo={speed_factor},volume=1.05,asplit=2[voicetrack][voice_sc];")

    # 2. Image grading & scaling to 1080x1920
    fc.append("[vspeed]scale=1080:1920:flags=lanczos,eq=contrast=1.08:brightness=-0.04:saturation=1.05,unsharp=5:5:0.8:5:5:0.0[vgrade];")

    # 3. Dynamic Punch-ins (1.05x in key emphasis moments)
    punch_expr = "between(t, 0.0, 2.0) + between(t, 6.8, 8.8) + between(t, 25.0, 27.0) + between(t, 28.5, 30.1)"
    fc.append(
        f"[vgrade]crop=w='if({punch_expr}, 1028, 1080)':h='if({punch_expr}, 1828, 1920)':"
        f"x='if({punch_expr}, 26, 0)':y='if({punch_expr}, 30, 0)',scale=1080:1920:flags=lanczos[vpunch];"
    )

    # 4. Fade filters on Panels (Inputs 3 to 8)
    panel_windows = [
        (0.2, 4.8),
        (5.2, 8.6),
        (8.9, 12.1),
        (12.4, 14.9),
        (15.2, 24.7),
        (25.0, 29.8),
    ]
    for idx, (st, out_st) in enumerate(panel_windows, start=1):
        fc.append(f"[{idx + 2}:v]format=rgba,fade=t=in:st={st}:d=0.25:alpha=1,fade=t=out:st={out_st}:d=0.25:alpha=1[p{idx}];")

    # 5. Fade filters on Cards (Inputs 9 to 14)
    card_windows = [
        (5.5, 8.3),
        (16.2, 17.8),
        (18.1, 19.8),
        (20.1, 21.9),
        (22.2, 24.6),
        (25.2, 27.3),
    ]
    for idx, (st, out_st) in enumerate(card_windows, start=1):
        fc.append(f"[{idx + 8}:v]format=rgba,fade=t=in:st={st}:d=0.25:alpha=1,fade=t=out:st={out_st}:d=0.25:alpha=1[c{idx}];")

    # 6. Overlays cascade with eof_action=pass
    panel_spans = [(0.2, 5.05), (5.2, 8.85), (8.9, 12.35), (12.4, 15.15), (15.2, 24.95), (25.0, 30.05)]
    prev = "vpunch"
    for idx, (st, end) in enumerate(panel_spans, start=1):
        nxt = f"o{idx}"
        fc.append(f"[{prev}][p{idx}]overlay=0:0:enable='between(t,{st},{end})':eof_action=pass[{nxt}];")
        prev = nxt

    card_spans = [(5.5, 8.55), (16.2, 18.05), (18.1, 20.05), (20.1, 22.15), (22.2, 24.85), (25.2, 27.55)]
    for idx, (st, end) in enumerate(card_spans, start=1):
        nxt = f"oc{idx}"
        fc.append(f"[{prev}][c{idx}]overlay=0:0:enable='between(t,{st},{end})':eof_action=pass[{nxt}];")
        prev = nxt

    # 7. Subtitles and Animated Bottom Progress Bar
    sub_escaped = _escape_ffmpeg_filter_path(subtitles_ass)
    fc.append(
        f"[{prev}]subtitles='{sub_escaped}',"
        "drawbox=x=0:y=1912:w=1080:h=8:color=0x0b192c@1:t=fill,"
        f"drawbox=x=0:y=1912:w='min(1080, (t/{duration})*1080)':h=8:color=0xffcc00@1:t=fill[vout];"
    )

    # 8. Audio Shutter SFX at each card entrance
    sfx_times_ms = [5500, 16200, 18100, 20100, 22200, 25200]
    fc.append("[2:a]asplit=6[sfx1][sfx2][sfx3][sfx4][sfx5][sfx6];")
    for idx, ms in enumerate(sfx_times_ms, start=1):
        fc.append(f"[sfx{idx}]adelay={ms}|{ms}[d{idx}];")
    fc.append("[d1][d2][d3][d4][d5][d6]amix=inputs=6:dropout_transition=0:normalize=0,volume=0.85[allsfx];")

    # 9. BGM Track with sidechaincompress ducking under voiceover
    fc.append(
        f"[1:a]atrim=0:{duration + 0.05:.2f},asetpts=PTS-STARTPTS,volume=0.28,"
        "afade=t=in:st=0:d=0.5,afade=t=out:st=28.5:d=1.5[bgm_raw];"
    )
    fc.append(
        "[bgm_raw][voice_sc]sidechaincompress=threshold=0.025:ratio=6:attack=20:release=250:makeup=1[bgm_ducked];"
    )

    # 10. Master Audio Mix (Voice + Ducked BGM + SFX) + EBU R128 loudness normalization
    fc.append(
        "[voicetrack][bgm_ducked][allsfx]amix=inputs=3:duration=first:dropout_transition=2:normalize=0,"
        "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]"
    )
    return "".join(fc)


def build_command(
    input_orig: Path | None = None,
    bgm_track: Path | None = None,
    sfx_shutter: Path | None = None,
    panels: Sequence[Path] | None = None,
    cards: Sequence[Path] | None = None,
    subtitles_ass: Path | None = None,
    output_final: Path | None = None,
) -> list[str]:
    input_orig = input_orig or resolve_asset("relampeja.mp4", fallback_to_scratch=False)
    if not input_orig.exists():
        input_orig = WORKSPACE_ROOT / "relampeja.mp4"
    bgm_track = bgm_track or resolve_asset("track_unstoppable.mp3", fallback_to_scratch=True)
    sfx_shutter = sfx_shutter or resolve_asset("sfx_shutter.wav")
    panels = list(panels) if panels else [PANELS_DIR / name for name in PANEL_FILENAMES]
    cards = list(cards) if cards else [CARDS_DIR / name for name in CARD_FILENAMES]
    subtitles_ass = subtitles_ass or (ASSETS_DIR / "captions.ass")
    output_final = output_final or (RELAMPEJA_DIR / "relampeja_final.mp4")

    filter_complex_str = build_filter_complex(subtitles_ass=subtitles_ass)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_orig),
        "-i", str(bgm_track),
        "-i", str(sfx_shutter),
    ]
    for p in panels:
        cmd.extend(["-loop", "1", "-i", str(p)])
    for c in cards:
        cmd.extend(["-loop", "1", "-i", str(c)])

    cmd.extend([
        "-filter_complex", filter_complex_str,
        "-map", "[vout]",
        "-map", "[aout]",
        "-t", str(DEFAULT_DURATION),
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "256k",
        "-movflags", "+faststart",
        str(output_final),
    ])
    return cmd


def main() -> None:
    cmd = build_command()
    print(f"Executing master render pipeline to {cmd[-1]}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Master render error:")
        print(res.stderr[-2000:])
        raise SystemExit(res.returncode)
    print("Master render SUCCESS!")


if __name__ == "__main__":
    main()
