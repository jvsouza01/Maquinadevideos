from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Sequence

from common import ASSETS_DIR

ASS_HEADER = """[Script Info]
Title: Relampeja Dynamic Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Segoe UI,56,&H00FFFFFF,&H0000CCFF,&H002C190B,&H80000000,-1,-1,0,0,100,100,1,0,1,5.5,3.0,2,60,60,200,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# Fallback dataset in accelerated (1.15x) timeline seconds when no transcript JSON is supplied
DEFAULT_CAPTION_GROUPS: list[list[tuple[str, float, float]]] = [
    [("FALA", 0.04, 0.35), ("MINHA", 0.35, 0.65), ("GALERA,", 0.65, 1.10), ("\\nTUDO", 1.10, 1.35), ("BELEZA?", 1.35, 1.65)],
    [("AQUI", 1.65, 1.95), ("QUEM", 1.95, 2.15), ("FALA", 2.15, 2.45), ("É", 2.45, 2.60), ("O", 2.60, 2.75), ("PROFESSOR", 2.75, 3.15), ("\\nANDERSON", 3.15, 3.45), ("CLAYTON,", 3.45, 3.75)],
    [("MAIS", 3.75, 4.00), ("CONHECIDO", 4.00, 4.35), ("COMO", 4.35, 4.60), ("\\nRELAMPEJA!", 4.60, 4.95)],
    [("VENHO", 5.15, 5.50), ("CONVIDAR", 5.50, 5.85), ("VOCÊ", 5.85, 6.20), ("A", 6.20, 6.35), ("\\nVIR", 6.35, 6.55), ("DESCOBRIR", 6.55, 6.85), ("COMIGO", 6.85, 7.10)],
    [("O", 7.10, 7.25), ("SEGREDO", 7.25, 7.75), ("DA", 7.75, 7.95), ("\\nAPROVAÇÃO", 7.95, 8.60)],
    [("A", 8.60, 8.80), ("PARTIR", 8.80, 9.15), ("DO", 9.15, 9.35), ("DIA", 9.35, 9.65), ("10/11", 9.65, 10.45), ("\\nÀS", 10.45, 10.75), ("19:00", 10.75, 12.00)],
    [("AS", 12.45, 12.70), ("AULAS", 12.70, 13.05), ("VÃO", 13.05, 13.35), ("SER", 13.35, 13.65), ("\\nHÍBRIDAS,", 13.65, 14.25), ("BELEZA?", 14.25, 14.85)],
    [("PARA", 14.90, 15.20), ("OS", 15.20, 15.35), ("SEGUINTES", 15.35, 15.75), ("\\nCONCURSOS:", 15.75, 16.20)],
    [("SALVADOR", 16.25, 16.90), ("\\nGUARDA", 16.90, 17.40), ("MUNICIPAL,", 17.40, 18.05)],
    [("AGENTE", 18.10, 18.50), ("DE", 18.50, 18.65), ("TRÂNSITO", 18.65, 19.15), ("\\nDE", 19.15, 19.35), ("CATU,", 19.35, 20.05)],
    [("AGENTE", 20.05, 20.40), ("DE", 20.40, 20.55), ("TRÂNSITO", 20.55, 21.05), ("\\nDE", 21.05, 21.20), ("LAURO", 21.20, 21.65), ("DE", 21.65, 21.80), ("FREITAS", 21.80, 22.20)],
    [("E", 22.20, 22.35), ("PARA", 22.35, 22.60), ("O", 22.60, 22.75), ("CONCURSO", 22.75, 23.25), ("DA", 23.25, 23.40), ("\\nPOLÍCIA", 23.40, 23.85), ("RODOVIÁRIA", 23.85, 24.35), ("FEDERAL.", 24.35, 24.90)],
    [("ISSO", 24.95, 25.20), ("MESMO!", 25.20, 25.50), ("\\nVENHA", 25.50, 25.75), ("COMIGO", 25.75, 26.05), ("DESCOBRIR", 26.05, 26.35)],
    [("O", 26.35, 26.50), ("SEGREDO", 26.50, 26.85), ("DA", 26.85, 27.00), ("\\nAPROVAÇÃO.", 27.00, 27.30)],
    [("UM", 27.30, 27.50), ("FORTE", 27.50, 27.80), ("ABRAÇO", 27.80, 28.20), ("\\nE", 28.20, 28.30), ("NÃO", 28.30, 28.50), ("ESQUEÇA:", 28.50, 28.80)],
    [("⚡", 28.80, 29.10), ("RELAMPEJA!", 29.10, 30.05)],
]

DEFAULT_TRIM_SEGMENTS: list[tuple[float, float]] = [
    (0.60, 17.70),
    (18.25, 19.82),
    (20.55, 22.70),
    (23.15, 36.85),
]


def format_ass_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def map_source_time_to_edited(
    source_sec: float,
    segments: Sequence[tuple[float, float]] = DEFAULT_TRIM_SEGMENTS,
    speed_factor: float = 1.15,
) -> float | None:
    """Map an original transcript timestamp through trim/concat segments and speed_factor."""
    if speed_factor <= 0:
        raise ValueError("speed_factor must be positive")
    concat_offset = 0.0
    for seg_start, seg_end in segments:
        if seg_start <= source_sec <= seg_end:
            return round((concat_offset + (source_sec - seg_start)) / speed_factor, 3)
        concat_offset += seg_end - seg_start
    return None


def scale_caption_groups(
    groups: Iterable[Sequence[tuple[str, float, float]]],
    speed_factor: float = 1.15,
    source_is_unscaled: bool = True,
    segments: Sequence[tuple[float, float]] | None = None,
) -> list[list[tuple[str, float, float]]]:
    """Scale or map word-level groups by speed_factor (and optional trim segments)."""
    if speed_factor <= 0:
        raise ValueError("speed_factor must be positive")
    scaled: list[list[tuple[str, float, float]]] = []
    for group in groups:
        out_group: list[tuple[str, float, float]] = []
        for word, start, end in group:
            if not source_is_unscaled:
                out_group.append((word, round(start, 3), round(end, 3)))
                continue
            if segments:
                mapped_s = map_source_time_to_edited(start, segments, speed_factor)
                mapped_e = map_source_time_to_edited(end, segments, speed_factor)
                if mapped_s is None or mapped_e is None:
                    continue
                out_group.append((word, mapped_s, max(mapped_s + 0.02, mapped_e)))
            else:
                out_group.append((word, round(start / speed_factor, 3), round(end / speed_factor, 3)))
        if out_group:
            scaled.append(out_group)
    return scaled


def load_groups_from_transcript_json(
    transcript_path: Path,
    speed_factor: float = 1.15,
    max_words_per_group: int = 5,
    segments: Sequence[tuple[float, float]] | None = DEFAULT_TRIM_SEGMENTS,
) -> list[list[tuple[str, float, float]]]:
    """Load word-level timestamps from JSON ({words:[...]} or list of segments/groups)."""
    data = json.loads(transcript_path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "groups" in data:
        raw_groups = [
            [(w["text"], float(w["start"]), float(w["end"])) for w in grp]
            for grp in data["groups"]
        ]
        return scale_caption_groups(raw_groups, speed_factor=speed_factor, source_is_unscaled=True, segments=segments)

    words = data["words"] if isinstance(data, dict) else data
    raw_groups: list[list[tuple[str, float, float]]] = []
    buf: list[tuple[str, float, float]] = []
    for idx, w in enumerate(words):
        text = str(w["text"]).strip().upper()
        if idx > 0 and len(buf) == 3:
            text = "\\n" + text
        buf.append((text, float(w["start"]), float(w["end"])))
        if len(buf) >= max_words_per_group or str(w["text"]).endswith((".", "!", "?", ",")):
            raw_groups.append(buf)
            buf = []
    if buf:
        raw_groups.append(buf)
    return scale_caption_groups(raw_groups, speed_factor=speed_factor, source_is_unscaled=True, segments=segments)


def build_ass_content(caption_groups: Sequence[Sequence[tuple[str, float, float]]]) -> str:
    events: list[str] = []
    for group in caption_groups:
        for active_idx, (_, w_start, w_end) in enumerate(group):
            line_parts: list[str] = []
            for i, (word, _, _) in enumerate(group):
                if word.startswith("\\n"):
                    clean_word = word[2:]
                    prefix = "\\N"
                else:
                    clean_word = word
                    prefix = " " if i > 0 and not group[i - 1][0].startswith("\\n") else ""

                if i == active_idx:
                    line_parts.append(f"{prefix}{{\\c&H0000CCFF&}}{clean_word}{{\\c&H00FFFFFF&}}")
                else:
                    line_parts.append(f"{prefix}{clean_word}")

            full_text = "".join(line_parts).strip()
            events.append(f"Dialogue: 0,{format_ass_time(w_start)},{format_ass_time(w_end)},Default,,0,0,0,,{full_text}")
    return ASS_HEADER + "\n".join(events) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ASS karaoke captions for relampeja-edit.")
    parser.add_argument("--transcript", type=Path, default=None, help="Optional word-level transcript JSON.")
    parser.add_argument("--speed-factor", type=float, default=1.15, help="Playback speed multiplier (default 1.15).")
    parser.add_argument("--output", type=Path, default=ASSETS_DIR / "captions.ass", help="Output .ass path.")
    args = parser.parse_args()

    if args.transcript and args.transcript.exists():
        groups = load_groups_from_transcript_json(args.transcript, speed_factor=args.speed_factor)
    else:
        groups = scale_caption_groups(DEFAULT_CAPTION_GROUPS, speed_factor=args.speed_factor, source_is_unscaled=False)

    ass_content = build_ass_content(groups)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(ass_content, encoding="utf-8")
    print(f"Generated {len(groups)} groups in {args.output}")


if __name__ == "__main__":
    main()
