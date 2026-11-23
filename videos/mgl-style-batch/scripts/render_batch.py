"""Renderiza em massa todas as composições compiladas em data/batch_manifest.json."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "data" / "batch_manifest.json"


def resolve_npx() -> str:
    return shutil.which("npx") or ("npx.cmd" if os.name == "nt" else "npx")


def main() -> int:
    only_slug = sys.argv[1] if len(sys.argv) > 1 else None
    quality = sys.argv[2] if len(sys.argv) > 2 else "looks"
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    npx_bin = resolve_npx()
    for row in manifest.get("videos", []):
        slug = row["slug"]
        if only_slug and slug != only_slug:
            continue
        comp = row["composition"]
        out = row["output"]
        print(f"Rendering {slug} ({comp} -> {out})...")
        cmd = [
            npx_bin,
            "--yes",
            "hyperframes@0.9.77",
            "render",
            "--composition",
            comp,
            "--output",
            out,
            "--quality",
            quality,
        ]
        res = subprocess.run(cmd, cwd=PROJECT_ROOT, shell=False)
        if res.returncode != 0:
            print(f"[FAIL] {slug} exited with {res.returncode}")
            return res.returncode
        print(f"[DONE] {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
