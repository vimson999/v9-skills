---
name: srt-visual-director
description: Design visual storyboards from narration and SRT. Use image-only mode for 图片视觉导演、文案配图、独立图片轮播、素材复用与缺图提示词; retain general mode for mixed-media renderer-aware storyboards. Does not generate images or render video.
metadata:
  short-description: Direct SRT into a visual storyboard
---

# SRT Visual Director

Use this Skill when narration, script, and SRT timing need to become a visual plan. Read [`references/storyboard-contract.md`](references/storyboard-contract.md) and, for factual or financial claims, [`references/evidence-rules.md`](references/evidence-rules.md) before editing the storyboard.

## Choose the mode

- **Image-only:** When the user wants independent still images matched to narration, read [`references/image-only-workflow.md`](references/image-only-workflow.md) and [`references/image-storyboard-contract.md`](references/image-storyboard-contract.md). This mode produces image designs, existing-asset references, missing-image prompts, and timing. Renderer assignment is deferred until implementation is requested. It can also produce an explicitly untimed draft from a script alone.
- **General:** For mixed media, information animation, or already assigned engines, follow the existing workflow below. Do not replace an existing project's artifact/profile without an explicit migration need.

Both modes extend the same `STORYBOARD.md`. Image-only mode does not generate images, mutate the shared asset library, or implement a renderer. Use the user's existing choices and authorization; do not require a fresh approval at every planning step.

## Inputs and output

For a named channel, directing profile, visual-style preset, or project `DIRECTOR.yaml`, read [`references/director-presets.md`](references/director-presets.md) and only the selected presets. Keep directing strategy, visual style, and project overrides separate. The bundled profiles include 兼听研报 and 中老年健康科普; neither is the universal default. Snapshot effective rules in the storyboard so later preset edits do not silently change existing projects.

In general mode, consume a BRIEF plus narration text and a usable SRT. Use audio when available to understand pacing, but keep the SRT timestamps as the supplied timing baseline. Flag discrepancies instead of silently changing them. Produce or extend the project's `STORYBOARD.md`.

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
