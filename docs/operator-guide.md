# Operator guide

## Install and start

Use Python 3.10+ in an isolated environment. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
python -m narwhal_delta serve --port 8768
```

Open the printed loopback URL. Initial computation takes place in the Python process; the browser displays its current result. A second browser tab sees the same in-memory project. There is no account, automatic disk library, multi-user isolation or cloud synchronization. Export before replacing a project or shutting down.

For source development use `PYTHONPATH=src python -m narwhal_delta serve`; otherwise reinstall the package after source edits. Never run `python -m http.server` over a directory containing private survey files as a substitute for the bounded workbench server.

## Know the reference cases

**Harbor / seabed change** is a constructed 44 × 32 m scene. It has a broad gain lobe, a loss lobe, a smaller gain lobe, Gaussian noise and a deliberate repeat-survey coverage gap. It is designed for inspection of change and coverage, not to mimic an independently calibrated water-column sensor.

**Control / no change** uses the same constructed underlying surface with independent noise draws. Default thresholds yield no detected change. That is a controlled test outcome, not a guarantee of zero false positives for arbitrary data.

**Alignment / +0.12 m bias** adds a uniform vertical offset to the repeat while leaving underlying terrain unchanged. It deliberately creates widespread apparent gain. Enabling the default stable strip removes the offset to within about 1 mm in this seeded experiment. The test illustrates a confounder and a limited correction, not general-purpose registration.

Selecting the scenario dropdown does not load it until **Load reference pair** is pressed. Loading replaces both input surveys, settings and annotations. Save the current project first.

## Prepare real inputs

Before importing, establish one common Cartesian frame, common vertical datum and metre scale. A useful frame ID is specific, such as `PIER-04-ENU-ORIGIN-2026-v1`; `ENU` alone does not identify an origin. Choose datum names that correspond to actual processing records. Delta cannot determine whether a declared datum is correct.

Check positive Z convention. A depth of 15 m below zero is `z=-15` in a positive-up coordinate system. Do not paste positive-down soundings into `z` without conversion. Delta rejects a JSON document declaring positive-down values, but cannot recognize a mislabeled CSV.

Export registered XYZ points rather than an unregistered moving sensor scan. Apply external tide, pose, extrinsic, optical and refraction corrections as required by your acquisition system. Survey points should represent the elevation surface you intend to compare; mixed objects, walls and overhangs can corrupt a median terrain interpretation.

### Import CSV or JSON

1. Select **Import** and choose A/baseline or B/repeat.
2. For CSV, enter a descriptive survey name, specific shared frame ID and vertical datum. Select the synthetic checkbox for simulated data. Optional Narwhal quality bit 32 also preserves that status automatically.
3. Choose UTF-8 CSV with lowercase `x,y,z` headers, or a `narwhal.survey/1` JSON document. Extra CSV columns are ignored except `quality`. JSON supplies its own name/frame/datum/units/convention/synthetic declarations.
4. Submit. If the other input still has a different frame/datum, the current comparison is cleared and a pending-pair message is shown. This is expected during the first real-data import. Import the matching other survey next.
5. Verify names, counts, frame declarations in the exported result, and the occupied extent. A valid parse does not establish valid geodesy.

If an import fails, its change is not committed; the previous project/pending pair remains. A CSV with all rows filtered by quality flags is rejected as empty. Inputs over the resource limits should be cropped or reduced in a separate reproducible preprocessing step.

### Import from Narwhal Topo or Replay

For Topo, export the registered terrain bundle with root `metadata.json` and `points.csv`. Topo's default registered marker is `MAP_ENU`. For Replay, reconstruct the desired mission time/window and export **Snapshot ZIP**, whose marker can be `POSE_REGISTERED`. Raw `.mcap` files and recording `.narwhal.zip` archives contain mission streams rather than the static registered pair needed here.

Supply exact common origin/frame and datum declarations in the import dialog; the generic embedded ENU marker does not establish common coordinates. The reader uses the snapshot's accepted point CSV and recomputes Delta medians on the selected common grid. It does not trust an already-rendered PNG or compare differently gridded source rasters. SENSOR_LOCAL exports are intentionally refused.

## Set the analysis contract

**Grid resolution** controls spatial aggregation and minimum sampled area. Smaller cells expose detail only where there is support; at sparse density they create many insufficient cells. Regridding from 0.5 m to 0.25 m may reduce useful coverage dramatically. Smaller pixels do not create new measurements.

**Min. returns** applies separately to A and B. Three is the default. This criterion is not a substitute for uncertainty modeling or independent sampling.

**Min. change** is a physical floor in metres, combined with the uncertainty-derived threshold by a maximum. It is not a smoothing radius, a false-positive probability or a clipping magnitude.

**Threshold multiplier** supplies 1, 1.96 or 2.576. Labels are nominal and conditional. The method does not estimate a probability that a particular real-world change happened.

**Uncertainty floors** and **residual alignment σ** must be defensible for the acquisition/registration context. Defaults are synthetic-experiment assumptions. The cell MAD roughness proxies are added automatically; they do not replace calibrated error estimates. Horizontal misregistration, slope coupling and correlated systematic biases may require greater uncertainty or external rejection.

Changing controls marks the current result stale and disables exports. Select **Compute difference** to update. Invalid settings produce an error without replacing the last computed project. The displayed old result remains identifiable by its run ID until a valid computation succeeds. **Reset analysis parameters** restores defaults and computes again; it preserves the current input pair and inspection notes.

## Align carefully

Manual corrections are applied to B in this order: yaw about the global origin; X/Y translation; manual Z translation; optional control-derived vertical correction. The UI does not estimate a rigid transform or optimize against all terrain.

Use **Stable-control vertical fit** only when you can justify that the selected rectangle did not change. Enter Xmin, Ymin, Xmax, Ymax in metres. Bounds include cell centres on the lower edge and exclude centres on the upper edge. At least 10 sufficiently sampled shared cells must lie inside. The control box appears dashed in plan views.

For the bias demo, retain the default `[0,0,44,5]` strip and compute. The reported control correction is about −0.119155 m from 880 cells. For real data, inspect independent controls and residuals. A broad real deposition event included in the control strip can be wrongly erased. Increase residual alignment uncertainty when justified; the software does not infer it from cell count or fit residuals.

## Restrict reporting area

Enable **Area of interest** and supply a rectangular half-open box. Inclusion is based on cell centre; cells are never fractionally clipped. Both source grids still exist outside that box, but those cells become `outside_roi` and do not contribute to shared area, changed area or volume. This is a reporting restriction, not a point-file crop or smaller in-memory extent. For resource-limit failures, crop source data externally.

## Read the views

- **Change:** class-aware signed Δz map. Cyan loss, amber gain, slate below threshold, purple insufficient support, hatch single-survey support. Tint saturates at 0.85 m for visual contrast; numerical values do not saturate.
- **A / B:** one shared elevation ramp and a before/after divider. Missing observations remain blank on the relevant side. This is a visual comparison, not a pixel-class image or registered photographic overlay.
- **Evidence:** magnitude-to-threshold ratio, capped visually at 3+. Read the inspector for the actual difference/threshold. The view is not a calibrated posterior probability.
- **Relief:** oblique repeat terrain with change colors and deliberate vertical exaggeration. Return to plan view for cell picking and coordinate interpretation.

Click in a plan view to inspect a cell; focus the map and use arrow keys to move between occupied neighbours. The inspector reports A/B elevations, Δz, operative threshold and return counts. Single-survey/sparse cells show no Δz or threshold. The northing slider selects an east/west grid row; the displayed section label is that row's centre. Lines break at missing data.

**Locate** in the findings table moves the cell inspector to that region's peak cell and moves the cross-section to its northing. Only the first 50 regions are listed in the UI, but all are exported. Region IDs are local to a run and may reorder after parameter changes.

## Annotate and preserve

Select a cell, enter up to 160 characters and choose **Pin to this location**. Notes record local metre coordinates and text. They belong to the project, survive parameter recomputation, and are exported in `annotations.json` and the HTML report. Coordinates remain fixed if alignment/settings later change; recheck whether old notes still refer to the intended feature. Loading a new reference or input pair clears notes. The initial version provides append-only notes in the UI; start a new project for a clean investigation.

**Evidence bundle** is the preferred save path. It contains normalized full point inputs and the computed evidence. Handle the ZIP as carefully as the underlying survey. Individual CSV/SVG/report exports are useful for sharing but do not contain enough input data to restore the project.

To restore, choose **Restore** and select a Delta evidence ZIP. The reader checks the exact member set, size limits, every SHA-256 entry, source survey contracts and recomputed run identity. It then replaces the current project atomically. Use the same software version; a future method/version change may intentionally invalidate the old run identity.

Open downloaded `report.html` directly in a browser for offline viewing. Use the browser's Print → Save as PDF for a PDF copy. The SVG is self-contained; CSV and JSON retain the machine-readable values. The HTML report lists up to 100 connected regions; use result JSON for the full list.

## CLI equivalents

```bash
# Constructed reference, no server needed
python -m narwhal_delta demo --scenario harbor --output harbor-evidence.zip

