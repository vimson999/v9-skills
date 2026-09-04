# v9-skills

`v9-skills` is a composable toolbox for agent-led video production. It separates triggerable Skills from the references, deterministic scripts, and project artifacts that let those Skills work together.

## Current foundation

This repository starts with the video system because it is the first concrete use case. The architecture is intentionally flat: conceptual roles such as capability, workflow, router, and engine are expressed in each Skill's responsibility, not in four physical parent directories.

| Path | Role | Responsibility |
| --- | --- | --- |
| [`skills/video`](skills/video) | Router Skill | Select the next video workflow or domain Skill |
| [`skills/report-video`](skills/report-video) | Workflow Skill | Orchestrate report production end to end |
| [`skills/srt-visual-director`](skills/srt-visual-director) | Domain Skill | Turn timed narration into semantic beats and a storyboard |
| [`skills/media-assets`](skills/media-assets) | Domain Skill | Inventory, select, govern, and track reusable media |
| [`skills/remotion`](skills/remotion) | Engine Skill | Implement assigned scenes with React and frame-based rendering |
| [`skills/hyperframes`](skills/hyperframes) | Engine Skill | Implement assigned scenes with HTML/CSS/GSAP motion design |
| [`skills/render-reliability`](skills/render-reliability) | Verification Skill | Check deterministic, complete, usable render outputs |

## Artifact flow

```text
BRIEF → timed narration (audio + SRT) → STORYBOARD.md
                                      ├→ ASSET_MANIFEST.json
                                      └→ per-shot execution.renderer
                                           ↓
                                  Remotion / HyperFrames
                                           ↓
                                  RENDER_OUTPUT.json + video
                                           ↓
                                  render-reliability
```

`STORYBOARD.md` is the single visual plan-layer artifact. It records narrative beats, visual intent, candidate assets, timing, and the renderer for each executable shot. Renderer source code does not belong in the storyboard, and a second `execution-plan.json` is not introduced.

## Object model

- **Skill** — an independently triggerable, coherent capability.
- **Router Skill** — selects the appropriate workflow or domain Skill.
- **Workflow Skill** — sequences Skills and owns handoffs and stop conditions.
- **Reference / Contract** — durable rules or formats read by a Skill.
- **Script** — deterministic mechanical work that should not be reinvented in prose.
- **Project Artifact** — state passed between stages of one production.

## Start here

1. Read the [foundation design](docs/superpowers/specs/2026-09-04-v9-skills-foundation-design.md) for the complete map and decisions.
2. Use [`skills/video/SKILL.md`](skills/video/SKILL.md) as the entry router.
3. Read the relevant Skill and its linked references only for the requested stage.
4. Run `./scripts/validate-foundation.sh` after changing the foundation.

## Deliberate non-goals for this phase

`asset-policy`, `technical-director`, `storyboard`, `shot-designer`, `health-video`, and `book-video` are not separate Skills yet. They become candidates only after repeated independent use or after an audit demonstrates a real boundary. The next migration step is to audit an existing `srt-visual-director` implementation against the current contracts.
