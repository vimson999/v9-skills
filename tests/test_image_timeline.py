"""Deterministic handoff checks using synthetic narration, not a quality benchmark."""

import copy
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/srt-visual-director/scripts/image_timeline.py"
spec = importlib.util.spec_from_file_location("image_timeline", SCRIPT)
timeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(timeline)
FIXTURES = ROOT / "tests/fixtures/image-director"


def plan():
    cues = timeline.parse_srt((FIXTURES / "narration.srt").read_text())["cues"]
    shots = []
    for i, cue in enumerate(cues):
        shots.append({
            "id": f"shot-{i + 1:03d}",
            "startMs": 0 if i == 0 else cue["startMs"],
            "endMs": cues[i + 1]["startMs"] if i + 1 < len(cues) else cue["endMs"],
            "voiceoverRefs": [cue["id"]], "voiceText": cue["text"],
            "timingBasis": "cue_boundary", "timingNote": "静音期间延续画面",
            "narrativeBeat": "解释物品位置与使用的关系", "visualIntent": "书桌前的人物与办公用品",
            "image": {"assetNeed": "独立的竖屏办公插画", "action": "generate",
                      "assetRef": None, "candidateIds": [],
                      "prompt": "一张独立9:16竖屏插画，浅蓝衬衫人物在暖白书桌前整理笔筒，深灰轮廓，原图无字，下部留白。",
                      "fallbackPrompt": None, "designBrief": None, "inImageText": [],
                      "overlay": {"title": "", "keywords": [], "labels": []},
                      "usage": {"crop": "完整画面", "motion": "轻微推近", "transition": "直接切换"}}
        })
    return {
        "profile": "image-v1", "project": {"id": "synthetic-desk", "title": "桌面整理"},
        "status": "ready", "timing": {"kind": "srt", "srtPath": "narration.srt", "startMs": 0, "endMs": 19000, "audioDurationMs": None},
        "style": {"aspectRatio": "9:16", "description": "暖白深灰线条配浅蓝", "referenceRefs": [], "textPolicy": "原图无字", "subtitleSafeArea": "下部", "confirmed": True},
        "assetLibrary": {"status": "not_provided", "source": None, "notes": []},
        "assumptions": [], "openQuestions": [], "shots": shots
    }, cues


