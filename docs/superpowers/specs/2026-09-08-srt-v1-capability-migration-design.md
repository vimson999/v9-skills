# SRT V1 Capability Migration Design

**Status:** Approved design baseline

**Date:** 2026-09-08

**Goal:** Migrate reusable capabilities from `vimson999/srt-v1` into the existing `v9-skills` architecture without replacing the modular `srt-visual-director` or regressing its general and image-only modes.

## Context

`srt-v1` contains a working but monolithic version of `srt-visual-director`. It combines SRT interpretation, project initialization, asset-library operations, finance defaults, renderer handoff, and render reliability. The open `v9-skills` PR #1 already implements a smaller director Skill with general and image-only modes, shared storyboard contracts, director/style presets, and deterministic image-plan validation.

The PR branch is the migration target and source of truth. `srt-v1` is an input to audit, not a directory to copy over the target.

## Design principles

1. Preserve one canonical `STORYBOARD.md` across planning and execution.
2. Preserve direct SRT-only startup: a user may provide only an SRT and receive an initialized project plus the next useful planning step.
3. Keep `srt-visual-director` responsible for SRT interpretation, semantic grouping, narrative beats, visual intent, and storyboard output.
4. Keep asset inventory, ingestion, provenance, licensing, and reuse accounting in `media-assets`.
5. Keep workflow sequencing, project state, master-timeline ownership, and final composition in `report-video`.
6. Keep renderer-specific implementation in `remotion` and `hyperframes`.
7. Keep preflight, smoke rendering, retry strategy, and output inspection in `render-reliability`.
8. Remove machine-specific paths and project-specific constants from reusable Skills and tests.
9. Preserve the existing image-only guarantees: independent images, no contact sheets as final assets, accurate text layering, honest timing/status, and no fabricated asset IDs or validation claims.

## Capability destinations

| `srt-v1` capability | Destination in `v9-skills` | Required outcome |
| --- | --- | --- |
| SRT timing truth, semantic beats, 5–15 second heuristic, ASR flags | `skills/srt-visual-director` | Shared guidance for general and image-only modes |
| Automatic SRT-only project initialization | `skills/report-video/scripts/init_project.py` plus workflow routing | Create a portable project skeleton without overwriting existing work |
| Shared asset-library creation, intake, hashing, catalog persistence | `skills/media-assets` scripts and references | Agent-owned intake with project inboxes and stable asset IDs |
| Context-footage acceptance, low-resolution report screenshots, reuse accounting | `skills/media-assets` selection/provenance references | Separate semantic fit, identity, license, resolution warnings, and reuse |
| Finance-specific visual defaults | `jianting-research` director preset or a routed profile reference | No finance defaults become universal director behavior |
| Renderer handoff and final composition | `report-video`, `remotion`, and `hyperframes` contracts | Director describes intent; workflow assigns and coordinates execution |
| Render preflight, adaptive concurrency, checkpointing, FFmpeg verification | `skills/render-reliability` | Portable checks and truthful `RENDER_OUTPUT.json` status |
| Project/output contracts | Repository `schemas/` and owning Skill references | One maintained contract per artifact |

## Project initialization contract

For a new SRT-only report-video job, the workflow creates `projects/<project_id>/` and refuses silent overwrite. At minimum it preserves the supplied SRT, writes a clean narration text file, records project metadata, and creates valid initial plan/asset/output artifacts or documented empty states compatible with repository schemas.

Project initialization must not create or depend on an absolute path. The factory root is an explicit argument or a path resolved by the caller. Shared asset-library initialization is delegated to `media-assets`; the project records only its configured library reference.

## Migration behavior

The migration is additive and test-driven:

- Existing PR #1 tests remain the regression baseline for image-only behavior.
- Portable tests are added before each migrated deterministic behavior.
- Tests copied from `srt-v1` are rewritten to use temporary directories and repository-relative fixtures.
- Policy-only guidance is tested through realistic forward scenarios and focused contract checks; wording checks alone do not prove behavioral quality.
- No migrated code may depend on `/Users/v9`, `/Downloads/report-video`, or another developer-machine path.

## Non-goals

- Do not copy the `srt-v1` directory wholesale into `skills/srt-visual-director`.
- Do not make the director generate images, mutate the shared asset library, or render video.
- Do not introduce a second storyboard or execution-plan artifact.
- Do not merge PR #1 until migrated tests and a realistic SRT forward test pass.
- Do not delete or archive `srt-v1` as part of this migration.

## Acceptance criteria

1. General and image-only director routes remain available from the same Skill.
2. A clean environment can initialize an SRT-only project without absolute paths.
3. Asset intake and catalog behavior live under `media-assets` and pass portable tests.
4. Render reliability guidance contains the reusable preflight, retry, audio-mux, and artifact-inspection invariants from `srt-v1` without importing project-specific settings.
5. Finance-only defaults are scoped to the finance directing profile.
6. Repository validation, all automated tests, and realistic forward tests pass.
7. PR #1 documents what migrated, what remains intentionally external, and what was actually verified.
