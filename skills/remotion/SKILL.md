---
name: remotion
description: Implement storyboard shots assigned to Remotion using reusable React components, frame-based timing, media, captions, and data-driven composition.
metadata:
  short-description: Implement frame-based video scenes
---

# Remotion Engine

Use this Skill when a storyboard shot explicitly assigns `execution.renderer: remotion`, or when the user asks for a React/component/frame-based video implementation.

## Engine contract

Consume the assigned storyboard shots and the resolved `ASSET_MANIFEST.json`. Implement scene behavior with React components and frame-based timing. Keep timing, layout intent, asset ids, and narrative meaning traceable back to the storyboard.

Remotion is a strong default for reusable scene components, long compositions, data-driven batches, captions, audio/media orchestration, and automated rendering. Use the project's existing runtime and composition conventions when they exist.

## Boundaries

- Do not change the narrative beat or silently reassign a shot without updating the storyboard.
- Do not treat component structure as a replacement for the storyboard plan layer.
- Resolve assets through manifest ids rather than guessing from filenames.
- Return scene/output metadata to the owning workflow so it can compose the master timeline and create `RENDER_OUTPUT.json`.
