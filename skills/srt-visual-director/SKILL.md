---
name: srt-visual-director
description: Convert timed narration and SRT cues into semantic beats, visual intent, and a renderer-aware STORYBOARD.md without implementing renderer source code.
metadata:
  short-description: Direct SRT into a visual storyboard
---

# SRT Visual Director

Use this Skill when narration, script, and SRT timing need to become a visual plan. Read [`references/storyboard-contract.md`](references/storyboard-contract.md) and, for factual or financial claims, [`references/evidence-rules.md`](references/evidence-rules.md) before editing the storyboard.

## Inputs and output

Consume a BRIEF plus narration text and a usable SRT. Use audio when available to understand pacing, but keep the SRT timestamps as timing truth. Produce or extend the project's `STORYBOARD.md`.

## Direction workflow

1. Inspect the SRT for cue order, gaps, overlaps, and total duration.
2. Group related subtitle cues into semantic visual units. A 5–15 second unit is a starting heuristic; the idea and pacing determine the final boundary.
3. Write the story layer: why the shot exists, what the viewer should understand, and which voiceover cues it serves.
4. Write the visual layer: visual intent, layout language, motion direction, transition, and candidate asset ids. Keep the description implementation-neutral.
5. Add an explicit `execution.renderer` of `remotion` or `hyperframes` after the visual intent is clear, and add a short pattern name when useful.
6. Extend the existing `STORYBOARD.md` through later stages instead of creating a second storyboard.

## Boundaries

- Do not write HTML, CSS, GSAP, React, or renderer source code in the storyboard.
- Do not resolve the asset library, decide license permission, or hide provenance gaps; hand those decisions to [`media-assets`](../media-assets/SKILL.md).
- Do not render a scene or claim that a render passed; hand implementation to the assigned engine and verification to [`render-reliability`](../render-reliability/SKILL.md).
- For evidence-led claims, follow the evidence reference and label illustrative B-roll as contextual rather than documentary.
