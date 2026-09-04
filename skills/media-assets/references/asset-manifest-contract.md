# Asset Manifest Contract

`ASSET_MANIFEST.json` is the project-scoped inventory and usage record. It answers what an asset is, where it came from, whether it may be used, and how often it has been reused.

The machine-readable contract is [`schemas/asset-manifest.schema.json`](../../../schemas/asset-manifest.schema.json).

## Minimum record

```json
{
  "projectId": "report-2026-q2",
  "generatedAt": "2026-09-04T12:00:00Z",
  "assets": [
    {
      "id": "asset-data-center-01",
      "kind": "image",
      "path": "assets/data-center-01.jpg",
      "description": "Illustrative data-center interior",
      "provenance": {
        "source": "internal-library",
        "sourceUrl": null,
        "capturedAt": null,
        "identityConfidence": "verified"
      },
      "license": {
        "status": "confirmed",
        "notes": "Internal licensed library"
      },
      "reuse": {
        "allowed": true,
        "usageCount": 2,
        "lastUsedAt": "2026-09-03T12:00:00Z"
      }
    }
  ]
}
```

`sourceUrl`, `capturedAt`, and `lastUsedAt` may be `null` when they do not apply, but the manifest must not omit the provenance and reuse decisions themselves.
