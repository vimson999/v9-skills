# Shared Library Workflow

Use a shared library when projects need a durable, reusable catalog of user-supplied originals. Keep the library as a sibling of project directories rather than embedding a private copy in each project:

```text
workspace/
  asset-library/
    inbox/<project-id>/
    raw/{video,images,reports,logos}/
    processed/{video,images,thumbnails}/
    catalog/
  projects/<project-id>/
```

The user supplies files and says when the assets are ready. The agent owns intake: it places or finds the files in the project's inbox and runs the repository script. Do not ask the user to run catalog tooling.

```bash
python3 skills/media-assets/scripts/intake_assets.py \
  --library-root ASSET_LIBRARY \
  --project-id PROJECT_ID
```

Use `--source SOURCE` when the supplied files are outside the default `inbox/<project-id>/` directory. An explicit source must already exist as a directory; a missing explicit source fails before the library is initialized or changed. By contrast, a missing default project inbox is created and produces a valid zero-count intake. The command resolves those paths, copies supported originals without moving or deleting the source, deduplicates by SHA-256, rebuilds the catalog, and prints a JSON summary. Repeating the command is safe: an identical hash is recorded as a duplicate instead of copied again.

For the default inbox, `PROJECT_ID` must be one non-empty directory name: path separators, `.`/`..`, control characters, surrounding whitespace, and platform-reserved path characters are rejected. The requested ID is preserved in the summary. Library-owned directories and catalog files must be real paths beneath the resolved library root; intake refuses symlinked components instead of following a library write outside that root.

Library mutation is single-writer across processes. Initialization, intake, catalog rebuild, and log publication hold an OS advisory lock for the full operation; a competing process fails clearly as busy and must not report success. The stable lock file is not an ownership sentinel and remains reusable on disk: the OS releases ownership on normal exit, exceptions, and process termination, so no manual stale-lock cleanup is needed.

Raw originals are first copied into an exclusively owned hidden staging file in the target directory. Intake flushes the complete bytes, publishes the staging inode to the final path without replacing any existing destination, removes the still-writable staging pathname, and only then applies source metadata to the final path. On any in-process interruption, including `KeyboardInterrupt`, it removes only staging or final paths that operation provably created and clears a partially applied read-only attribute when required for cleanup; it never changes a pre-existing destination. A staging dotfile left by abrupt process termination remains unsupported and hidden from deduplication and catalog scans. Catalog JSON files are published by atomic replacement from the same directory.

## Sources of truth

- `raw/` is the source of truth for computed identity, hash, path, filename, size, and media kind.
- `catalog/metadata.json` is the durable source of reviewed descriptions, tags, selection state, provenance state, license state, resolution warnings, and notes. Catalog rebuilds never replace it.
- `catalog/assets.json` is a deterministic computed view of files on disk plus allowed reviewed fields from metadata.
- `catalog/review_queue.json` identifies assets still missing a description or a resolved selection, provenance, or license decision.
- `catalog/usage.json` independently tracks project and asset use and is never reset by intake.
- `catalog/intake_log.json` records the latest intake, while `catalog/intake_logs/` retains timestamped intake records.

Do not hand-edit computed fields in `assets.json`; update reviewed fields in `metadata.json` and rebuild. Keep original user media in `raw/`. Derived images, video, and thumbnails belong under `processed/`.

Only supported media files participate in raw hash deduplication and catalog eligibility; an unsupported backup such as `clip.mp4.bak` cannot suppress an incoming `clip.mp4`. If pre-existing raw files share a full SHA-256 digest, all originals remain on disk but `assets.json` emits one stable ID. Its canonical record uses the first POSIX relative path in deterministic lexical order; changing that set of raw paths may therefore change which path represents the unchanged content hash.

Reviewed metadata is normalized at rebuild. Descriptions and notes must be strings; tags must be a list of strings; `resolutionWarning` must be a string or `null`. Selection accepts `unreviewed`, `candidate`, `selected`, `rejected`, or `backup`; provenance accepts `unknown`, `probable`, or `verified`; license accepts `unverified`, `confirmed`, `restricted`, or `forbidden`. Invalid hand-edited values fall back to their unresolved defaults and remain in the review queue rather than corrupting the computed catalog.

## Acceptance and handoff

Catalog genuine user-provided media even when it needs review. In particular, keep a low-resolution report screenshot and record its limitation in `resolutionWarning`; resolution alone is not grounds for silently rejecting it. Never infer or recreate text that cannot be read from the supplied pixels.

Selection, provenance, and license are separate decisions. Completing one does not resolve either of the others. An asset-ready handoff reports the intake counts, unresolved review-queue reasons, and any resolution warning before project-level selection begins.

This workflow inventories and governs media. Story decisions remain with the visual-directing workflow, and renderer selection remains with the orchestration or rendering workflow.
