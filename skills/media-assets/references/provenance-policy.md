# Provenance Policy

Every selected asset needs an inspectable provenance record:

- stable asset id;
- local path or resolvable source;
- source name and source URL when applicable;
- identity confidence (`verified`, `probable`, or `unknown`);
- license status (`confirmed`, `unverified`, `restricted`, or `forbidden`);
- reuse permission and usage count.

If a source is unknown, keep the uncertainty explicit. `unknown` identity is not equivalent to verified identity, and `unverified` license is not equivalent to confirmed permission. A generated asset should identify its generation source and should not be represented as documentary evidence.
