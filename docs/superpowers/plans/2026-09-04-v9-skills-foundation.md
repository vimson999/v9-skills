# v9-skills Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the agreed video-agent architecture into a small, navigable, machine-checkable foundation without prematurely splitting `srt-visual-director`.

**Architecture:** Keep a flat `skills/<skill-name>/` namespace. Use `video` as the router, `report-video` as the first workflow, `srt-visual-director` and `media-assets` as domain capabilities, Remotion and HyperFrames as engine skills, and references/schemas as the collaboration contracts. Keep `STORYBOARD.md` as the plan-layer source of truth and store renderer assignment per shot.

**Tech Stack:** Markdown skill instructions, JSON Schema Draft 2020-12 contracts, POSIX shell validation, no runtime dependencies.

**Spec:** `docs/superpowers/specs/2026-09-04-v9-skills-foundation-design.md`

## Global Constraints

- Skills use lowercase letters, digits, and hyphens in directory names.
- The physical namespace is flat under `skills/`; do not create `capabilities/`, `policies/`, `engines/`, or `workflows/` parent directories.
- `STORYBOARD.md` is the only canonical visual plan artifact; do not introduce `execution-plan.json`.
- SRT timestamps are timing truth for narration-led videos.
- Storyboard instructions express visual intent and renderer assignment, not HTML, React, or GSAP implementation code.
- Renderer assignment is explicit per executable shot and is `remotion` or `hyperframes`.
- Asset provenance and license state are recorded in the asset manifest.
- New Skills are added only for independently triggerable, reusable behavior; rules remain references.

---

### Task 1: Add the project entrypoint and stable architecture index

**Files:**
- Create: `README.md`
- Use as source: `docs/superpowers/specs/2026-09-04-v9-skills-foundation-design.md`

**Interfaces:**
- Consumes: the approved foundation design.
- Produces: a short project entrypoint that links to the design record, the initial Skills, and the validation command.

- [ ] **Step 1: Write the README sections**

Include the project purpose, object model table, initial Skill list, artifact flow, and next migration boundary. Link to the spec instead of duplicating its full Mermaid diagram.

- [ ] **Step 2: Check that every linked initial Skill path is planned**

Run:

```bash
rg -n "skills/(video|report-video|srt-visual-director|media-assets|remotion|hyperframes|render-reliability)" README.md
```

Expected: each of the seven initial Skill paths appears in the README.

### Task 2: Define the artifact contracts and policy references

**Files:**
- Create: `schemas/brief.schema.json`
- Create: `schemas/storyboard.schema.json`
- Create: `schemas/asset-manifest.schema.json`
- Create: `schemas/render-output.schema.json`
- Create: `skills/srt-visual-director/references/storyboard-contract.md`
- Create: `skills/srt-visual-director/references/evidence-rules.md`
- Create: `skills/media-assets/references/asset-manifest-contract.md`
- Create: `skills/media-assets/references/selection-policy.md`
- Create: `skills/media-assets/references/provenance-policy.md`

**Interfaces:**
- Consumes: the artifact invariants and renderer boundary in the spec.
- Produces: stable field names for BRIEF, STORYBOARD, ASSET MANIFEST, and RENDER OUTPUT; human-readable guidance for the two domain Skills.

- [ ] **Step 1: Define the BRIEF schema**

Require `id`, `title`, `domain`, `objective`, and `sourceMaterials`; model source materials as objects with `id`, `kind`, and `path`.

- [ ] **Step 2: Define the storyboard projection schema**

Require `project`, `timingSource`, and `shots`. Each shot must include `id`, `start`, `end`, `narrativeBeat`, `visualIntent`, and `execution.renderer`; restrict the renderer to `remotion` and `hyperframes`.

- [ ] **Step 3: Define the asset manifest schema**

Require `projectId`, `generatedAt`, and `assets`. Each asset must include identity, kind, path, provenance, license, and reuse metadata.

- [ ] **Step 4: Define the render output schema**

Require `projectId`, `renderedAt`, `outputs`, and `verification`. Record output path, renderer, duration, frame rate, and verification status without replacing the storyboard.

- [ ] **Step 5: Write the Markdown contracts**

Document the canonical `STORYBOARD.md` sections, the rule that it is extended rather than duplicated, the SRT-to-semantic-unit grouping rule, and the renderer assignment block. Document evidence and asset policies as references, not Skills.

- [ ] **Step 6: Cross-check field names between schemas and references**

Run:

```bash
rg -n "renderer|projectId|timingSource|sourceMaterials|provenance|verification" schemas skills/*/references
```

Expected: the same names are used consistently; no `execution-plan.json` appears.

### Task 3: Create the Video Router and report workflow

**Files:**
- Create: `skills/video/SKILL.md`
- Create: `skills/report-video/SKILL.md`

