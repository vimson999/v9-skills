# Asset Selection Policy

Select an asset for a shot by considering the following signals in order:

1. **Claim safety:** identity, evidence role, and licensing state must allow the intended use.
2. **Semantic fit:** the asset must support the shot's visual intent and narrative beat.
3. **Format fit:** prefer the required orientation, resolution, duration, and crop headroom.
4. **Reuse fit:** avoid unnecessary consecutive reuse or an obvious unvaried loop.
5. **Production fit:** prefer assets that can be resolved at render time and whose metadata is complete.

When candidates trade off, record the reason for the selection in the manifest or project notes. Do not treat a filename, search-result title, or visual resemblance as proof of identity.

An asset with an unverified license may be used for internal preview only when the project explicitly allows that state. Publication-facing workflows should block or replace it according to the manifest's license status.
