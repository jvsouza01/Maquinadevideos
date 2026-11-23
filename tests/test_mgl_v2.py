import sys
import unittest
from pathlib import Path

MGL_SCRIPTS = Path(__file__).resolve().parent.parent / "videos" / "mgl-style-batch" / "scripts"
if str(MGL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(MGL_SCRIPTS))

import cue_engine  # noqa: E402
import mascot_rig  # noqa: E402
import props_engine  # noqa: E402


class CueEngineTests(unittest.TestCase):
    def setUp(self):
        self.words = [
            {"text": "Se", "start": 0.1, "end": 0.2},
            {"text": "você", "start": 0.25, "end": 0.45},
            {"text": "sobe", "start": 0.5, "end": 0.72},
            {"text": "oferta", "start": 0.75, "end": 1.05},
            {"text": "no", "start": 1.1, "end": 1.2},
            {"text": "chute,", "start": 1.25, "end": 1.6},
            {"text": "torra", "start": 1.7, "end": 2.0},
            {"text": "grana.", "start": 2.05, "end": 2.4},
        ]

    def test_resolve_word_cue_exact_and_accent_insensitive(self):
        t_chute = cue_engine.resolve_word_cue(self.words, "chute", 0.5, scene_start=10.0, scene_dur=3.0)
        self.assertAlmostEqual(t_chute, 11.25, places=3)
        t_voce = cue_engine.resolve_word_cue(self.words, "voce", 0.5, scene_start=10.0, scene_dur=3.0)
        self.assertAlmostEqual(t_voce, 10.25, places=3)

    def test_resolve_word_cue_fallback(self):
        t_miss = cue_engine.resolve_word_cue(self.words, "inexistente", 0.4, scene_start=5.0, scene_dur=2.5)
        self.assertAlmostEqual(t_miss, 6.0, places=3)

    def test_caption_chunks_never_overlap(self):
        chunks = cue_engine.group_caption_chunks(self.words, scene_start=0.0, scene_end=2.8)
        self.assertGreaterEqual(len(chunks), 2)
        for i in range(len(chunks) - 1):
            cur_end = chunks[i]["start"] + chunks[i]["duration"]
            nxt_start = chunks[i + 1]["start"]
            self.assertLess(cur_end, nxt_start)


class MascotRigAndPropsTests(unittest.TestCase):
    def test_inline_rig_has_articulated_layers_and_unique_ids(self):
        svg_a = mascot_rig.render_inline_mascot_rig("confident", uid="0-0-confident")
        svg_b = mascot_rig.render_inline_mascot_rig("shock", uid="1-0-shock")
        for cls in (
            "mascot-shadow",
            "mascot-body-rig",
            "mascot-head-rig",
            "mascot-eyelids",
            "mascot-mouth",
            "mascot-arm-l",
            "mascot-arm-r",
        ):
            self.assertIn(cls, svg_a)
        self.assertIn('id="st-0-0-confident-skin"', svg_a)
        self.assertIn('id="st-1-0-shock-skin"', svg_b)

    def test_dynamic_props_emit_cue_attributes(self):
        cards = props_engine.render_prop(
            "cards_stack",
            "light",
            {"items": [{"title": "A", "badge": "10k", "cue_word": "dez"}]},
        )
        self.assertIn('data-cue-step="1"', cards)
        self.assertIn('data-cue-word="dez"', cards)

        flow = props_engine.render_prop("flow_steps", "dark", {})
        self.assertIn("cue-stroke-draw", flow)

        chart = props_engine.render_prop("bar_chart", "lime", {})
        self.assertIn("cue-count-up", chart)
        self.assertIn('data-cue-anim="grow-y"', chart)

        metrics = props_engine.render_prop("metrics_board", "dark", {})
        self.assertIn("cue-count-up", metrics)

    def test_marina_rig_and_story_props(self):
        marina = mascot_rig.render_inline_mascot_rig("marina_clutch", uid="m-0")
        self.assertIn("mascot-body-rig", marina)
        self.assertIn("mascot-mouth", marina)
        elev = props_engine.render_prop("elevator_incident", "dark", {})
        self.assertIn('data-cue-step="2"', elev)
        rc = props_engine.render_prop("revenue_clean_showcase", "lime", {})
        self.assertIn("REVENUE", rc)
        self.assertIn("Saiba mais", rc)


if __name__ == "__main__":
    unittest.main()
