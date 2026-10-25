# Verification ledger

**Recorded 25 October 2026 / v0.1.0.** This ledger separates software checks from field validation. The live Actions badge is the authoritative current CI status; a badge alone is not proof of external certification.

## Automated checks

The initial suite contains **58 tests** in `tests/test_delta.py`. The installed package was tested, including packaged web assets, rather than relying only on a source-directory import. CI runs the suite, reference reproduction and browser syntax check on Ubuntu with Python 3.10 and 3.12.

| Domain | Discriminating checks / acceptance |
| :-- | :-- |
| Numeric contracts | Reject NaN/Inf/Boolean/huge coordinates, empty points, Boolean settings, noninteger support counts and inverted boxes |
| Frame/datum | Reject mismatched declarations; never compute a staged mismatched pair |
| Exact quantities | Recover known 4 m³ gain, 4 m³ loss, and mixed CSV example 2 m³ gain/1 m³ loss/+1 m³ net |
| Threshold behavior | Equality is below threshold; zero change produces zero detected area; quadrature matches an analytic calculation |
| Robustness/support | MAD roughness raises the threshold; isolated extreme values do not shift the median; insufficient support cannot become change |
| Coordinates/ROI | Correct floor behavior below zero, yaw/translation convention, half-open centre inclusion and pathological extent refusal |
| Coverage/components | Single-survey coverage is never counted as erosion; diagonal cells are separate four-neighbour components; no-overlap state has null median threshold |
| Alignment/reference truth | Stable control needs ≥10 cells; known 12 cm offset removed within 3 mm; seeded unchanged terrain has zero exceedances; harbor mean absolute Δz error <0.012 m |
| Determinism | Repeated comparison identical in the same environment; parameter changes alter run ID; bundle bytes repeat for identical inputs/results/notes |
| Imports | CSV/JSON round trip, positive-down refusal, missing frame, invalid/duplicate headers, malformed metadata, quality filtering and synthetic flag preservation |
| Snapshot adapters | Accept registered MAP_ENU/POSE_REGISTERED point bundles; reject SENSOR_LOCAL, path traversal and duplicate ZIP members |
| Evidence integrity | Restored result identity matches recomputation; altered input bytes fail checksum verification; report escapes names/notes; SVG parses as XML; CSV preserves cell count |
| Transaction safety | Invalid settings do not replace valid state; valid mismatched staged import intentionally clears comparison until matching input arrives |
| HTTP integration | Real local server returns assets/state, refuses foreign Origin/wrong Host/arbitrary source paths, emits JSON validation errors, and downloads a real restorable project |

The suite does not assert a code-coverage percentage. No mutation-testing score, formal proof, external penetration test, third-party audit or standards certification is claimed.

## Reproduce locally

```bash
python -m pip install .
python -m unittest discover -s tests -v
python examples/reproduce.py
node --check src/narwhal_delta/web/app.js
```

`runs/reference-results.json` and `runs/harbor-evidence.zip` are generated. A recorded reference JSON is committed in `examples/reference-results.json`. Numerical acceptance uses meaningful tolerances; do not mistake a floating-point fingerprint change across environments for a calibrated physical discrepancy. Archive exact inputs, version and source commit for a research result.

## Browser/manual checks

The workbench was inspected at **1440 × 1100** and **390 × 844** viewport overrides, then the temporary viewport was reset. At the narrow size, document and viewport widths were both 390 px and map width was 356 px; there was no horizontal page overflow. The mobile parameter-expansion control revealed the compute action.

Observed paths:

- Change, A/B divider, Evidence and oblique Relief views render the actual result; color interpretations and north/oblique labels change appropriately.
- Raising minimum change to 1 m yields zero detected area on the harbor case. Exports become disabled while edited controls are stale; computation updates them. Reset restores 365.25 m² reference detected area.
- The bias reference displays about 1,397.75 m² apparent change before fitting. Selecting the stable-control strip produces −0.119 m displayed correction and zero detected area.
- Locating a loss region selects its peak location and updates the cross-section. A note was pinned at E30.75/N14.25 m; the location remains selected after saving.
- A full evidence ZIP was downloaded through the browser. Restore accepted that downloaded file; the original harbor run prefix `c9ddafe93bcb5bf4` and note text/coordinates survived. Independent Python restore/recomputation of the browser download matched the full run identity.
- Desktop workbench screenshot is `docs/assets/workbench.png`; share-card geometry and values were visually inspected against the reference result.

These are representative manual checks, not an automated browser compatibility matrix or accessibility certification. Basic native labels, visible focus, keyboard cell navigation, text inspector/table and responsive layouts support inspection; assistive-technology coverage has not been independently audited.

## Controlled numerical results

The harbor experiment reports 5,512 shared cells, 120 A-only gap cells, 365.25 m² detected area, 69.1278 m³ gain, 42.1474 m³ loss magnitude, 26.9804 m³ thresholded net, 30.4170 m³ raw net, and median operative threshold 0.08605 m. Mean absolute Δz error is 0.00845 m against the constructed truth.

The null case has no threshold exceedance, but its raw net is not forcibly zero. The bias case has no threshold exceedance after the known-stable fit, but still has a small nonzero raw net. Those distinctions are intentional and documented.

## Not yet validated

Physical underwater accuracy; sensor timing/optics/refraction; tide or vertical datum processing; real control networks; bottom/object classification; probabilistic coverage calibration; correlated volume uncertainty; multiple-testing behavior; material cause; large-area streaming; Windows/macOS full platform matrix; Internet-facing service security; IHO/ISO conformity; independent peer review.

**Evidence standard:** a synthetic result demonstrates a controlled software property. It does not establish survey certification. Future field evidence should be recorded with acquisition/calibration records, withheld check points and failures, not substituted by more badges.
