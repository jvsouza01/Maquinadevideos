from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def probe_media(path: Path) -> dict:
    cmd = ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def measure_lufs(path: Path) -> float | None:
    cmd = ["ffmpeg", "-nostats", "-i", str(path), "-filter_complex", "ebur128", "-f", "null", "-"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    matches = re.findall(r"I:\s*(-?\d+(?:\.\d+)?)\s*LUFS", res.stderr)
    return float(matches[-1]) if matches else None


def collect_media_targets() -> list[Path]:
    targets = [
        WORKSPACE_ROOT / "videos" / "whatsapp-reels" / "final_audio.wav",
        WORKSPACE_ROOT / "videos" / "whatsapp-reels" / "reels_black_friday_vistarumo.mp4",
        WORKSPACE_ROOT / "videos" / "relampeja-edit" / "relampeja_final.mp4",
    ]
    for pipeline in ("vistarumo-promo", "mgl-style-batch", "revenue-clean-pixar"):
        renders_dir = WORKSPACE_ROOT / "videos" / pipeline / "renders"
        if renders_dir.exists():
            targets.extend(sorted(renders_dir.glob("*.mp4")))
    return targets


def audit_media_artifacts() -> list[str]:
    has_ffprobe = shutil.which("ffprobe") is not None
    has_ffmpeg = shutil.which("ffmpeg") is not None
    targets = collect_media_targets()

    if not has_ffprobe or not has_ffmpeg:
        return ["SKIP media audit (ffprobe/ffmpeg not found in PATH)"]

    results: list[str] = []
    audited = 0
    for target in targets:
        if not target.exists():
            results.append(f"SKIP {target.relative_to(WORKSPACE_ROOT)} (not rendered locally)")
            continue
        meta = probe_media(target)
        duration = float(meta.get("format", {}).get("duration", 0))
        streams = meta.get("streams", [])
        v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
        lufs = measure_lufs(target) if a_stream else None
        res_str = f"{v_stream['width']}x{v_stream['height']}" if v_stream else "audio-only"
        lufs_str = f"{lufs:.1f} LUFS" if lufs is not None else "n/a"
        assert duration > 0, f"Invalid duration on {target}"
        results.append(f"OK {target.relative_to(WORKSPACE_ROOT)}: {res_str}, {duration:.2f}s, {lufs_str}")
        audited += 1

    if audited == 0:
        results.append("INFO no local rendered media found (clean clone mode)")
    return results


def main() -> int:
    scratch_dir = WORKSPACE_ROOT / "scratch"
    if scratch_dir.exists():
        scratch_files = list(scratch_dir.glob("*"))
        print(f"INFO scratch/ present ({len(scratch_files)} entries)")
    else:
        print("SKIP scratch/ not present (clean clone mode)")

    for line in audit_media_artifacts():
        print(line)

    unit_res = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=WORKSPACE_ROOT)
    if unit_res.returncode != 0:
        return unit_res.returncode

    wa_node_modules = WORKSPACE_ROOT / "videos" / "whatsapp-reels" / "node_modules"
    if not wa_node_modules.exists():
        print("SKIP whatsapp-reels frame test (run 'npm --prefix videos/whatsapp-reels install' first)")
    elif shutil.which("node") is None:
        print("SKIP whatsapp-reels frame test (node not found in PATH)")
    else:
        wa_res = subprocess.run(["node", "videos/whatsapp-reels/test_preview_frames.js"], cwd=WORKSPACE_ROOT)
        if wa_res.returncode != 0:
            return wa_res.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
