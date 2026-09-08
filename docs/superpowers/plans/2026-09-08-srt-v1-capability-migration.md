# SRT V1 Capability Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the portable, reusable behavior in `vimson999/srt-v1` into the existing modular `v9-skills` PR branch while preserving both general and image-only visual direction.

**Architecture:** Keep PR #1 as the source of truth. Add deterministic project initialization to `report-video`, deterministic shared-library intake to `media-assets`, move operational render rules to `render-reliability`, and keep only SRT interpretation and storyboard intent in `srt-visual-director`. Validate executable behavior with temporary-directory tests and validate Skill guidance with before/after agent scenarios.

**Tech Stack:** Markdown Agent Skills, Python 3 standard library, `unittest`, YAML presets, Git/GitHub.

**Spec:** `docs/superpowers/specs/2026-09-08-srt-v1-capability-migration-design.md`

## Global Constraints

- Preserve one canonical `STORYBOARD.md`; do not add a parallel execution-plan artifact.
- An SRT-only request must be able to initialize a project without an existing BRIEF.
- `srt-visual-director` does not generate images, mutate the asset library, or render video.
- Asset identity, provenance, licensing, and shared-library state belong to `media-assets`.
- Renderer implementation belongs to `remotion` or `hyperframes`; render verification belongs to `render-reliability`.
- No reusable script or test may depend on `/Users/v9`, `/Downloads/report-video`, or another developer-machine path.
- Existing general and image-only behavior, including the 24 `image_timeline` checks, must remain green.

---

### Task 1: Record baseline Skill behavior

**Files:**
- Create: `tests/skill-evaluations/srt-v1-migration.md`

**Interfaces:**
- Consumes: Current PR #1 Skills before migration changes.
- Produces: Three repeatable scenarios and the observed baseline gaps used to justify the minimal guidance changes.

- [ ] **Step 1: Run three read-only baseline scenarios without migrated guidance**

Use isolated agents with the current branch and these exact requests:

```text
Scenario A: The user supplies only final.srt and asks for a new report-video project. Decide the next action and exact artifact path. Do not invent missing project state.

Scenario B: The user says assets are ready in asset-library/inbox/episode-a and asks to continue. Decide who owns intake, deduplication, catalog updates, and what the user must run.

Scenario C: A 12-minute Remotion render passed at concurrency 1, fails at concurrency 8, and has verified completed segments. Decide retry scope, audio handling, and what can be deleted.
```

Expected baseline gap: at least one response must lack a deterministic repository-owned action or leave a responsibility ambiguous. If every response already satisfies the spec, remove the corresponding documentation change instead of adding redundant guidance.

- [ ] **Step 2: Save evidence, not invented conclusions**

Write the scenario, the agent's decision, the specific missing/ambiguous behavior, and the acceptance rule. Do not paste hidden reasoning or claim a failure when the response complied.

- [ ] **Step 3: Verify the evaluation document is complete**

Run:

```bash
rg -n '^## Scenario|^Baseline decision:|^Observed gap:|^Acceptance rule:' tests/skill-evaluations/srt-v1-migration.md
```

Expected: three scenarios, each with all four fields.

---

### Task 2: Add portable SRT-only project initialization

**Files:**
- Create: `skills/report-video/scripts/init_project.py`
- Create: `tests/test_report_video_init.py`
- Modify: `skills/report-video/SKILL.md`
- Modify: `skills/srt-visual-director/SKILL.md`

**Interfaces:**
- Consumes: A factory root, a readable `.srt`, and optional project ID, title, aspect ratio, subtitle burn-in setting, and asset-library path.
- Produces: `projects/<project-id>/` with `project.json`, `input/subtitles.srt`, `input/script.txt`, `STORYBOARD.md`, an empty valid `ASSET_MANIFEST.json`, and output directories. It does not create `RENDER_OUTPUT.json` before a render exists.

- [ ] **Step 1: Write the failing behavior test**

```python
def test_srt_only_initialization_is_portable_and_non_destructive(self):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "Final Episode.srt"
        source.write_text("1\n00:00:00,000 --> 00:00:02,000\n<b>Hello</b> world\n", encoding="utf-8")
        project = init.initialize_project(root / "factory", source, project_id="Episode A")
        self.assertEqual(project.name, "episode-a")
        self.assertEqual((project / "input/subtitles.srt").read_bytes(), source.read_bytes())
        self.assertEqual((project / "input/script.txt").read_text().strip(), "Hello world")
        self.assertEqual(json.loads((project / "ASSET_MANIFEST.json").read_text())["assets"], [])
        self.assertFalse((project / "RENDER_OUTPUT.json").exists())
        self.assertFalse((root / "factory/asset-library").exists())
        with self.assertRaises(FileExistsError):
            init.initialize_project(root / "factory", source, project_id="Episode A")
```