class SrtTests(unittest.TestCase):
    def test_bom_crlf_multiline_and_decimal_separator(self):
        parsed = timeline.parse_srt("\ufeff7\r\n00:00:01.250 --> 00:00:03,500\r\n第一行\r\n第二行\r\n")
        self.assertEqual(parsed["cues"], [{"id": "srt-007", "startMs": 1250, "endMs": 3500, "text": "第一行\n第二行"}])

    def test_gaps_and_overlaps_are_retained(self):
        parsed = timeline.parse_srt("1\n00:00:00,000 --> 00:00:04,000\n甲\n\n2\n00:00:02,000 --> 00:00:03,000\n乙\n\n3\n00:00:06,000 --> 00:00:07,000\n丙")
        self.assertEqual(len(parsed["warnings"]), 2)
        self.assertEqual(parsed["lastCueEndMs"], 7000)

    def test_invalid_srt_is_rejected(self):
        for text in ("", "1\n00:61:00,000 --> 00:62:00,000\n甲", "1\n00:00:03,000 --> 00:00:02,000\n甲", "bad block"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                timeline.parse_srt(text)

    def test_duplicate_and_unsorted_cues_are_rejected(self):
        for number, start in ((1, "00:00:02,000"), (2, "00:00:00,000")):
            text = f"1\n00:00:01,000 --> 00:00:03,000\n甲\n\n{number}\n{start} --> 00:00:04,000\n乙"
            with self.subTest(number=number), self.assertRaises(ValueError):
                timeline.parse_srt(text)


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.plan, self.cues = plan()

    def errors(self):
        return timeline.validate_plan(self.plan, self.cues)

    def test_valid_plan_preserves_initial_and_internal_silence(self):
        self.assertEqual(self.errors(), [])
        self.assertEqual(self.plan["shots"][1]["endMs"], 11000)

    def test_independently_authored_storyboard_passes_handoff_checks(self):
        sample = timeline.load_plan(FIXTURES / "STORYBOARD.md")
        self.assertEqual(timeline.validate_plan(sample, self.cues), [])
        self.assertTrue(any(shot["image"]["action"] == "search_pending" for shot in sample["shots"]))

    def test_gap_overlap_and_wrong_tail_are_rejected(self):
        for delta in (-1, 1):
            with self.subTest(delta=delta):
                self.plan, self.cues = plan()
                self.plan["shots"][1]["startMs"] += delta
                self.assertTrue(self.errors())
        self.plan, self.cues = plan()
        self.plan["timing"]["endMs"] += 1000
        self.assertTrue(self.errors())

    def test_actual_srt_required(self):
        self.assertTrue(timeline.validate_plan(self.plan))

    def test_requested_presets_require_matching_snapshot(self):
        requested = dict(directing_profile="health-explainer", visual_style="warm-life-illustration")
        self.assertTrue(timeline.validate_plan(self.plan, self.cues, **requested))
        self.plan["direction"] = {
            "directingProfile": {"id": "health-explainer", "revision": 1, "source": "preset.yaml"},
            "visualStyle": {"id": "warm-life-illustration", "revision": 1, "source": "style.yaml"},
            "audience": "成年人", "overrides": [], "resolvedRules": ["保持项目画风和人物设定"]}
        self.assertEqual(timeline.validate_plan(self.plan, self.cues, **requested), [])
        for key in ("directingProfile", "visualStyle"):
            original = self.plan["direction"][key]
            for replacement in (None, dict(original, id="different-preset")):
                with self.subTest(key=key, replacement=replacement):
                    self.plan["direction"][key] = replacement
                    self.assertTrue(timeline.validate_plan(self.plan, self.cues, **requested))
            self.plan["direction"][key] = original

    def test_cli_checks_requested_presets_and_reports_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "STORYBOARD.json"
            path.write_text(json.dumps(self.plan))
            args = ["validate", str(path), "--srt", str(FIXTURES / "narration.srt")]
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = timeline.main(args + ["--visual-style", "warm-life-illustration"])
            result = json.loads(out.getvalue())
            self.assertEqual(code, 1)
            self.assertFalse(result["valid"])
            self.assertIn("visual_semantics", result["notChecked"])
            # Older, unconfigured projects still work without preset expectations.
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(timeline.main(args), 0)

    def test_wrong_missing_duplicate_cue_references(self):
        for refs in ([], ["srt-999"], ["srt-001", "srt-001"]):
            with self.subTest(refs=refs):
                self.plan["shots"][0]["voiceoverRefs"] = refs
                self.assertTrue(self.errors())

    def test_internal_cut_requires_honest_timing_basis(self):
        original = self.plan["shots"][0]
        second = copy.deepcopy(original)
        original["endMs"] = 3000
        second.update(id="shot-001b", startMs=3000)
        self.plan["shots"].insert(1, second)
        self.assertTrue(self.errors())
        for shot in (original, second):
            shot.update(timingBasis="estimated", timingNote="按语义估计，尚未核验音频")
        self.assertTrue(self.errors())  # Not ready while timing is estimated.
        self.plan.update(status="planned", openQuestions=["核对内部切点"])
        self.assertEqual(self.errors(), [])

    def test_untimed_draft_never_invents_times(self):
        self.plan.update(status="planned")
        self.plan["timing"].update(kind="untimed", srtPath=None, startMs=None, endMs=None)
        for shot in self.plan["shots"]:
            shot.update(startMs=None, endMs=None, voiceoverRefs=[], timingBasis="untimed")
        self.assertEqual(timeline.validate_plan(self.plan), [])
        self.plan["shots"][0]["startMs"] = 0
        self.assertTrue(timeline.validate_plan(self.plan))

    def test_reuse_requires_viewed_and_confirmed_asset(self):
        image = self.plan["shots"][0]["image"]
        image.update(action="reuse", prompt=None, assetRef={"assetId":"asset-desk-001", "source":"fixture-catalog", "version":None, "viewed":False, "useStatus":"unverified"})
        self.assertTrue(self.errors())
        image["assetRef"].update(viewed=True, useStatus="confirmed")
        self.assertEqual(self.errors(), [])
        image["assetRef"]["useStatus"] = "forbidden"
        self.assertTrue(self.errors())

    def test_pending_candidate_does_not_block_draft_or_masquerade_as_ready(self):
        image = self.plan["shots"][0]["image"]
        image.update(action="search_pending", prompt=None, candidateIds=["asset-desk-001"])
        self.assertTrue(self.errors())
        self.plan.update(status="planned", openQuestions=["查看候选并核对使用状态"])
        self.assertEqual(self.errors(), [])

    def test_new_images_need_prompts_and_cannot_have_fake_asset_ids(self):
        image = self.plan["shots"][0]["image"]
        image["prompt"] = " "
        self.assertTrue(self.errors())
        self.plan, self.cues = plan()
        self.plan["shots"][0]["image"]["assetRef"] = {"assetId":"fake", "source":"fake", "version":None, "viewed":True, "useStatus":"confirmed"}
        self.assertTrue(self.errors())

    def test_external_chart_requires_design_brief(self):
        image = self.plan["shots"][0]["image"]
        image.update(action="external_design", prompt=None)
        self.assertTrue(self.errors())
        image["designBrief"] = "用用户提供的表格绘制柱状图，保留原始单位和来源，不推测缺失数值。"
        self.assertEqual(self.errors(), [])

    def test_bad_shapes_fail_cleanly(self):
        for bad in (None, [], {}, {"profile": "other"}):
            self.assertTrue(timeline.validate_plan(bad, self.cues))
        self.plan["shots"][0]["startMs"] = True
        self.assertTrue(self.errors())

    def test_range_cannot_exceed_known_audio(self):
        self.plan["timing"]["audioDurationMs"] = 18000
        self.assertTrue(self.errors())

    def test_partial_range_keeps_absolute_times(self):
        self.plan["timing"].update(startMs=11000)
        self.plan["shots"] = self.plan["shots"][2:]
        self.assertEqual(self.errors(), [])

    def test_markdown_has_exactly_one_canonical_json_block(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "STORYBOARD.md"
            body = "```json\n" + json.dumps(self.plan) + "\n```\n"
            path.write_text("# Storyboard\n\n" + body)
            self.assertEqual(timeline.load_plan(path), self.plan)
            path.write_text(body + "\n" + body)
            with self.assertRaises(ValueError):
                timeline.load_plan(path)

    def test_schema_checker_supports_all_keywords_in_profile(self):
        allowed = {"$schema", "$id", "title", "description", "type", "const", "enum", "required", "properties", "additionalProperties", "items", "minItems", "minLength", "minimum", "pattern"}
        def visit(node):
            self.assertFalse(set(node) - allowed)
            for child in node.get("properties", {}).values():
                visit(child)
            if "items" in node:
                visit(node["items"])
        visit(json.loads(timeline.SCHEMA.read_text()))


if __name__ == "__main__":
    unittest.main()
