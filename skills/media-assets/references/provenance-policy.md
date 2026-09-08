# Provenance Policy

Every selected asset needs an inspectable provenance record:

- stable asset id;
- local path or resolvable source;
- source name and source URL when applicable;
- identity confidence (`verified`, `probable`, or `unknown`);
- license status (`confirmed`, `unverified`, `restricted`, or `forbidden`);
- reuse permission and usage count.

If a source is unknown, keep the uncertainty explicit. `unknown` identity is not equivalent to verified identity, and `unverified` license is not equivalent to confirmed permission. A generated asset should identify its generation source and should not be represented as documentary evidence.

Context media may rely on broad semantic fit only when it does not imply a false exact company, event, product, date, or location. Evidence claims require inspectable identity: neither a filename nor visual resemblance proves what an asset depicts.

Keep selection status separate from provenance and license state. Selecting an asset does not verify its identity or grant permission, and verified provenance does not make it selected. For a genuine user-provided report screenshot, retain the asset even when resolution is low, record the limitation with `resolutionWarning`, and never invent text that cannot be inspected.
