# Data contracts / v1

## Survey JSON

```json
{
  "schema": "narwhal.survey/1",
  "name": "Pier 04 / baseline",
  "frame_id": "PIER-04-LOCAL-v1",
  "vertical_datum": "SITE-ZERO-2026",
  "units": "m",
  "z_positive": "up",
  "synthetic": false,
  "points": [[0.2, 0.2, -12.1], [0.3, 0.2, -12.11], [0.2, 0.3, -12.09]]
}
```

Points are exact-length XYZ arrays of finite numeric values (Booleans are not coordinates). Coordinates are bounded to ±10,000,000 m. Each survey contains 1–200,000 points. Name, frame ID, datum and source basename are nonempty trimmed strings of at most 160 characters. `synthetic` is Boolean. JSON rejects NaN/Infinity tokens and requires positive-up metre declarations. A well-formed declaration is not external verification of actual units or datum.

Normalized export documents add `provenance: {source, source_sha256}`. For an original import, the reader computes SHA-256 over the original file bytes and records the sanitized filename basename. Normal re-import treats that normalized JSON file as a new source, so provenance and run identity can change. **Project Restore** deliberately preserves archived provenance to reproduce the original numerical run identity.

The survey identity hashes a sorted compact serialization of its normalized document, including provenance. The run identity hashes A/B survey identities, settings and Delta version. It is not the source Git commit; record that separately. Notes are not part of numerical identity. No creation timestamps or random run IDs are added to deterministic results.

## CSV

UTF-8 (optional BOM), comma-delimited, lowercase headers `x,y,z`. Extra columns are accepted and ignored except optional `quality`, which must be an integer from 0 to 65535. Numeric values must be finite and within the coordinate bound. Bad rows fail the import with a line number rather than silently dropping coordinates. Standard quoted CSV is supported by Python's CSV reader.

Quality masks 1, 2 or 8 cause a row to be skipped; mask 32 marks accepted synthetic points. An input with no accepted rows fails the nonempty-survey requirement. Other masks, including timing/synchronization indicators, are not automatically rejected; their scientific meaning must be checked upstream. The reader does not use intensity as elevation or estimate positional uncertainty from signal brightness.

A CSV file has no embedded frame/datum standard in this profile. Supply these declarations via UI/CLI, and indicate synthetic status when quality flags do not capture it. Positive-down bathymetric depth must be converted beforehand.

## Snapshot ZIP adapter

This profile reads existing Narwhal Topo export and Replay reconstruction snapshot bundles, not raw mission archives. Root members `metadata.json` and `points.csv` are required. Metadata may wrap its frame in `metadata.frame`; accepted frame strings are `MAP_ENU`, `POSE_REGISTERED`, `ENU`, `LOCAL_ENU`. `SENSOR_LOCAL` is refused. Supply an exact common frame ID and datum externally even when the generic ENU marker is present.

Members are never extracted. At most 32 members and 32 MiB total expanded size are allowed. Absolute paths, `..` components, backslashes, duplicate member names and encrypted members are rejected. Additional safe files such as source PNG/SVG/grid products are ignored. Source ZIP SHA-256 covers the original archive. Input source bytes are not copied into the evidence project; accepted XYZ is normalized.

Topo/Replay synthetic quality bits survive through `points.csv`. The adapter does not read original MCAP schemas, infer poses, compare raster images or trust a rendered source map as a measurement surface.

## Settings

All fields are optional in `/api/compare` or CLI settings JSON; defaults are below. Unknown fields are rejected by the dataclass constructor.

| Field | Default | Accepted range / semantics |
| :-- | --: | :-- |
| `cell_size` | 0.5 | 0.1–5 m; fixed common origin |
| `min_points` | 3 | Integer 1–100, separately for A and B |
| `sigma_a` | 0.025 | 0–5 m survey A uncertainty floor |
| `sigma_b` | 0.025 | 0–5 m survey B uncertainty floor |
| `sigma_alignment` | 0.02 | 0–5 m residual vertical-equivalent alignment σ |
| `min_change` | 0.08 | 0–10 m physical detection floor |
| `confidence` | 1.96 | Exactly 1, 1.96 or 2.576; nominal multiplier |
| `dx`, `dy`, `dz` | 0 | Each −100 to +100 m, correction applied to B |
| `yaw_deg` | 0 | −180 to +180 degrees about coordinate origin |
| `roi` | null | `[xmin,ymin,xmax,ymax]`, increasing half-open box, centre inclusion |
| `control` | null | Same box format; ≥10 sufficiently sampled shared cells |

UI presets expose common cell sizes, not every valid API value. The server handles valid values throughout the stated range. If restoring a project with an API-selected size outside UI presets, the UI must still preserve that exact value when recomputing; the current implementation adds it as a select option when necessary.