Use `unittest` assertions in the committed test because the repository has no pytest dependency. Add separate cases for malformed extension, missing input, multiline cues, and optional relative asset-library configuration.

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
python3 -m unittest tests.test_report_video_init -v
```

Expected: import/file failure because `skills/report-video/scripts/init_project.py` does not exist.

- [ ] **Step 3: Implement the minimal initializer**

Implement three callable functions with the Python standard library: `sanitize_project_id(value: str) -> str`, `srt_to_script(srt_text: str) -> str`, and `initialize_project(factory_root: Path, srt_path: Path, *, project_id: str | None = None, title: str | None = None, aspect_ratio: str = "16:9", subtitle_burn_in: bool = True, asset_library: Path | None = None) -> Path`.

The stable project metadata shape is:

```json
{
  "schemaVersion": 1,
  "projectId": "episode-a",
  "title": "Episode A",
  "status": "initialized",
  "timingSource": "input/subtitles.srt",
  "script": "input/script.txt",
  "storyboard": "STORYBOARD.md",
  "assetManifest": "ASSET_MANIFEST.json",
  "renderOutput": null,
  "aspectRatio": "16:9",
  "subtitleBurnIn": true,
  "assetLibrary": null
}
```

`project.json` records relative artifact paths and their initial states. `STORYBOARD.md` states that planning has not started and points to the preserved SRT. `ASSET_MANIFEST.json` uses `projectId`, an RFC 3339 UTC `generatedAt`, and an empty `assets` list so it conforms to the repository schema. Refuse an existing project before creating any project files.

- [ ] **Step 4: Route SRT-only startup through the workflow**

In `report-video`, instruct the agent to execute:

```bash
python3 skills/report-video/scripts/init_project.py FINAL.srt --factory-root FACTORY_ROOT
```

when the request starts with an SRT and no project exists. In `srt-visual-director`, route initialization to that script before writing the storyboard; keep subsequent director work inside the director Skill.

- [ ] **Step 5: Verify GREEN and regressions**

Run:

```bash
python3 -m unittest tests.test_report_video_init -v
python3 -m unittest discover -s tests -p 'test_*.py'
bash scripts/validate-foundation.sh
```

Expected: all commands exit 0; existing 24 image-only tests still pass.

---

### Task 3: Add portable shared-asset intake

**Files:**
- Create: `skills/media-assets/scripts/intake_assets.py`
- Create: `skills/media-assets/references/shared-library-workflow.md`
- Create: `tests/test_media_asset_intake.py`
- Modify: `skills/media-assets/SKILL.md`
- Modify: `skills/media-assets/references/selection-policy.md`
- Modify: `skills/media-assets/references/provenance-policy.md`

**Interfaces:**
- Consumes: `library_root: Path`, `project_id: str`, and optional `source: Path`.
- Produces: hash-deduplicated originals under `raw/`, `catalog/assets.json`, durable `catalog/metadata.json`, `catalog/review_queue.json`, `catalog/usage.json`, append-only intake logs, and a JSON command summary.

- [ ] **Step 1: Write failing intake tests**

```python
def test_intake_is_hash_idempotent_and_preserves_reviewed_metadata():
    first = intake.intake_assets(library, "episode-a")
    asset_id = first["imported"][0]["id"]
    metadata["assets"][asset_id] = {"description": "Reviewed factory line", "licenseStatus": "confirmed"}
    second = intake.intake_assets(library, "episode-a")
    assert first["importedCount"] == 1
    assert second["duplicateCount"] == 1
    assert catalog_record(asset_id)["description"] == "Reviewed factory line"
    assert catalog_record(asset_id)["sha256"] == sha256(b"video-bytes").hexdigest()
```

Add observable cases for category inference, same-name/different-content collision handling, unsupported input reporting, source preservation, stable `asset-<hash-prefix>` IDs, and custom temporary roots.

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
python3 -m unittest tests.test_media_asset_intake -v
```

Expected: import/file failure because the media-assets intake script does not exist.

- [ ] **Step 3: Implement portable intake and catalog rebuild**

Implement these public functions: `sha256_file(path: Path) -> str`, `category_for_path(path: Path) -> str`, `initialize_library(library_root: Path) -> None`, `rebuild_catalog(library_root: Path) -> dict`, and `intake_assets(library_root: Path, project_id: str, source: Path | None = None) -> dict`.

Derive stable IDs and immutable computed fields as follows:

```python
asset_id = f"asset-{digest[:16]}"
computed = {
    "id": asset_id,
    "sha256": digest,
    "kind": kind,
    "path": destination.relative_to(library_root).as_posix(),
    "fileName": destination.name,
    "fileSizeBytes": destination.stat().st_size,
}
```

The script must not call a developer-local `build-index.mjs`. It computes portable catalog fields itself, merges only reviewed descriptive fields from `metadata.json`, leaves file identity/path/hash computed from disk, and never deletes inbox sources. New assets enter the review queue with explicit visual, provenance, and license review reasons.

- [ ] **Step 4: Document ownership and acceptance rules**

`shared-library-workflow.md` defines the sibling library layout, agent-owned inbox flow, catalog sources of truth, and command:

```bash
python3 skills/media-assets/scripts/intake_assets.py --library-root ASSET_LIBRARY --project-id PROJECT_ID
```

Add the demonstrated `srt-v1` rules: semantic fit for context assets; exact identity for evidence claims; low resolution is a warning rather than automatic rejection for a genuine user-provided report screenshot; selection status remains separate from provenance/license; reuse and unique duration are reported separately.

- [ ] **Step 5: Verify GREEN and regressions**

Run:

```bash
python3 -m unittest tests.test_media_asset_intake -v
python3 -m unittest discover -s tests -p 'test_*.py'
bash scripts/validate-foundation.sh
```

Expected: all commands exit 0 with no dependency on an external index builder or absolute machine path.

---

### Task 4: Re-home render and finance-profile guidance

**Files:**
- Create: `skills/render-reliability/references/render-operations.md`
- Modify: `skills/render-reliability/SKILL.md`
- Modify: `skills/report-video/SKILL.md`
- Modify: `skills/srt-visual-director/references/presets/directing/jianting-research.yaml`
- Modify: `tests/skill-evaluations/srt-v1-migration.md`

**Interfaces:**
- Consumes: The migrated design and baseline scenario gaps.
- Produces: Focused operational guidance loaded only for preview/export, finance-only optional production defaults, and recorded forward-test results.

- [ ] **Step 1: Add the minimal render operations reference**

Cover the reusable invariants from `srt-v1`: preflight composition/media/browser/disk/memory checks; representative smoke render; concurrency as a measured setting; resumable numeric frame segments; retry only failed ranges; one final audio mux; explicit source-to-local audio ranges; task-owned cleanup; final `ffprobe`/artifact inspection; stale-output detection; preview approval separate from export authorization.

- [ ] **Step 2: Route the reference without bloating the entrypoint**

Keep `render-reliability/SKILL.md` concise and require `references/render-operations.md` before a preview/export or retry plan. Update `report-video` to keep preview approval distinct from a full render request and to use muted segments plus one final audio mux for segmented rendering.

- [ ] **Step 3: Scope finance-only defaults**

Add an optional `high_background_podcast` variant under `jianting-research.yaml` with a 90% background-video coverage starting target, separate reporting of unique footage, allowed varied reuse, and independent asset-opacity/overlay-alpha controls. Apply it only when the user/project requests that variant; do not make it the universal finance or image-only default.

- [ ] **Step 4: Re-run the same three Skill scenarios with migrated guidance**

Expected behavior:

```text
A: Executes the report-video initializer, preserves the SRT, and does not invent a completed storyboard.
B: The agent runs media-assets intake itself, keeps inbox files, deduplicates by hash, and records unresolved review state.
C: Retries only failed segments at proven concurrency, preserves verified segments, muxes source audio once, and limits cleanup to task-owned verified intermediates.
```

Save the decisions and any remaining gap in `tests/skill-evaluations/srt-v1-migration.md`. Revise only guidance implicated by an observed failure, then re-run that scenario.

- [ ] **Step 5: Run full verification**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
bash scripts/validate-foundation.sh
python3 skills/srt-visual-director/scripts/image_timeline.py validate tests/fixtures/image-director/STORYBOARD.md --srt tests/fixtures/image-director/narration.srt
rg -n '/Users/v9|/Downloads/report-video' skills tests scripts
git diff --check
```

Expected: all test/validation commands exit 0; the path scan returns no matches; `git diff --check` is clean.

---

### Task 5: Update repository guidance and PR #1

**Files:**
- Modify: `README.md`
- Modify: PR #1 description

**Interfaces:**
- Consumes: Verified migration commits and evaluation evidence.
- Produces: An accurate repository map and PR description that distinguishes automated checks, agent forward tests, and untested image/render quality.

- [ ] **Step 1: Update the repository map**

Document the SRT-only initializer and shared-library intake commands beside their owning Skills. State that `srt-v1` was audited into modular destinations rather than copied wholesale.

- [ ] **Step 2: Re-run final verification from a clean checkout state**

Run the Task 4 full verification command set and inspect `git status --short`, `git diff --stat`, and the commit list against `origin/main`.

- [ ] **Step 3: Commit and push the branch**

Use focused commits:

```bash
git add skills/report-video skills/srt-visual-director tests/test_report_video_init.py
git commit -m "feat: initialize report projects from SRT"
git add skills/media-assets tests/test_media_asset_intake.py
git commit -m "feat: migrate shared asset intake"
git add skills/render-reliability README.md tests/skill-evaluations
git commit -m "docs: complete srt-v1 capability migration"
git push origin feat/image-visual-director
```

When connector-backed pushing is required, create equivalent commits on the same remote branch without force-updating it.

- [ ] **Step 4: Update PR #1 truthfully**

Include exact test counts, baseline/forward scenarios, the removed absolute-path dependency, and remaining boundaries: no generated images, no paid APIs, no full video render, no visual-quality claim, and no deletion/archive reminders for `srt-v1`.