**Interfaces:**
- Consumes: BRIEF, SRT/audio, STORYBOARD, ASSET MANIFEST, and RENDER OUTPUT contracts.
- Produces: routing decisions and an ordered report-video workflow with explicit stop conditions.

- [ ] **Step 1: Write `video/SKILL.md` frontmatter and routing table**

Route full report production to `report-video`, SRT-to-storyboard work to `srt-visual-director`, inventory/selection work to `media-assets`, renderer implementation to `remotion` or `hyperframes`, and output checks to `render-reliability`.

- [ ] **Step 2: State the router boundary**

Make clear that `video` chooses the next unit and does not itself make narrative, asset, or engine implementation decisions.

- [ ] **Step 3: Write `report-video/SKILL.md`**

Specify the sequence BRIEF → timed narration → STORYBOARD → ASSET MANIFEST → per-shot renderer execution → master composition → RENDER OUTPUT → reliability verification. Stop when timing truth, evidence provenance, or renderer assignment is missing instead of silently inventing it.

### Task 4: Create the two domain Skills

**Files:**
- Create: `skills/srt-visual-director/SKILL.md`
- Create: `skills/media-assets/SKILL.md`

**Interfaces:**
- Consumes: the references and schemas from Task 2.
- Produces: a coherent SRT-to-storyboard capability and an inventory/selection/provenance capability without splitting policy into separate Skills.

- [ ] **Step 1: Write `srt-visual-director/SKILL.md`**

Keep SRT interpretation, semantic beat grouping, narrative intent, and visual direction together. Require the Skill to read the storyboard and evidence references, and forbid HTML/React/GSAP implementation in the plan layer.

- [ ] **Step 2: Write `media-assets/SKILL.md`**

Keep inventory, candidate selection, provenance, licensing state, and reuse decisions together. Require the Skill to record unresolved license or identity issues instead of hiding them in filenames or prompts.

### Task 5: Create engine and reliability Skills

**Files:**
- Create: `skills/remotion/SKILL.md`
- Create: `skills/hyperframes/SKILL.md`
- Create: `skills/render-reliability/SKILL.md`

**Interfaces:**
- Consumes: storyboard shot assignments and the asset manifest.
- Produces: engine-specific implementation guidance and a verification contract for render outputs.

- [ ] **Step 1: Write the Remotion engine Skill**

Describe React/component/frame-based implementation, data-driven reuse, and its responsibility for assigned shots only.

- [ ] **Step 2: Write the HyperFrames engine Skill**

Describe HTML/CSS/GSAP/timeline-based implementation, motion-graphics strengths, and its responsibility for assigned shots only.

- [ ] **Step 3: Write the reliability Skill**

Require a smoke render, file existence checks, duration/frame-rate checks, deterministic rerun comparison where available, and a structured `RENDER_OUTPUT.json` report.

### Task 6: Add a repeatable foundation validator

**Files:**
- Create: `scripts/validate-foundation.sh`

**Interfaces:**
- Consumes: all initial Skill directories and JSON schemas.
- Produces: exit code 0 only when the expected structure, frontmatter, JSON syntax, and no-placeholder rule pass.

- [ ] **Step 1: Implement the validator**

Check the seven expected `SKILL.md` files, require `name` and `description` frontmatter, parse every `schemas/*.json` file with `jq` when available or Node's standard JSON parser otherwise, and reject `TODO`, `TBD`, or `{{...}}` in Skill instructions.

- [ ] **Step 2: Make it executable**

Run:

```bash
chmod +x scripts/validate-foundation.sh
```

- [ ] **Step 3: Run the validator**

Run:

```bash
./scripts/validate-foundation.sh
```

Expected: exit code 0 and one success line for the foundation.

### Task 7: Perform final structural verification

**Files:**
- Verify: all files created in Tasks 1–6.

**Interfaces:**
- Consumes: the completed foundation.
- Produces: fresh evidence that the project matches the spec and that no premature category tree or parallel storyboard artifact was introduced.

- [ ] **Step 1: List the structure**

Run:

```bash
find . -maxdepth 4 -type f -print | sort
```

Expected: the seven flat initial Skill directories, `schemas/`, `docs/`, and `scripts/` are present; no `capabilities/`, `policies/`, `engines/`, or `workflows/` parent directories exist.

- [ ] **Step 2: Search for forbidden parallel planning artifacts**

Run:

```bash
rg -n "execution-plan\.json|second storyboard|parallel storyboard" .
```

Expected: no result in implementation files; the design record may explain why the artifact is intentionally absent.

- [ ] **Step 3: Run the foundation validator again**

Run:

```bash
./scripts/validate-foundation.sh
```

Expected: exit code 0 after the final file set is in place.
