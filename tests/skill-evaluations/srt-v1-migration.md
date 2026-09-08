# SRT v1 migration baselines

These scenarios record decisions observed from agents that read only the current PR #1 Skills.

## Scenario A

The user supplies only `/tmp/final.srt` and asks to create a new report-video project and continue visual direction. No project or `BRIEF.md` exists.

Baseline decision: The agent paused visual direction, asked the user for project root, audience, language, aspect ratio, and publication constraints, created no artifact, and proposed creating `<project-root>/BRIEF.md` before `<project-root>/STORYBOARD.md`.

Observed gap: The repository has no deterministic SRT-only initializer or exact portable project path, so the current Skills block on information the approved design says may remain unknown at initialization.

Acceptance rule: The workflow executes a repository-owned initializer, preserves the SRT, creates `projects/<project-id>/`, records unknown brief fields honestly, and leaves storyboard planning incomplete rather than invented.

Evidence: This is the recorded response from an agent given the scenario input after reading only the current PR #1 Skills; the agent created no artifact.

## Scenario B

The user says assets are ready in `asset-library/inbox/episode-a` and asks to continue.

Baseline decision: The agent correctly said the user runs no command and the inbox remains untouched, but could only inspect candidates and update project `ASSET_MANIFEST.json`. It explicitly reported that the current Skill does not define shared-library intake, hash deduplication, global catalog paths, or their owner.

Observed gap: No repository-owned deterministic intake path exists for the agent to perform the promised deduplication and shared catalog update.

Acceptance rule: `media-assets` owns and runs portable hash-based intake, keeps inbox files, updates a shared catalog and review queue, and exposes unresolved provenance/license work without asking the user to run internal commands.

Evidence: This is the recorded response from an agent given the scenario input after reading only the current PR #1 Skills; it documents the unavailable intake ownership and paths.

## Scenario C

A 12-minute Remotion render passed a representative smoke range at concurrency 1, fails at concurrency 8, and has verified completed frame segments.

Baseline decision: The agent reused only identity-compatible verified segments, retried failed or missing ranges at concurrency 1, ordered concatenation by frame range, muxed one full-timeline audio track after video assembly, kept SRT timing authority, deleted only incomplete, corrupt, or superseded task outputs, and retained sources and segments until final verification.

Observed gap: None observed in this scenario. The current Skills plus agent capability already produced the approved retry, audio, and cleanup behavior.

Acceptance rule: Preserve this behavior. Do not add duplicate Skill prose unless a later forward test shows a concrete regression.

Evidence: This records the agent's decision for the supplied scenario after reading only the current PR #1 Skills; it does not validate an actual render.

## Forward verification after migration

The same three scenarios were re-run by fresh agents that read only the migrated v9 Skill routes. Scenarios A and B executed the repository-owned scripts in an isolated temporary workspace; Scenario C remained a decision test and did not claim an actual render.

### Scenario A — PASS

Forward decision: The agent ran `python3 skills/report-video/scripts/init_project.py /tmp/v9-forward-eval.8IwKT7/final.srt --factory-root /tmp/v9-forward-eval.8IwKT7/factory`, continued from the created `projects/final` path, and stopped before inventing completed shots or renderer assignments.

Evidence: The agent inspected `project.json`, `STORYBOARD.md`, `input/subtitles.srt`, `input/script.txt`, and `ASSET_MANIFEST.json`. The SRT was preserved, numeric spoken text remained in the extracted script, the manifest was empty, and the storyboard stayed explicitly not started.

Remaining gap: The sample's financial claim lacked entity, comparison period, supporting source, and licensed evidence; audience and publication constraints were also unknown. These correctly block evidence-led visual decisions, not initialization.

### Scenario B — PASS

Forward decision: The agent ran `python3 skills/media-assets/scripts/intake_assets.py --library-root /tmp/v9-forward-eval.8IwKT7/asset-library --project-id episode-a` itself and repeated the command to verify idempotence.

Evidence: The first run imported two files; the second imported none and recorded two SHA-256 duplicates. The catalog contained one video and one logo, both source inbox files remained present, raw held exactly two copies, and current plus timestamped logs were written.

Remaining gap: Both assets remained in the review queue with `missing_description`, `selection_unreviewed`, `provenance_unknown`, and `license_unverified`. Project-level selection correctly remained pending rather than treating intake as approval.

### Scenario C — PASS

Forward decision: The agent kept concurrency at the demonstrated-safe value of 1, accepted only segments matching the same composition/build/props/frame identity, ordered them by numeric start frame, retried only complementary missing or failed ranges, rendered segments muted, and muxed source audio once over the complete timeline.

Evidence: The decision preserved verified segments until a new uniquely named final passed file, duration, frame-count, frame-rate, dimension, audio, caption, boundary-continuity, and staleness checks. Cleanup remained limited to invalid or superseded intermediates owned by the current render attempt.

Remaining gap: The scenario did not provide actual composition metadata, segment manifests, frame ranges, checksums, or audio/caption expectations, so no numeric retry ranges or real render success were claimed.

Forward-test conclusion: The two observed migration gaps are closed, and the previously correct render-recovery behavior remains intact without copying the legacy render reference into v9.
