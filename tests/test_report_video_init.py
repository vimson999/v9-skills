"""Behavioral tests for creating a report-video project from an SRT."""

from datetime import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/report-video/scripts/init_project.py"
SPEC = importlib.util.spec_from_file_location("report_video_init", SCRIPT)
report_video_init = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report_video_init)


class InitializeReportVideoProjectTests(unittest.TestCase):
    def write_srt(self, root: Path, name: str = "Episode A.srt") -> tuple[Path, bytes]:
        payload = (
            b"\xef\xbb\xbf1\r\n"
            b"00:00:00,000 --> 00:00:02,000\r\n"
            b"<b>Hello</b> world\r\n\r\n"
            b"2\r\n"
            b"00:00:02,000 --> 00:00:04,000 align:start\r\n"
            b"Second line\r\n"
        )
        path = root / name
        path.write_bytes(payload)
        return path, payload

    def test_initialize_creates_portable_project_with_expected_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = Path(directory)
            srt_path, source_bytes = self.write_srt(factory)

            project = report_video_init.initialize_project(
                factory,
                srt_path,
                project_id="Episode A",
                title="Episode A",
            )

            expected = (factory / "projects/episode-a").resolve()
            self.assertEqual(project, expected)
            self.assertTrue((project / "input").is_dir())
            self.assertTrue((project / "output/preview").is_dir())
            self.assertTrue((project / "output/final").is_dir())
            self.assertEqual((project / "input/subtitles.srt").read_bytes(), source_bytes)
            self.assertEqual(
                (project / "input/script.txt").read_text(encoding="utf-8"),
                "Hello world\nSecond line\n",
            )

            storyboard = (project / "STORYBOARD.md").read_text(encoding="utf-8")
            self.assertIn("not started", storyboard.lower())
            self.assertIn("input/subtitles.srt", storyboard)
            self.assertNotIn("shot-", storyboard.lower())
            self.assertNotIn("remotion", storyboard.lower())
            self.assertNotIn("hyperframes", storyboard.lower())

            manifest = json.loads(
                (project / "ASSET_MANIFEST.json").read_text(encoding="utf-8")
            )
            self.assertEqual(set(manifest), {"projectId", "generatedAt", "assets"})
            self.assertEqual(manifest["projectId"], "episode-a")
            self.assertEqual(manifest["assets"], [])
            generated_at = datetime.fromisoformat(
                manifest["generatedAt"].replace("Z", "+00:00")
            )
            self.assertIsNotNone(generated_at.tzinfo)
            self.assertEqual(generated_at.utcoffset().total_seconds(), 0)

            project_data = json.loads(
                (project / "project.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                project_data,
                {
                    "schemaVersion": 1,
                    "projectId": "episode-a",
                    "title": "Episode A",
                    "status": "initialized",
                    "timingSource": "input/subtitles.srt",
                    "script": "input/script.txt",
                    "storyboard": "STORYBOARD.md",
                    "assetManifest": "ASSET_MANIFEST.json",
                    "renderOutput": None,
                    "aspectRatio": "16:9",
                    "subtitleBurnIn": True,
                    "assetLibrary": None,
                },
            )

    def test_rejects_missing_directory_and_non_srt_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = Path(directory)
            missing = factory / "missing.srt"
            with self.assertRaises(FileNotFoundError):
                report_video_init.initialize_project(factory, missing)

            wrong_extension = factory / "captions.txt"
            wrong_extension.write_text("captions", encoding="utf-8")
            with self.assertRaises(ValueError):
                report_video_init.initialize_project(factory, wrong_extension)

            srt_directory = factory / "captions.srt"
            srt_directory.mkdir()
            with self.assertRaises(ValueError):
                report_video_init.initialize_project(factory, srt_directory)

    def test_srt_to_script_handles_bom_tags_and_multiline_cues(self):
        srt = (
            "\ufeff1\r\n"
            "00:00:00,000 --> 00:00:01,500\r\n"
            "<font color=\"yellow\">First</font> line\r\n"
            "continues <i>here</i>\r\n\r\n"
            "2\r\n"
            "00:00:01,500 --> 00:00:03,000 position:50%\r\n"
            "<b>Final</b> cue\r\n"
        )

        self.assertEqual(
            report_video_init.srt_to_script(srt),
            "First line continues here\nFinal cue",
        )

    def test_srt_to_script_preserves_numeric_only_spoken_text(self):
        srt = (
            "1\n"
            "00:00:00,000 --> 00:00:01,500\n"
            "2026\n\n"
            "2\n"
            "00:00:01,500 --> 00:00:03,000\n"
            "Revenue rose\n"
        )

        self.assertEqual(report_video_init.srt_to_script(srt), "2026\nRevenue rose")

    def test_srt_to_script_preserves_comparisons_and_removes_formatting_tags(self):
        srt = (
            "1\n"
            "00:00:00,000 --> 00:00:01,500\n"
            "<b>EPS < 1 and revenue > 2</b>\n\n"
            "2\n"
            "00:00:01,500 --> 00:00:03,000\n"
            "<i>Forecast</i> is <font color=\"yellow\">steady</font>\n"
        )

        self.assertEqual(
            report_video_init.srt_to_script(srt),
            "EPS < 1 and revenue > 2\nForecast is steady",
        )

    def test_srt_to_script_preserves_compact_comparisons(self):
        srt = (
            "1\n"
            "00:00:00,000 --> 00:00:01,500\n"
            "a<b and c>d\n"
        )

        self.assertEqual(report_video_init.srt_to_script(srt), "a<b and c>d")

    def test_sanitize_project_id_is_path_safe_and_has_a_stable_fallback(self):
        cases = {
            " Episode__A/../TeSt ": "episode-a-test",
            "A_/_B": "a-b",
            "R\u00e9sum\u00e9 2026": "r-sum-2026",
            "../../": "project",
            "\u4e2d\u6587": "project",
            "": "project",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(report_video_init.sanitize_project_id(raw), expected)

        with tempfile.TemporaryDirectory() as directory:
            factory = Path(directory)
            srt_path, _ = self.write_srt(factory, "safe.srt")
            project = report_video_init.initialize_project(
                factory, srt_path, project_id="../../../Outside"
            )
            self.assertEqual(project, (factory / "projects/outside").resolve())
            self.assertTrue(project.is_relative_to((factory / "projects").resolve()))

    def test_existing_project_is_refused_without_mutating_it(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = Path(directory)
            srt_path, _ = self.write_srt(factory)
            project = factory / "projects/episode-a"
            project.mkdir(parents=True)
            sentinel = project / "keep.txt"
            sentinel.write_text("untouched", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                report_video_init.initialize_project(
                    factory, srt_path, project_id="Episode A"
                )

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "untouched")
            self.assertEqual(sorted(path.name for path in project.iterdir()), ["keep.txt"])

    def test_cli_prints_only_created_path_and_applies_options(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = Path(directory)
            srt_path, _ = self.write_srt(factory, "CLI Input.srt")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(srt_path),
                    "--factory-root",
                    str(factory),
                    "--project-id",
                    "CLI Demo",
                    "--title",
                    "CLI title",
                    "--aspect-ratio",
                    "9:16",
                    "--no-burn-subtitles",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            project = (factory / "projects/cli-demo").resolve()
            self.assertEqual(result.stdout, f"{project}\n")
            self.assertEqual(result.stderr, "")
            config = json.loads((project / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(config["title"], "CLI title")
            self.assertEqual(config["aspectRatio"], "9:16")
            self.assertFalse(config["subtitleBurnIn"])

    def test_asset_library_is_recorded_relative_without_creating_it(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = Path(directory)
            srt_path, _ = self.write_srt(factory)
            library = factory / "shared/assets"

            project = report_video_init.initialize_project(
                factory,
                srt_path,
                project_id="library-demo",
                asset_library=library,
            )

            config = json.loads((project / "project.json").read_text(encoding="utf-8"))
            expected = Path(os.path.relpath(library.resolve(), project)).as_posix()
            self.assertEqual(config["assetLibrary"], expected)
            self.assertFalse(library.exists())

    def test_initialization_has_no_render_or_shared_library_side_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = Path(directory)
            srt_path, _ = self.write_srt(factory)

            project = report_video_init.initialize_project(factory, srt_path)

            self.assertFalse((project / "RENDER_OUTPUT.json").exists())
            self.assertFalse((factory / "assets").exists())
            config = json.loads((project / "project.json").read_text(encoding="utf-8"))
            self.assertIsNone(config["assetLibrary"])


if __name__ == "__main__":
    unittest.main()
