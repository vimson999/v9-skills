---
name: render-reliability
description: Verify video render outputs for file completeness, duration, frame rate, deterministic behavior, and structured handoff metadata.
metadata:
  short-description: Verify reliable video renders
---

# Render Reliability

Use this Skill after scene or master-video rendering, or when the user asks whether a video output is complete and usable. Read [`schemas/render-output.schema.json`](../../schemas/render-output.schema.json) before writing the structured report.

## Verification sequence

1. Confirm every expected output path exists and is readable.
2. Inspect the final video's duration, frame rate, dimensions, audio presence, and caption output against the storyboard and brief.
3. Run a smoke render or short representative render when the project has a renderer command.
4. When a deterministic rerun is available, compare the relevant metadata or hashes and record any expected nondeterminism.
5. Write `RENDER_OUTPUT.json` with the output paths, renderer, duration, frame rate, verification checks, and overall status.

## Status rules

- `passed` means the required checks completed without a blocking discrepancy.
- `warning` means the output is inspectable but a known issue remains and is recorded.
- `failed` means a required file or verification condition is missing or contradictory.

Never infer a successful render from a command that merely started, from a stale output file, or from a renderer's textual success message without inspecting the resulting artifact.
