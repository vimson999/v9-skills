---
name: hyperframes
description: Implement storyboard shots assigned to HyperFrames using HTML, CSS, GSAP timelines, and motion-graphics patterns.
metadata:
  short-description: Implement HTML and GSAP motion scenes
---

# HyperFrames Engine

Use this Skill when a storyboard shot explicitly assigns `execution.renderer: hyperframes`, or when the user asks for an HTML/CSS/GSAP motion-graphics implementation.

## Engine contract

Consume the assigned storyboard shots and the resolved `ASSET_MANIFEST.json`. Treat HTML as the scene source of truth, use CSS for visual design, and use a GSAP timeline or the project's established HyperFrames timing conventions for animation.

HyperFrames is a strong fit for kinetic typography, title cards, marker sweeps, scribbles, chart motion, overlays, captions, and visually dense transitions. Keep the scene's timing and meaning traceable back to the storyboard.

## Boundaries

- Do not decide what a shot means or rewrite its narrative beat in the engine layer.
- Do not introduce untracked assets or present illustrative media as evidence.
- Do not create a second storyboard inside the engine project.
- Return scene/output metadata to the owning workflow so it can compose the master timeline and create `RENDER_OUTPUT.json`.
