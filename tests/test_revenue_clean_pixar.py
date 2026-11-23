import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
PIXAR_SCRIPTS = ROOT / "videos" / "revenue-clean-pixar" / "scripts"
if str(PIXAR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PIXAR_SCRIPTS))

import build_scenes as bs


class HybridPixarMediaTests(unittest.TestCase):
    def test_video_first_when_clip_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "shot_1a.mp4").write_bytes(b"fake-mp4")
            tag, is_video = bs.render_shot_media("shot_1a", 0.0, 5.4, playback_rate=0.90, clips_dir=Path(tmp))
        self.assertTrue(is_video)
        self.assertIn("<video ", tag)
        self.assertIn('src="assets/clips/shot_1a.mp4"', tag)
        self.assertIn("muted", tag)
        self.assertIn("playsinline", tag)
        self.assertIn('data-start="0.0"', tag)
        self.assertIn('data-duration="5.4"', tag)
        self.assertIn('data-playback-rate="0.9"', tag)
        self.assertNotIn('class="clip"', tag)

    def test_image_fallback_when_clip_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tag, is_video = bs.render_shot_media("shot_2b", 3.0, 4.3, clips_dir=Path(tmp))
            self.assertFalse(is_video)
            self.assertIn("<img ", tag)
            self.assertIn('src="assets/shots/shot_2b_phone_ots.jpg"', tag)

    def test_scene_04_tracks_bottle_label_on_video(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "shot_4a.mp4").write_bytes(b"fake-mp4")
            (Path(tmp) / "shot_4b.mp4").write_bytes(b"fake-mp4")
            with mock.patch.object(bs, "CLIPS_DIR", Path(tmp)):
                html_out = bs.build_scene_04(13.2)
        self.assertIn('id="vid-shot_4a"', html_out)
        self.assertIn('id="vid-shot_4b"', html_out)
        self.assertIn('data-playback-rate="0.65"', html_out)
        self.assertIn('id="rc-label-group"', html_out)
        self.assertIn("Saiba mais", html_out)


if __name__ == "__main__":
    unittest.main()
