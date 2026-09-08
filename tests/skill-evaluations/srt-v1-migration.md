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
