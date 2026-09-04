---
name: media-assets
description: Inventory, select, and track project media with explicit provenance, license state, identity confidence, and reuse metadata.
metadata:
  short-description: Govern and select video assets
---

# Media Assets

Use this Skill when a project needs an asset inventory, candidate selection, source tracking, licensing state, or reuse accounting. Read [`references/asset-manifest-contract.md`](references/asset-manifest-contract.md), [`references/selection-policy.md`](references/selection-policy.md), and [`references/provenance-policy.md`](references/provenance-policy.md) for the relevant operation.

## Inputs and output

Consume a project's storyboard shot intents, candidate ids or search requirements, and any available local media library. Produce or update `ASSET_MANIFEST.json` with stable ids, metadata, provenance, license status, and reuse decisions.

## Selection workflow

1. Resolve candidate files and inspect their dimensions, duration, orientation, and readability at the target output size.
2. Check claim safety before semantic fit: identity and license state must permit the intended use.
3. Rank candidates by semantic fit, format fit, reuse fit, and render-time resolvability.
4. Record the selected asset id and any meaningful reason or warning in the manifest or project notes.
5. Keep uncertain identity, unverified license, missing source, and unavailable files explicit. Let the workflow decide whether a warning blocks publication or is limited to internal preview.

## Boundaries

- This Skill manages the media decision and record; it does not rewrite the narrative or choose a renderer.
- A filename, search-result title, or visual resemblance is not proof of identity.
- Generated or illustrative media must not be represented as an authentic source document or as evidence about an organization it does not depict.
