from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "videos" / "whatsapp-reels"))
sys.path.insert(0, str(WORKSPACE_ROOT / "videos" / "relampeja-edit" / "scripts"))

import build_audio as wa_audio  # noqa: E402
import build_master_video as rel_master  # noqa: E402
import build_subtitles as rel_subs  # noqa: E402
import common as rel_common  # noqa: E402


class WhatsAppAudioFilterGraphTests(unittest.TestCase):
    def test_uses_asplit_and_disable_amix_normalize(self) -> None:
        fc = wa_audio.build_filter_complex()
        self.assertIn("[1:a]asplit=", fc)
        self.assertIn("[2:a]asplit=", fc)
        self.assertIn("[4:a]asplit=", fc)
        self.assertEqual(fc.count("[1:a]"), 1)
        self.assertEqual(fc.count("[2:a]"), 1)
        self.assertEqual(fc.count("[4:a]"), 1)
        self.assertIn("normalize=0", fc)
        self.assertIn("loudnorm=I=-14:TP=-1.5:LRA=11", fc)

    def test_key_times_within_typing_windows(self) -> None:
        keys = wa_audio.compute_key_times()
        self.assertGreater(len(keys), 20)
        for kt in keys:
            self.assertTrue(
                any(start < kt < end for start, end in wa_audio.TYPING_WINDOWS),
                f"Key time {kt} outside typing windows",
            )


class RelampejaPipelineTests(unittest.TestCase):
    def test_format_ass_time(self) -> None:
        self.assertEqual(rel_subs.format_ass_time(0.04), "0:00:00.04")
        self.assertEqual(rel_subs.format_ass_time(65.5), "0:01:05.50")

    def test_scale_caption_groups_by_speed_factor(self) -> None:
        raw = [[("FALA", 1.15, 2.30), ("GALERA", 2.30, 3.45)]]
        scaled = rel_subs.scale_caption_groups(raw, speed_factor=1.15, source_is_unscaled=True)
        self.assertEqual(scaled[0][0], ("FALA", 1.0, 2.0))
        self.assertEqual(scaled[0][1], ("GALERA", 2.0, 3.0))

    def test_load_transcript_json_maps_segments_and_speed(self) -> None:
        payload = {
            "words": [
                {"text": "Fala", "start": 0.60, "end": 1.75},
                {"text": "galera!", "start": 1.75, "end": 2.90},
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "transcript.json"
            p.write_text(json.dumps(payload), encoding="utf-8")
            groups = rel_subs.load_groups_from_transcript_json(p, speed_factor=1.15)
            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0][0], ("FALA", 0.0, 1.0))
            self.assertEqual(groups[0][1], ("GALERA!", 1.0, 2.0))
            ass_text = rel_subs.build_ass_content(groups)
            self.assertIn("Dialogue: 0,0:00:00.00,0:00:01.00", ass_text)

    def test_master_video_filter_has_sidechain_ducking_and_loudnorm(self) -> None:
        fc = rel_master.build_filter_complex(subtitles_ass=Path("videos/relampeja-edit/assets/captions.ass"))
        self.assertIn("asplit=2[voicetrack][voice_sc]", fc)
        self.assertIn("sidechaincompress=", fc)
        self.assertIn("loudnorm=I=-14:TP=-1.5:LRA=11", fc)
        self.assertIn("normalize=0", fc)

    def test_common_asset_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            assets_dir = root / "relampeja" / "assets"
            relampeja_dir = root / "relampeja"
            scratch_dir = root / "scratch"
            assets_dir.mkdir(parents=True)
            scratch_dir.mkdir(parents=True)

            local_img = assets_dir / "estudos.jpg"
            local_img.write_bytes(b"img")
            scratch_img = scratch_dir / "estudos.jpg"
            scratch_img.write_bytes(b"scratch-img")
            scratch_bgm = scratch_dir / "track_unstoppable.mp3"
            scratch_bgm.write_bytes(b"mp3")

            with mock.patch.multiple(
                rel_common,
                ASSETS_DIR=assets_dir,
                RELAMPEJA_DIR=relampeja_dir,
                WORKSPACE_ROOT=root,
                SCRATCH_DIR=scratch_dir,
            ):
                self.assertEqual(rel_common.resolve_asset("estudos.jpg"), local_img)
                self.assertEqual(rel_common.resolve_asset("track_unstoppable.mp3"), scratch_bgm)
                missing = rel_common.resolve_asset("inexistente.png")
                self.assertEqual(missing, assets_dir / "inexistente.png")
                self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