# Real or analytic registered inputs
python -m narwhal_delta compare before.csv after.csv \
  --frame-id SITE-LOCAL-v1 --vertical-datum SITE-DATUM \
  --settings examples/settings.json --output comparison.zip

# Run the seeded multi-experiment verification
python examples/reproduce.py
```

CLI settings JSON uses the same fields as the workbench; omitted settings use defaults. JSON survey declarations take precedence over CLI frame/datum arguments. CLI errors return argparse error text and a nonzero exit code. Output parent directories must already exist. A path already present at `--output` is overwritten; choose an appropriate evidence filename.

## Troubleshooting

| Symptom | Meaning / next action |
| :-- | :-- |
| `Address already in use` | Another server owns the port. Stop your prior instance or choose a different port. |
| Pending matching pair | Import the other survey with exactly matching frame ID and datum. No mismatched comparison is shown. |
| Many purple cells | Too few returns per cell; inspect density, use a coarser grid or justify a lower support criterion. |
| Almost all terrain changes the same sign | Investigate datum/tide/vertical offset before interpreting it as real change. |
| Narrow bands or twin edges around features | Investigate XY/yaw or navigation misalignment; vertical fitting cannot repair it. |
| Control requires ≥10 cells | Enlarge a genuinely stable control box or change support/grid settings appropriately. |
| No shared cells | Check coordinate origin, axes, extent and correction sign. Different positions are not zero change. |
| Rectangle/occupied-cell limit | Increase cell size or crop source surveys externally; ROI alone does not reduce input gridding. |
| Export exceeds expanded-size bound | Reduce point count/extent and recompute. Export refusal preserves the in-memory analysis. |
| Bundle checksum/identity failure | Do not bypass the check. Keep the file intact and confirm software version/source. |
| Work disappeared after restart | The server is in memory. Restore a previously exported evidence ZIP. |
| Browser cannot connect | Keep the Python process running and use the exact printed loopback port. |

For a reproducible bug, include software version, run ID, settings and a minimal synthetic input pair. Do not upload private coordinates to a public issue without permission.
