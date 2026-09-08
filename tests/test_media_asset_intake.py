"""Behavioral tests for portable shared media-library intake."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/media-assets/scripts/intake_assets.py"
SPEC = importlib.util.spec_from_file_location("media_asset_intake", SCRIPT)
media_asset_intake = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(media_asset_intake)


class MediaAssetIntakeTests(unittest.TestCase):
    def load_json(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_empty_default_intake_initializes_only_the_requested_library(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "custom-library"

            result = media_asset_intake.intake_assets(root, "Project A")

            resolved = root.resolve()
            self.assertEqual(result["libraryRoot"], str(resolved))
            self.assertEqual(result["projectId"], "Project A")
            self.assertEqual(result["source"], str((resolved / "inbox/Project A").resolve()))
            self.assertEqual(
                (result["importedCount"], result["duplicateCount"], result["ignoredCount"]),
                (0, 0, 0),
            )
            self.assertEqual(result["imported"], [])
            self.assertEqual(result["duplicates"], [])
            self.assertEqual(result["ignored"], [])
            for relative in (
                "inbox/Project A",
                "raw/video",
                "raw/images",
                "raw/reports",
                "raw/logos",
                "processed/video",
                "processed/images",
                "processed/thumbnails",
                "catalog/intake_logs",
            ):
                self.assertTrue((resolved / relative).is_dir(), relative)
            for relative in (
                "catalog/assets.json",
                "catalog/metadata.json",
                "catalog/review_queue.json",
                "catalog/usage.json",
                "catalog/intake_log.json",
            ):
                self.assertTrue((resolved / relative).is_file(), relative)
            self.assertEqual(
                self.load_json(resolved / "catalog/metadata.json"),
                {"schemaVersion": 1, "libraryId": "v9-asset-library", "assets": {}},
            )
            self.assertEqual(
                self.load_json(resolved / "catalog/usage.json"),
                {
                    "schemaVersion": 1,
                    "libraryId": "v9-asset-library",
                    "projects": {},
                    "assets": {},
                },
            )

    def test_default_source_rejects_unsafe_project_ids_without_creating_library(self):
        unsafe_ids = (
            "",
            " ",
            ".",
            "..",
            "../other",
            "one/two",
            r"one\two",
            "one\ttwo",
            "one\ntwo",
            "one\x7ftwo",
            "one\u0085two",
            "/tmp/outside",
        )
        for project_id in unsafe_ids:
            with self.subTest(project_id=project_id), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "library"

                with self.assertRaises(ValueError):
                    media_asset_intake.intake_assets(root, project_id)

                self.assertFalse(root.exists())

    def test_library_write_components_cannot_be_symlinks_to_outside(self):
        components = (
            "raw",
            "raw/video",
            "processed",
            "processed/thumbnails",
            "catalog",
            "catalog/intake_logs",
        )
        for component in components:
            with self.subTest(component=component), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                root = base / "library"
                outside = base / "outside"
                source = base / "source"
                root.mkdir()
                outside.mkdir()
                source.mkdir()
                (source / "clip.mp4").write_bytes(b"clip")
                link = root / component
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(outside, target_is_directory=True)

                with self.assertRaises(ValueError):
                    media_asset_intake.intake_assets(root, "safe-project", source)

                self.assertEqual(list(outside.iterdir()), [])

    def test_import_infers_categories_ignores_hidden_entries_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "library"
            source = base / "drop"
            fixtures = {
                "movie.MP4": b"video",
                "image.JPEG": b"image",
                "reports/brief.PDF": b"report",
                "brand/logos/mark.PNG": b"logo",
                "notes.txt": b"unsupported",
                ".hidden.mov": b"hidden file",
                ".private/secret.jpg": b"hidden directory",
            }
            for relative, payload in fixtures.items():
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)

            result = media_asset_intake.intake_assets(root, "demo", source)

            self.assertEqual(result["importedCount"], 4)
            self.assertEqual(result["duplicateCount"], 0)
            self.assertEqual(result["ignoredCount"], 1)
            self.assertEqual(result["ignored"][0]["reason"], "unsupported_media_type")
            self.assertTrue((root / "raw/video/movie.MP4").is_file())
            self.assertTrue((root / "raw/images/image.JPEG").is_file())
            self.assertTrue((root / "raw/reports/brief.PDF").is_file())
            self.assertTrue((root / "raw/logos/mark.PNG").is_file())
            self.assertFalse((root / "raw/video/.hidden.mov").exists())
            self.assertFalse((root / "raw/images/secret.jpg").exists())
            for relative, payload in fixtures.items():
                self.assertEqual((source / relative).read_bytes(), payload)
            self.assertEqual(media_asset_intake.category_for_path(source / "clip.webm"), "video")
            self.assertEqual(media_asset_intake.category_for_path(source / "photo.tiff"), "images")
            self.assertEqual(media_asset_intake.category_for_path(source / "summary.pdf"), "reports")
            self.assertEqual(media_asset_intake.category_for_path(source / "logos/photo.jpg"), "logos")

    def test_second_run_deduplicates_by_hash_and_keeps_stable_catalog_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "library"
            source = base / "source"
            source.mkdir()
            original = source / "clip.mp4"
            original.write_bytes(b"same media")
            digest = hashlib.sha256(b"same media").hexdigest()

            first = media_asset_intake.intake_assets(root, "demo", source)
            first_catalog = self.load_json(root / "catalog/assets.json")
            second = media_asset_intake.intake_assets(root, "demo", source)
            second_catalog = self.load_json(root / "catalog/assets.json")

            self.assertEqual(first["importedCount"], 1)
            self.assertEqual(second["duplicateCount"], 1)
            self.assertEqual(second["importedCount"], 0)
            self.assertEqual(len(list((root / "raw/video").iterdir())), 1)
            self.assertEqual(first_catalog["assets"], second_catalog["assets"])
            self.assertEqual(len(second_catalog["assets"]), 1)
            asset = second_catalog["assets"][0]
            self.assertEqual(asset["id"], f"asset-{digest[:16]}")
            self.assertEqual(asset["sha256"], digest)
            self.assertEqual(asset["kind"], "video")
            self.assertEqual(asset["path"], "raw/video/clip.mp4")
            self.assertEqual(asset["fileName"], "clip.mp4")
            self.assertEqual(asset["fileSizeBytes"], len(b"same media"))
            self.assertEqual(media_asset_intake.sha256_file(original), digest)

    def test_unsupported_raw_backup_does_not_suppress_supported_import(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "library"
            source = base / "source"
            media_asset_intake.initialize_library(root)
            source.mkdir()
            payload = b"supported media"
            (root / "raw/video/clip.mp4.bak").write_bytes(payload)
            (source / "clip.mp4").write_bytes(payload)

            result = media_asset_intake.intake_assets(root, "demo", source)

            self.assertEqual(result["importedCount"], 1)
            self.assertEqual(result["duplicateCount"], 0)
            self.assertEqual((root / "raw/video/clip.mp4").read_bytes(), payload)
            catalog = self.load_json(root / "catalog/assets.json")
            self.assertEqual([asset["path"] for asset in catalog["assets"]], ["raw/video/clip.mp4"])

    def test_same_name_different_content_gets_hash_suffix(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "library"
            first_source = base / "first"
            second_source = base / "second"
            first_source.mkdir()
            second_source.mkdir()
            (first_source / "clip.mp4").write_bytes(b"first")
            (second_source / "clip.mp4").write_bytes(b"second")
            second_digest = hashlib.sha256(b"second").hexdigest()

            media_asset_intake.intake_assets(root, "one", first_source)
            result = media_asset_intake.intake_assets(root, "two", second_source)

            self.assertEqual(result["importedCount"], 1)
            self.assertEqual((root / "raw/video/clip.mp4").read_bytes(), b"first")
            collision = root / f"raw/video/clip__{second_digest[:8]}.mp4"
            self.assertEqual(collision.read_bytes(), b"second")

    def test_hash_collision_candidate_uses_numeric_suffix_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "library"
            source = base / "source"
            source.mkdir()
            media_asset_intake.initialize_library(root)
            (root / "raw/video/clip.mp4").write_bytes(b"original name")
            payload = b"new content"
            digest = hashlib.sha256(payload).hexdigest()
            first_collision = root / f"raw/video/clip__{digest[:8]}.mp4"
            first_collision.write_bytes(b"different collision content")
            (source / "clip.mp4").write_bytes(payload)

            result = media_asset_intake.intake_assets(root, "demo", source)

            numeric = root / f"raw/video/clip__{digest[:8]}_2.mp4"
            self.assertEqual(result["imported"][0]["path"], numeric.relative_to(root).as_posix())
            self.assertEqual((root / "raw/video/clip.mp4").read_bytes(), b"original name")
            self.assertEqual(first_collision.read_bytes(), b"different collision content")
            self.assertEqual(numeric.read_bytes(), payload)

    def test_keyboard_interrupt_during_copy_leaves_no_eligible_partial_and_retry_succeeds(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "library"
            source = base / "source"
            source.mkdir()
            payload = b"complete source payload"
            (source / "clip.mp4").write_bytes(payload)
            original_copy = media_asset_intake.shutil.copyfileobj

            def interrupted_copy(source_handle, target_handle):
                target_handle.write(b"partial")
                target_handle.flush()
                raise KeyboardInterrupt("simulated interruption")

            media_asset_intake.shutil.copyfileobj = interrupted_copy
            try:
                with self.assertRaisesRegex(KeyboardInterrupt, "simulated interruption"):
                    media_asset_intake.intake_assets(root, "demo", source)
            finally:
                media_asset_intake.shutil.copyfileobj = original_copy

            self.assertEqual(list((root / "raw/video").iterdir()), [])
            self.assertEqual(self.load_json(root / "catalog/assets.json")["assets"], [])

            result = media_asset_intake.intake_assets(root, "demo", source)

            self.assertEqual(result["importedCount"], 1)
            self.assertEqual((root / "raw/video/clip.mp4").read_bytes(), payload)
            self.assertEqual(len(self.load_json(root / "catalog/assets.json")["assets"]), 1)
            self.assertFalse(any(path.name.startswith(".") for path in (root / "raw").rglob("*")))

    def test_unavailable_source_never_changes_preexisting_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = root / "missing.mp4"
            destination = root / "clip.mp4"
            original = b"pre-existing destination"
            destination.write_bytes(original)

            with self.assertRaises(FileNotFoundError):
                media_asset_intake._copy_non_clobber(missing, destination)

            self.assertEqual(destination.read_bytes(), original)
            self.assertEqual([path.name for path in root.iterdir()], ["clip.mp4"])

    def test_read_only_metadata_is_applied_only_after_staging_name_is_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.mp4"
            destination = root / "destination.mp4"
            payload = b"complete read-only source"
            source.write_bytes(payload)
            source.chmod(0o444)
            original_copystat = media_asset_intake.shutil.copystat
            metadata_destinations = []

            def observed_copystat(source_path, destination_path):
                destination_path = Path(destination_path)
                metadata_destinations.append(destination_path)
                self.assertEqual(destination_path, destination)
                self.assertEqual(list(root.glob(".*.staging")), [])
                return original_copystat(source_path, destination_path)

            media_asset_intake.shutil.copystat = observed_copystat
            try:
                media_asset_intake._copy_non_clobber(source, destination)
                self.assertEqual(destination.read_bytes(), payload)
                self.assertEqual(metadata_destinations, [destination])
            finally:
                media_asset_intake.shutil.copystat = original_copystat
                source.chmod(0o644)
                if destination.exists():
                    destination.chmod(0o644)

    def test_metadata_interrupt_removes_only_the_published_final(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.mp4"
            destination = root / "destination.mp4"
            source.write_bytes(b"complete source")
            original_copystat = media_asset_intake.shutil.copystat

            def interrupted_copystat(source_path, destination_path):
                destination_path = Path(destination_path)
                self.assertEqual(destination_path, destination)
                self.assertEqual(list(root.glob(".*.staging")), [])
                destination_path.chmod(0o444)
                raise KeyboardInterrupt("metadata interruption")

            media_asset_intake.shutil.copystat = interrupted_copystat
            try:
                with self.assertRaisesRegex(KeyboardInterrupt, "metadata interruption"):
                    media_asset_intake._copy_non_clobber(source, destination)
            finally:
                media_asset_intake.shutil.copystat = original_copystat
                if destination.exists():
                    destination.chmod(0o644)

            self.assertFalse(destination.exists())
            self.assertEqual([path.name for path in root.iterdir()], ["source.mp4"])

    def test_interrupt_after_publish_detects_and_removes_the_owned_final_inode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.mp4"
            destination = root / "destination.mp4"
            source.write_bytes(b"complete source")
            original_link = media_asset_intake.os.link

            def interrupted_link(staging_path, destination_path):
                original_link(staging_path, destination_path)
                raise KeyboardInterrupt("publish interruption")

            media_asset_intake.os.link = interrupted_link
            try:
                with self.assertRaisesRegex(KeyboardInterrupt, "publish interruption"):
                    media_asset_intake._copy_non_clobber(source, destination)
            finally:
                media_asset_intake.os.link = original_link

            self.assertFalse(destination.exists())
            self.assertEqual([path.name for path in root.iterdir()], ["source.mp4"])

    def test_rebuild_merges_only_reviewed_fields_and_preserves_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "library"
            media_asset_intake.initialize_library(root)
            raw = root / "raw/images/photo.png"
            raw.write_bytes(b"pixels")
            digest = hashlib.sha256(b"pixels").hexdigest()
            asset_id = f"asset-{digest[:16]}"
            media_asset_intake.rebuild_catalog(root)
            initial_queue = self.load_json(root / "catalog/review_queue.json")["assets"]
            self.assertEqual(initial_queue[0]["id"], asset_id)
            self.assertTrue(initial_queue[0]["reasons"])
            metadata = {
                "schemaVersion": 1,
                "libraryId": "v9-asset-library",
                "assets": {
                    asset_id: {
                        "id": "overridden-id",
                        "sha256": "0" * 64,
                        "kind": "video",
                        "path": "/not/portable",
                        "fileName": "wrong.mov",
                        "fileSizeBytes": 999,
                        "description": "A reviewed product image",
                        "tags": ["product", "approved"],
                        "selectionStatus": "selected",
                        "provenanceStatus": "verified",
                        "licenseStatus": "confirmed",
                        "resolutionWarning": "Source is 320px wide",
                        "notes": "Use without enlarging text",
                        "unexpected": "must not leak",
                    }
                },
            }
            usage = {
                "schemaVersion": 1,
                "libraryId": "v9-asset-library",
                "projects": {"demo": {"assetIds": [asset_id]}},
                "assets": {asset_id: {"reuseCount": 2}},
            }
            (root / "catalog/metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
            (root / "catalog/usage.json").write_text(json.dumps(usage), encoding="utf-8")

            catalog = media_asset_intake.rebuild_catalog(root)

            asset = catalog["assets"][0]
            self.assertEqual(
                {key: asset[key] for key in ("id", "sha256", "kind", "path", "fileName", "fileSizeBytes")},
                {
                    "id": asset_id,
                    "sha256": digest,
                    "kind": "image",
                    "path": "raw/images/photo.png",
                    "fileName": "photo.png",
                    "fileSizeBytes": len(b"pixels"),
                },
            )
            self.assertEqual(asset["description"], "A reviewed product image")
            self.assertEqual(asset["tags"], ["product", "approved"])
            self.assertEqual(asset["selectionStatus"], "selected")
            self.assertEqual(asset["provenanceStatus"], "verified")
            self.assertEqual(asset["licenseStatus"], "confirmed")
            self.assertEqual(asset["resolutionWarning"], "Source is 320px wide")
            self.assertEqual(asset["notes"], "Use without enlarging text")
            self.assertNotIn("unexpected", asset)
            self.assertEqual(self.load_json(root / "catalog/metadata.json"), metadata)
            self.assertEqual(self.load_json(root / "catalog/usage.json"), usage)
            self.assertEqual(self.load_json(root / "catalog/review_queue.json")["assets"], [])

    def test_malformed_reviewed_metadata_is_normalized_and_stays_unresolved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "library"
            media_asset_intake.initialize_library(root)
            raw = root / "raw/images/photo.png"
            raw.write_bytes(b"pixels")
            digest = hashlib.sha256(b"pixels").hexdigest()
            asset_id = f"asset-{digest[:16]}"
            metadata = {
                "schemaVersion": 1,
                "libraryId": "v9-asset-library",
                "assets": {
                    asset_id: {
                        "description": None,
                        "tags": ["valid", 7],
                        "selectionStatus": "   ",
                        "provenanceStatus": 123,
                        "licenseStatus": "mystery",
                        "resolutionWarning": {"bad": "shape"},
                        "notes": ["not", "text"],
                    }
                },
            }
            (root / "catalog/metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

            catalog = media_asset_intake.rebuild_catalog(root)

            asset = catalog["assets"][0]
            self.assertEqual(asset["description"], "")
            self.assertEqual(asset["tags"], [])
            self.assertEqual(asset["selectionStatus"], "unreviewed")
            self.assertEqual(asset["provenanceStatus"], "unknown")
            self.assertEqual(asset["licenseStatus"], "unverified")
            self.assertIsNone(asset["resolutionWarning"])
            self.assertEqual(asset["notes"], "")
            queue = self.load_json(root / "catalog/review_queue.json")["assets"]
            self.assertEqual(
                set(queue[0]["reasons"]),
                {
                    "missing_description",
                    "selection_unreviewed",
                    "provenance_unknown",
                    "license_unverified",
                },
            )

    def test_review_queue_has_explicit_reasons_and_catalog_order_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "library"
            media_asset_intake.initialize_library(root)
            (root / "raw/video/z.mp4").write_bytes(b"z")
            (root / "raw/images/a.png").write_bytes(b"a")

            first = media_asset_intake.rebuild_catalog(root)
            second = media_asset_intake.rebuild_catalog(root)

            self.assertEqual(first["assets"], second["assets"])
            assets = first["assets"]
            self.assertEqual([asset["id"] for asset in assets], sorted(asset["id"] for asset in assets))
            queue = self.load_json(root / "catalog/review_queue.json")["assets"]
            self.assertEqual([item["id"] for item in queue], sorted(item["id"] for item in queue))
            expected_reasons = {
                "missing_description",
                "selection_unreviewed",
                "provenance_unknown",
                "license_unverified",
            }
            for item in queue:
                self.assertEqual(set(item["reasons"]), expected_reasons)

    def test_rebuild_uses_one_deterministic_canonical_path_per_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "library"
            media_asset_intake.initialize_library(root)
            payload = b"identical raw content"
            image = root / "raw/images/a.png"
            video = root / "raw/video/z.mp4"
            image.write_bytes(payload)
            video.write_bytes(payload)
            asset_id = f"asset-{hashlib.sha256(payload).hexdigest()[:16]}"

            first = media_asset_intake.rebuild_catalog(root)
            second = media_asset_intake.rebuild_catalog(root)

            self.assertEqual([asset["id"] for asset in first["assets"]], [asset_id])
            self.assertEqual(first["assets"][0]["path"], "raw/images/a.png")
            self.assertEqual(first["assets"], second["assets"])
            self.assertEqual(image.read_bytes(), payload)
            self.assertEqual(video.read_bytes(), payload)

    def test_intake_writes_current_and_timestamped_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "library"
            source = base / "source"
            source.mkdir()
            (source / "photo.webp").write_bytes(b"photo")

            result = media_asset_intake.intake_assets(root, "Client / Demo", source)

            self.assertEqual(self.load_json(root / "catalog/intake_log.json"), result)
            logs = list((root / "catalog/intake_logs").glob("*-client-demo.json"))
            self.assertEqual(len(logs), 1)
            self.assertEqual(self.load_json(logs[0]), result)

    def test_cli_outputs_json_for_a_custom_root_and_source(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "nested/custom-assets"
            source = base / "incoming"
            source.mkdir()
            (source / "sample.mkv").write_bytes(b"sample")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--library-root",
                    str(root),
                    "--project-id",
                    "CLI Demo",
                    "--source",
                    str(source),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            summary = json.loads(result.stdout)
            self.assertEqual(summary["importedCount"], 1)
            self.assertEqual(summary["libraryRoot"], str(root.resolve()))
            self.assertEqual(summary["source"], str(source.resolve()))
            self.assertEqual(summary["projectId"], "CLI Demo")
            self.assertEqual(result.stderr, "")

    def test_missing_explicit_source_is_rejected_before_api_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "library"
            missing = Path(directory) / "missing-source"

            with self.assertRaisesRegex(FileNotFoundError, "Explicit source does not exist"):
                media_asset_intake.intake_assets(root, "demo", missing)

            self.assertFalse(root.exists())

    def test_missing_explicit_source_has_clear_nonzero_cli_error_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "library"
            missing = Path(directory) / "missing-source"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--library-root",
                    str(root),
                    "--project-id",
                    "demo",
                    "--source",
                    str(missing),
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertIn("Explicit source does not exist", result.stderr)
            self.assertFalse(root.exists())

    def test_concurrent_process_fails_clearly_while_library_lock_is_held(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "library"
            first_source = base / "first-source"
            second_source = base / "second-source"
            first_source.mkdir()
            second_source.mkdir()
            first_payload = b"first concurrent original"
            second_payload = b"second concurrent original"
            (first_source / "clip.mp4").write_bytes(first_payload)
            (second_source / "clip.mp4").write_bytes(second_payload)
            command = [
                sys.executable,
                str(SCRIPT),
                "--library-root",
                str(root),
                "--project-id",
                "second",
                "--source",
                str(second_source),
            ]

            with media_asset_intake._library_lock(root.resolve()):
                first = media_asset_intake._intake_assets_locked(
                    root.resolve(), "first", first_source.resolve()
                )
                busy = subprocess.run(command, capture_output=True, text=True)

            self.assertEqual(first["importedCount"], 1)
            self.assertNotEqual(busy.returncode, 0)
            self.assertEqual(busy.stdout, "")
            self.assertIn("Asset library is busy", busy.stderr)
            self.assertTrue((root / ".intake.lock").is_file())
            self.assertEqual((root / "raw/video/clip.mp4").read_bytes(), first_payload)
            first_id = f"asset-{hashlib.sha256(first_payload).hexdigest()[:16]}"
            second_id = f"asset-{hashlib.sha256(second_payload).hexdigest()[:16]}"
            self.assertEqual(
                [asset["id"] for asset in self.load_json(root / "catalog/assets.json")["assets"]],
                [first_id],
            )

            successful = subprocess.run(command, check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(successful.stdout)["importedCount"], 1)
            catalog = self.load_json(root / "catalog/assets.json")
            self.assertEqual({asset["id"] for asset in catalog["assets"]}, {first_id, second_id})
            self.assertEqual(len(list((root / "raw/video").iterdir())), 2)

    def test_process_termination_releases_library_lock_without_manual_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "library"
            source = base / "source"
            source.mkdir()
            (source / "clip.mp4").write_bytes(b"clip")
            holder_code = """
import importlib.util
from pathlib import Path
import sys
import time

spec = importlib.util.spec_from_file_location("holder_intake", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with module._library_lock(Path(sys.argv[2])):
    print("locked", flush=True)
    time.sleep(60)
"""
            holder = subprocess.Popen(
                [sys.executable, "-c", holder_code, str(SCRIPT), str(root)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                self.assertEqual(holder.stdout.readline().strip(), "locked")
                holder.terminate()
                holder.communicate(timeout=5)
            finally:
                if holder.poll() is None:
                    holder.kill()
                    holder.communicate(timeout=5)

            result = media_asset_intake.intake_assets(root, "demo", source)

            self.assertEqual(result["importedCount"], 1)
            self.assertEqual((root / "raw/video/clip.mp4").read_bytes(), b"clip")


if __name__ == "__main__":
    unittest.main()