## Result JSON

`schema: narwhal.delta/1` includes software `version`, deterministic `run_id`, `synthetic` (true if either input is synthetic), input survey declarations/provenance, input survey identities, settings, alignment diagnostics, statistics, occupied cell records, connected regions and interpretive warnings.

Each cell contains:

```text
i, j                   Integer common-grid indices
x, y                   Cell centre / m
a, b                   A median, adjusted B median / m; null if absent
n_a, n_b               Accepted sample counts
state                   Classification enum
delta                   B − A / m; null unless sufficiently sampled and inside ROI
sigma                   Propagated roughness/error proxy / m, or null
lod                     Operative max(min_change, k × sigma) threshold / m, or null
```

States: `gain`, `loss`, `below_threshold`, `insufficient`, `only_a`, `only_b`, `outside_roi`. ROI classification has priority. A/B elevations may still be present for insufficient/outside-ROI cells; their change, σ and threshold are null. The cell CSV uses empty fields for nulls. Entirely empty union cells do not appear.

Region objects include `id`, `kind`, `cells`, `area`, signed `volume`, signed `peak`, peak `x,y`, and `bounds` of component cell centres. Components are four-connected and sign-specific. IDs are ordered by descending absolute volume and are not stable across parameter changes.

Statistics distinguish positive gain magnitude, positive loss magnitude, signed thresholded net and signed raw net. `threshold_envelope_volume` sums threshold magnitudes × cell area; it is not a volume confidence interval. `median_lod` is null if there are no sufficiently supported shared cells. Coverage denominator uses occupied union cells inside ROI, not an external footprint polygon.

## Evidence project ZIP

Exact members: `before.json`, `after.json`, `result.json`, `cells.csv`, `change-map.svg`, `report.html`, `annotations.json`, `README.txt`, `SHA256SUMS`. Total expanded size must remain within 32 MiB. Export rejects a project too large for this restorable profile. Each checksum line is `64-hex-digest`, two spaces, member name. Every member except the manifest itself must be present once in the manifest.

Restore rejects a wrong member set, oversized content, duplicate members, missing/duplicate checksum entries or checksum mismatch. It reconstructs surveys/settings, validates at most 100 notes, recomputes the result, then compares run identity before committing the new project. An untrusted archive's stored result is not used as the displayed numerical authority. Integrity hashes are not signatures or proof of who created an archive.

Annotations are `{text,x,y}` objects, each text 1–160 characters and finite bounded XY metre coordinates. They are project inspection notes rather than sensor detections. The HTML report escapes note/name content and embeds no executable JavaScript. It is a standalone artifact with inline print styles and vector map, not a PDF binary.

## Loopback HTTP API

Server: `http://127.0.0.1:8768` by default. `Host` must match configured `127.0.0.1:port` or `localhost:port`. If `Origin` is supplied it must be the matching HTTP loopback origin. POST bodies require `application/json`. Cross-origin access is not enabled. There is one shared in-memory project per server process, serialized by a lock.

| Method/path | Input | Result |
| :-- | :-- | :-- |
| GET `/api/state` | none | `result`, `annotations`, `point_counts` |
| POST `/api/demo` | `{scenario: harbor/unchanged/bias}` | Replaces pair and resets settings/notes |
| POST `/api/compare` | Settings object | Recompute transactionally using current pair |
| POST `/api/import` | `slot`, `filename`, base64 `data`, optional `metadata` | Replace selected survey; stage pending pair on frame mismatch |
| POST `/api/restore` | base64 `data` | Validate/recompute project, then replace state |
| POST `/api/annotations` | `{annotations: [...]}` | Replace note list after validation |
| GET `/export.zip` | none | Complete evidence ZIP attachment |
| GET `/report.html` | none | Standalone report with notes attachment |
| GET `/change-map.svg` | none | Class-colored vector plan attachment |
| GET `/cells.csv` | none | Full occupied-cell evidence attachment |

A pending mismatch state returns `result: null` plus an explanatory `pending` message. Exports return HTTP 409 until a valid pair is complete. Wrong Host/Origin returns 403, unsupported content type 415, unknown GET path 404 and validation errors 400 with `{error: string}`. A failed computation/restore leaves prior valid state intact; a successfully staged mismatched import intentionally clears the old comparison.

Maximum input file is 32 MiB; base64 HTTP body allowance is `32 MiB × 4/3 + 4096` bytes. This is not a streaming upload or chunk protocol. CLI bypasses base64 but uses the same import file bound. There is no remote URL import, arbitrary file endpoint or shell execution API. The server is not intended for Internet exposure or untrusted multi-user workloads.
