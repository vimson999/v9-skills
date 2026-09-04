---
name: report-video
description: Orchestrate a report or research video from brief and timed narration through storyboard, assets, renderer execution, master composition, and verified output.
metadata:
  short-description: Orchestrate report-video production
---

# Report Video Workflow

Use this Skill for a complete report-video deliverable or when the user asks to run the report-video production workflow. It coordinates other Skills; it does not duplicate their domain instructions.

## Inputs and outputs

Inputs may include a structured or Markdown BRIEF, report sources, narration audio, and an SRT file. The workflow produces or updates:

- `STORYBOARD.md` — the single visual plan layer;
- `ASSET_MANIFEST.json` — project-scoped media inventory and usage record;
- scene outputs and a master video; and
- `RENDER_OUTPUT.json` — output metadata and verification results.

The artifact shapes are documented in the repository `schemas/` directory and linked from the domain Skills.

## Ordered workflow

1. Establish the BRIEF and identify the source material, audience, language, aspect ratio, and publication constraints.
2. Confirm the timed narration inputs. For narration-led work, SRT timestamps are the timing truth; align or produce audio and SRT before visual planning.
3. Invoke [`srt-visual-director`](../srt-visual-director/SKILL.md) to group cues into semantic visual units and extend `STORYBOARD.md` with story and visual design.
4. Invoke [`media-assets`](../media-assets/SKILL.md) to resolve candidates and write provenance, license, and reuse decisions into `ASSET_MANIFEST.json`.
5. Check that every executable storyboard shot has `execution.renderer` set to `remotion` or `hyperframes`. Keep this assignment in the storyboard; do not create a parallel execution plan.
6. Route each assigned shot to [`remotion`](../remotion/SKILL.md) or [`hyperframes`](../hyperframes/SKILL.md). The workflow owns the master timeline and cross-engine composition.
7. Run [`render-reliability`](../render-reliability/SKILL.md) against the produced files and write `RENDER_OUTPUT.json`.

## Stop conditions

Stop and report the missing input when:

- the narration-led project has no usable SRT or the timestamps are malformed;
- a factual or financial visual has no inspectable source identity or license state;
- an executable shot has no renderer assignment; or
- an output file cannot be found, inspected, or reconciled with the expected duration and frame rate.

Do not silently fabricate evidence, substitute an untracked asset, or mark a failed verification as passed.
