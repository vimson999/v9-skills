# Asset Selection Policy

Select an asset for a shot by considering the following signals in order:

1. **Claim safety:** identity, evidence role, and licensing state must allow the intended use.
2. **Semantic fit:** the asset must support the shot's visual intent and narrative beat.
3. **Format fit:** prefer the required orientation, resolution, duration, and crop headroom.
4. **Reuse fit:** avoid unnecessary consecutive reuse or an obvious unvaried loop.
5. **Production fit:** prefer assets that can be resolved at render time and whose metadata is complete.

When candidates trade off, record the reason for the selection in the manifest or project notes. Do not treat a filename, search-result title, or visual resemblance as proof of identity.

For context media, broad semantic fit is acceptable when the image or footage does not imply a false exact company, event, product, date, or location. Evidence claims have a higher bar: use an asset only when its claimed identity is inspectable. A filename or resemblance is not evidence.

An asset with an unverified license may be used for internal preview only when the project explicitly allows that state. Publication-facing workflows should block or replace it according to the manifest's license status.

A genuine user-provided low-resolution report screenshot remains eligible for the catalog. Record the limitation in `resolutionWarning`, assess readability at output size, and never invent unreadable text. Resolution by itself is not a provenance or license decision.

Keep selection status independent from provenance and license state. Report background coverage separately from unique footage duration and reuse count. Varied reuse is acceptable when each use remains semantically honest; unique duration alone is not an asset-gap gate.
