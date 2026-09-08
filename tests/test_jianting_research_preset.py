"""Policy checks for the optional jianting-research production variant."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PRESET = (
    ROOT
    / "skills/srt-visual-director/references/presets/directing/jianting-research.yaml"
)


def mapping_block(text: str, key: str, indent: int) -> str | None:
    """Return a YAML mapping block without depending on a YAML package."""
    prefix = " " * indent
    match = re.search(rf"(?m)^{re.escape(prefix + key)}:\s*$", text)
    if match is None:
        return None
    lines = text[match.end() :].splitlines()
    kept = []
    for line in lines:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        kept.append(line)
    return "\n".join(kept)


class JiantingResearchPresetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PRESET.read_text(encoding="utf-8")
        cls.variant = mapping_block(cls.text, "high_background_podcast", 2)

    def require_variant(self) -> str:
        self.assertIsNotNone(
            self.variant,
            "high_background_podcast variant is absent from jianting-research",
        )
        return self.variant

    def test_revision_increments_and_variant_is_explicitly_opt_in(self):
        revision = re.search(r"(?m)^revision:\s*(\d+)\s*$", self.text)
        self.assertIsNotNone(revision)
        self.assertEqual(int(revision.group(1)), 2)

        defaults = mapping_block(self.text, "defaults", 0)
        self.assertIsNotNone(defaults)
        self.assertNotIn("high_background_podcast", defaults)

        variant = self.require_variant()
        for boundary in (
            "明确请求",
            "泛称财经",
            "jianting-research",
            "image-only",
            "不自动启用",
        ):
            with self.subTest(boundary=boundary):
                self.assertIn(boundary, variant)

    def test_coverage_target_and_metrics_have_distinct_meanings(self):
        variant = self.require_variant()
        self.assertRegex(variant, r"(?m)^\s+coverage_starting_target:\s*0\.90\s*$")
        for meaning in (
            "构图总帧",
            "有效背景视频层",
            "覆盖率",
            "不是独立源素材时长",
            "不等于感知可见度",
        ):
            with self.subTest(meaning=meaning):
                self.assertIn(meaning, variant)

        reporting = mapping_block(variant, "reporting", 4)
        self.assertIsNotNone(reporting)
        for separate_metric in (
            "background_coverage",
            "unique_usable_footage",
            "reused_assets_and_treatments",
        ):
            with self.subTest(separate_metric=separate_metric):
                self.assertRegex(reporting, rf"(?m)^\s+{separate_metric}:")
        self.assertIn("诊断指标", variant)
        self.assertIn("不是制作门槛", variant)

    def test_varied_reuse_and_compositing_controls_remain_editorially_honest(self):
        variant = self.require_variant()
        self.assertIn("编辑诚实", variant)
        for treatment in ("trim", "crop", "scale", "speed", "opacity", "layout", "spacing"):
            with self.subTest(treatment=treatment):
                self.assertRegex(variant, rf"(?m)^\s+- {treatment}:")

        controls = mapping_block(variant, "compositing_controls", 4)
        self.assertIsNotNone(controls)
        self.assertNotIn("combined_opacity", controls)
        for control in ("asset_opacity", "overlay_alpha"):
            with self.subTest(control=control):
                block = mapping_block(controls, control, 6)
                self.assertIsNotNone(block)
                self.assertIn("独立可调", block)
                self.assertIn("不设通用固定数值区间", block)

    def test_data_holdouts_and_existing_research_rules_are_preserved(self):
        variant = self.require_variant()
        for holdout_boundary in ("纯数据", "证据画面", "可读性", "来源忠实度"):
            with self.subTest(holdout_boundary=holdout_boundary):
                self.assertIn(holdout_boundary, variant)

        for existing_rule in (
            "相同指标、单位和时间范围",
            "区分报告事实、机构预测与作者判断",
            "缺数据则列待办，不编造柱高或曲线",
            "不把虚构工厂、人物或报告页伪装成真实证据",
        ):
            with self.subTest(existing_rule=existing_rule):
                self.assertIn(existing_rule, self.text)

        self.assertNotRegex(self.text, r"(?m)(?:^|\s)/(?:tmp|home|Users|workspace)/")
        for renderer_detail in ("ffmpeg", "Remotion", "HyperFrames", "concurrency"):
            with self.subTest(renderer_detail=renderer_detail):
                self.assertNotIn(renderer_detail, variant)


if __name__ == "__main__":
    unittest.main()
