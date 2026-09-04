---
name: video
description: Route video-production requests to the appropriate workflow or engine-aware domain Skill using the available project artifacts and explicit renderer boundaries.
metadata:
  short-description: Route video work to the right Skill
---

# Video Router

Use this Skill when a request concerns planning, creating, editing, rendering, or verifying a video. Choose the narrowest next Skill that can complete the requested stage, then pass the relevant project artifact to it.

## Routing table

| Request or current artifact | Route to |
| --- | --- |
| Produce a report video from a brief, narration, report, or SRT | [`report-video`](../report-video/SKILL.md) |
| Turn narration and SRT timing into beats or a storyboard | [`srt-visual-director`](../srt-visual-director/SKILL.md) |
| Inventory, find, select, license, or track media | [`media-assets`](../media-assets/SKILL.md) |
| Implement a shot assigned to React/components/frames | [`remotion`](../remotion/SKILL.md) |
| Implement a shot assigned to HTML/CSS/GSAP motion design | [`hyperframes`](../hyperframes/SKILL.md) |
| Check a render, smoke test, output metadata, or determinism | [`render-reliability`](../render-reliability/SKILL.md) |

## Routing rules

1. Prefer an existing artifact over reconstructing state from a prompt. The main handoff artifacts are BRIEF, timed narration (audio + SRT), `STORYBOARD.md`, `ASSET_MANIFEST.json`, and `RENDER_OUTPUT.json`.
2. For a narration-led deliverable, route through the storyboard before engine implementation unless the user explicitly asks for an isolated engine experiment.
3. Do not route asset governance to an engine Skill, and do not route renderer implementation to the director Skill.
4. If a request is ambiguous between a full workflow and a single stage, ask one question that changes the route. Do not load every Skill speculatively.
5. Preserve explicit stop conditions from the selected workflow. Missing timing, provenance, license state, or renderer assignment is a production issue, not permission to invent data.

## Boundary

This router selects and hands off work. It does not write a storyboard, choose evidence, implement a renderer, or claim that a render passed verification.
