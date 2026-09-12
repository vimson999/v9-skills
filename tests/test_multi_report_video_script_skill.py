"""Regression checks for the multi-report script delivery contract."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/multi-report-video-script/SKILL.md"
PROMPT = ROOT / "skills/multi-report-video-script/references/prompt-v1.md"


class MultiReportVideoScriptSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = SKILL.read_text(encoding="utf-8")
        cls.prompt = PROMPT.read_text(encoding="utf-8")
        cls.stage_b = cls.prompt.split("# 阶段 B：", maxsplit=1)[1]

    def test_research_and_tts_delivery_are_separate_layers(self):
        for required in (
            "研究证据层",
            "TTS 交付层",
            "filecite",
            "来源核对表",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.prompt)

        self.assertIn("不得进入 TTS 最终稿", self.prompt)

    def test_stage_b_has_a_fixed_zero_citation_delivery_contract(self):
        for forbidden_marker in (
            "filecite",
            "来源标签",
            "脚注",
            "链接",
        ):
            with self.subTest(forbidden_marker=forbidden_marker):
                self.assertIn(forbidden_marker, self.stage_b)

        self.assertIn("正文 → Takeaway → 免责声明", self.stage_b)
        self.assertIn("默认包含", self.stage_b)

    def test_stage_b_requires_tts_cleanup_and_prevents_research_drift(self):
        for required in (
            "朗读层清洗",
            "EV/NOPAT",
            "DCF",
            "WACC",
            "公式放画面，逻辑留口播",
            "不得新增研究结构",
            "已批准的 Debate Map",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.stage_b)

    def test_final_gate_checks_all_five_delivery_elements(self):
        self.assertIn("五项交付门槛", self.stage_b)
        for required in (
            "开头异常",
            "母问题",
            "第二高潮",
            "Takeaway",
            "免责声明",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.stage_b)

    def test_entrypoint_exposes_the_strict_six_step_flow(self):
        self.assertIn("Strict delivery flow", self.skill)
        for step in range(1, 7):
            with self.subTest(step=step):
                self.assertIn(f"{step}.", self.skill)


if __name__ == "__main__":
    unittest.main()
