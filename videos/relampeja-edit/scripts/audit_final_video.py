from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path
from PIL import Image

from common import RELAMPEJA_DIR

TIMESTAMPS = [
    (1.5, "Panel 1 (Prof Anderson / Relampeja)"),
    (6.0, "Panel 2 + Card 1 (Aulas Hibridas / Estudos)"),
    (10.0, "Panel 3 (Inicio 10/11)"),
    (16.5, "Panel 5 + Card 2 (Guarda Municipal Salvador)"),
    (18.5, "Panel 5 + Card 3 (Agente Transito Catu)"),
    (20.5, "Panel 5 + Card 4 (Agente Transito Lauro de Freitas)"),
    (22.5, "Panel 5 + Card 5 (PRF)"),
    (26.0, "Panel 6 + Card 6 (O Segredo da Aprovacao)"),
]


def probe_media(video_path: Path) -> dict:
    cmd = ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(video_path)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)
    streams = data.get("streams", [])
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float(data.get("format", {}).get("duration", 0))
    return {"video": v_stream, "audio": a_stream, "duration": duration}


def measure_lufs(media_path: Path) -> float | None:
    cmd = ["ffmpeg", "-nostats", "-i", str(media_path), "-filter_complex", "ebur128", "-f", "null", "-"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    matches = re.findall(r"I:\s*(-?\d+(?:\.\d+)?)\s*LUFS", res.stderr)
    return float(matches[-1]) if matches else None


def audit_video(video_path: Path = RELAMPEJA_DIR / "relampeja_final.mp4") -> dict:
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    meta = probe_media(video_path)
    assert meta["video"] is not None, "Missing video stream"
    assert meta["audio"] is not None, "Missing audio stream"
    assert meta["video"]["width"] == 1080 and meta["video"]["height"] == 1920, (
        f"Unexpected resolution: {meta['video']['width']}x{meta['video']['height']}"
    )
    assert 29.0 <= meta["duration"] <= 31.5, f"Unexpected duration: {meta['duration']:.2f}s"

    lufs = measure_lufs(video_path)
    assert lufs is not None, "Failed to measure LUFS"

    panel_checks = []
    with tempfile.TemporaryDirectory(prefix="relampeja_audit_") as tmp_dir:
        for t, desc in TIMESTAMPS:
            frame_path = Path(tmp_dir) / f"frame_{t:.1f}s.png"
            subprocess.run(
                ["ffmpeg", "-y", "-ss", str(t), "-i", str(video_path), "-frames:v", "1", str(frame_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            img = Image.open(frame_path).convert("RGB")
            p_center = img.getpixel((120, 180))
            c_banner = img.getpixel((820, 1110))
            is_panel_navy = p_center[0] < 45 and p_center[1] < 55 and p_center[2] < 75
            is_card_navy = (
                c_banner[0] < 45 and c_banner[1] < 55 and c_banner[2] < 75
                if t in [6.0, 16.5, 18.5, 20.5, 22.5, 26.0]
                else None
            )
            assert is_panel_navy, f"Panel check failed at t={t}s ({desc}): RGB{p_center}"
            if is_card_navy is False:
                raise AssertionError(f"Card banner check failed at t={t}s ({desc}): RGB{c_banner}")
            panel_checks.append((t, is_panel_navy, is_card_navy))

    return {
        "path": str(video_path),
        "duration": meta["duration"],
        "resolution": f"{meta['video']['width']}x{meta['video']['height']}",
        "lufs": lufs,
        "frames_checked": len(panel_checks),
    }


if __name__ == "__main__":
    summary = audit_video()
    print(f"PASS audit: {summary}")
