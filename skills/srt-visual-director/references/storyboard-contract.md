# Storyboard Contract

`STORYBOARD.md` is the canonical plan-layer artifact for a video project. It can be extended through the production loop, but a later stage must edit the same file rather than create a second storyboard.

## Required project sections

```markdown
# Storyboard: <project title>

## Project

- id: `<project-id>`
- timing source: `<path to SRT or other timing source>`

## Global direction

<audience, tone, visual language, aspect ratio, and editorial constraints>

## Shots

### shot-001

- time: `00:00:00.000 → 00:00:04.000`
- narrative beat: <what the viewer should understand>
- voiceover refs: `srt-001..srt-002`
- visual intent: <what should be seen and why>
- asset candidates: `asset-001`, `asset-002`
- execution renderer: `remotion`
- execution pattern: <named visual pattern>
- transition in: <treatment or none>
- transition out: <treatment or none>
- status: `planned`
```

The example is a shape, not a requirement to use the exact prose. The machine-readable projection is defined in [`schemas/storyboard.schema.json`](../../../schemas/storyboard.schema.json).

## Layer rules

### Story design

Record the narrative beat, voiceover relationship, and reason the shot exists. At this layer, do not decide React component structure, HTML structure, CSS properties, or GSAP calls.

### Visual design

Add visual intent, asset candidates, layout language, motion direction, transitions, and a named pattern. The description remains implementation-neutral: it says what should happen, not how to write the renderer source.

### Execution handoff

After visual design, add an explicit `execution.renderer` for every executable shot:

```yaml
execution:
  renderer: remotion
  pattern: comparison-chart
```

Use `remotion` for a React/frame-based implementation or `hyperframes` for an HTML/CSS/GSAP implementation. The video workflow may use both engines across different shots; the storyboard does not contain engine source code.

## Timing rules

- SRT timestamps are timing truth when narration drives the project.
- A subtitle cue is not automatically a shot. Group related cues into semantic visual units.
- Use 5–15 seconds as a starting heuristic for a semantic unit, then adjust for the idea, pacing, and available evidence.
- Do not invent timing to conceal a missing or malformed SRT. Mark the handoff as blocked and ask for a corrected timing source.
