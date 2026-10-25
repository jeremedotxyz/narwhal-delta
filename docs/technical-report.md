# Narwhal Delta: Traceable Repeat-Survey Elevation Differencing

**Technical report · version 0.1.0 · 25 October 2026**  
**Author:** Jereme Abernathy  
**Status:** engineering reference with synthetic verification; not independently peer reviewed or certified.

## Abstract

Repeat underwater terrain surveys are potentially useful for detecting seabed change, but direct differencing can conflate real elevation change with registration bias, missing coverage and measurement uncertainty. Narwhal Delta provides a local, inspectable workflow for two already registered metre-coordinate point surveys. It uses a common origin-anchored grid, median elevation estimators, robust per-cell roughness proxies, declared survey uncertainty floors and an explicit residual-alignment term. A configurable minimum-change floor and nominal Gaussian multiplier produce a conditional pointwise detection threshold. The implementation retains unsupported and single-survey states, separates raw and thresholded volume budgets, identifies four-connected signed change regions, and exports checksummed evidence containing normalized inputs, parameters, results, annotations, vector maps and a printable report. A seeded 44 × 32 m synthetic experiment yields a mean absolute cell-difference error of approximately 0.00845 m relative to constructed truth under the default settings. An unchanged-terrain experiment yields no threshold exceedances, while an injected +0.12 m uniform bias creates widespread apparent change and is removed within the configured threshold by a selected stable-control fit. These results verify specific numerical behaviors; they do not establish physical underwater accuracy or general confidence calibration.

## 1. Problem statement

A visual comparison of two attractive terrain renders is insufficient evidence of change. A new gap in coverage can resemble loss; a uniform height bias can resemble widespread deposition; fine pixels can imply resolution unsupported by point density. A credible engineering tool should expose which cells are jointly observed, which observations support their estimates, which model determines the threshold, and which inputs and parameters produced the final measurement.

Delta addresses that inspection problem. It deliberately assumes that navigation, sensor extrinsics, water-column/refraction correction, tidal/datum processing and common-coordinate registration have already been performed. It does not present a hardware concept as an operationally calibrated sensor. Its role within the Narwhal stack is downstream of registered terrain/snapshot exports from Topo and Replay.

## 2. Objectives and non-objectives

The engineering objectives are: (i) deterministic common-support comparison; (ii) explicit uncertainty assumptions; (iii) separation of missing data from numerical zero; (iv) explainable area/volume aggregation; (v) interactive cell-level inspection; and (vi) portable evidence that can be restored and recomputed.

Non-objectives include autonomous navigation, hardware control, underwater optical simulation, rigid point-cloud registration optimization, multibeam processing, full 3D surface correspondence, material identification, sediment transport attribution, probabilistic causal inference and hydrographic certification. The interface provides manual yaw/translation and one limited stable-control vertical fit rather than silently optimizing all terrain.

## 3. Software and data design

The numerical implementation is a standard-library Python package with an HTTP workbench and an equivalent CLI. The browser uses native Canvas for maps and sections. There is no third-party numerical kernel, database, API key or cloud processing dependency. Optional Pillow rendering is isolated to artwork regeneration.

Input contracts accept finite XYZ metre points with a specific common frame ID, datum and positive-up convention. CSV, schema-marked JSON and bounded registered Topo/Replay snapshot ZIPs are supported. Raw sensor-local scans are rejected by the snapshot adapter. File provenance includes original input SHA-256; normalized full input points are retained in evidence bundles.

Each computation returns occupied cell records, support states, conditional thresholds, change classes, regional summaries, multiple volume budgets, assumptions and a deterministic run identity. Inspection notes are separate project evidence, not numerical detections. The server's current project is in memory; durable preservation requires exporting a project ZIP.

## 4. Method

### Common support and robust surface estimates

The same cell indices `floor(x/h), floor(y/h)` are used for both surveys. Median elevation and scaled median absolute deviation are calculated independently in each occupied cell. A fixed minimum-return requirement applies to both surveys. No values are interpolated into empty cells; single-survey and insufficient cells cannot contribute to reported change.

### Alignment

A is fixed. B receives an explicit yaw-about-origin rotation and XYZ translation. If selected, a known-stable rectangle provides the median shared-cell vertical difference, whose negative is applied uniformly to B. At least 10 sufficiently sampled shared control cells are required. Control residual roughness is reported diagnostically; residual alignment uncertainty remains an operator-supplied term rather than an unearned precision estimate.

### Conditional threshold

For supported shared cells, the difference is adjusted B median minus A median. Survey floors, robust roughness proxies and residual alignment σ are combined in quadrature. The threshold is the maximum of a physical change floor and the selected nominal multiplier times the combined proxy. Strict positive/negative exceedance yields gain/loss; equality or smaller magnitude is below threshold.

The formulation is intentionally conditional. Quadrature propagation is motivated by independent error components, but marine survey errors can be spatially correlated, systematic and non-Gaussian. Cell roughness is not a calibrated estimator of total survey uncertainty. Thus nominal 95%/99% labels are not demonstrated field coverage probabilities. See the [complete method](methods.md) for equations and operation order.

### Budgets and spatial summaries

Area is cell count times `h²`. Gain/loss volume integrates full cell differences only where the threshold is exceeded. Raw net volume integrates all sufficiently supported shared cells. A sum of cell thresholds times area is provided as a sensitivity envelope, explicitly not a probabilistic confidence interval for integrated volume. No spatial covariance or material density is inferred.

Signed regions use four-neighbour connectivity, with no hidden minimum size. They are ranked by absolute volume. East/west sections show aligned median elevations and break at missing observations. Oblique relief is explanatory and vertically exaggerated; numerical measurements remain plan-grid quantities.

## 5. Controlled experiment design

The reference generator creates a 44 × 32 m footprint on 0.50 m nominal cells, with 88 × 64 locations and five jittered XY samples per cell. The baseline contains 28,160 returns. Underlying elevation is a sloping, sinusoidally modulated surface with a smooth raised feature. The change experiment adds two positive Gaussian lobes and one negative lobe to the cell-centre terrain, plus independent seeded Gaussian elevation noise with 0.014 m standard deviation. Constructed elevations are assigned from the nominal cell-centre surface, while XY samples remain jittered inside their cells. This is a controlled gridding experiment, not a beam/refraction/pose simulation.

The repeat omits a 5 × 6 m rectangle, leaving 27,560 returns. The gap occupies 120 grid cells/30 m² and must remain single-survey support. The random generator uses seed 532. A separate null-change case retains the full footprint with independent noise. A bias case retains the same unchanged underlying surface and adds +0.12 m to every repeat elevation.

Default parameters are 0.50 m cells, three required returns on each side, 0.025 m survey floors, 0.02 m residual alignment σ, 0.08 m minimum change and multiplier 1.96. The bias fit uses a control strip `[0,0,44,5]` containing 880 cells.

The experiment checks mean absolute Δz error against constructed cell-centre truth, absence of coverage-gap loss, no threshold exceedance for the seeded null case, apparent change under known bias, and its removal under the explicitly stable control condition. Separate analytic tests check exact volumes, signs, strict threshold equality, coordinate flooring, ROI edges and uncertainty arithmetic.

## 6. Results

| Measurement | Reference harbor result |
| :-- | --: |
| Supported shared cells | 5,512 |
| Supported shared area | 1,378.00 m² |
| Repeat coverage gap | 120 A-only cells / 30.00 m² |
| Gain cells | 888 |
| Loss cells | 573 |
| Below-threshold shared cells | 4,051 |
| Changed area | 365.25 m² |
| Gain volume | 69.1278 m³ |
| Loss volume magnitude | 42.1474 m³ |
| Thresholded signed net | +26.9804 m³ |
| Raw signed net | +30.4170 m³ |
| Median operative threshold | 0.08605 m |
| Mean absolute Δz error against constructed truth | 0.00845 m |

The analytic minimal CSV example recovers exactly 2 m³ gain, 1 m³ loss and +1 m³ thresholded net on a 1 m grid. The reference null-change case has 5,632 supported shared cells, zero detected area, and a small nonzero raw net of approximately −0.1030 m³, demonstrating the distinction between no threshold exceedance and exactly zero observed difference.

The uncorrected +0.12 m bias produces 5,591 gain cells/1,397.75 m² apparent change. The stable-control fit estimates −0.119155 m, with control residual roughness about 0.010845 m over 880 cells. Following correction, no cells exceed the configured threshold. Raw net remains approximately +1.0871 m³ rather than being forcibly zeroed.

The initial test suite contains 58 meaningful numerical, contract, archive and loopback HTTP tests. CI runs the same suite and synthetic reproduction on Python 3.10 and 3.12. Current pass/fail state is linked from the repository badge; recorded numerical evidence is in `examples/reference-results.json`. These results are synthetic software verification, not a field trial.

## 7. Discussion

Three distinctions are central. First, no common support is different from measured zero difference. The explicit A-only gap state prevents missing observations from becoming false erosion. Second, threshold exceedance and physical cause are different. A uniform datum bias produces extensive apparent gain despite unchanged terrain; the bias demo makes that failure visible rather than hiding it behind an attractive map. Third, raw net and thresholded budgets answer different questions. Summing only individually supported cells changes the integrated budget and can introduce selection bias; both are retained.

The local standard-library implementation makes the algorithm inspectable and reproducible, at the expense of large-area scaling, specialist geospatial format support and sophisticated covariance modeling. A bounded in-memory tool is appropriate for controlled experiments and small registered surveys. It should not be mistaken for an operational multi-user hydrographic processing platform.

## Limitations and threats to validity

- **Synthetic evidence only:** no independent real underwater check survey, calibrated sensor, field control network or certified reference surface was used.
- **Error-model mismatch:** MAD roughness can reflect terrain, sampling or mixed returns; it can miss coherent bias. Declared floors can be too small or inappropriate. Nominal multipliers are not empirically calibrated probabilities.
- **Spatial correlation:** observations and cell errors can be correlated. Integrated-volume covariance and multiple-comparison effects are not modeled.
- **Horizontal/slope coupling:** XY/yaw errors can produce systematic elevation difference on sloping/structured terrain; the vertical fit does not fix them. Roll/pitch/scale are not supported corrections.
- **Control selection:** fitting a changed region can erase true change. The software does not identify stable terrain autonomously.
- **Marine physics and datum:** tide, refraction, water-column changes, turbidity, beam footprint, pose drift and datum mismatch remain external to the method.
- **Surface representation:** medians are 2.5D. Overhangs, vertical faces, vegetation, objects and multi-return layers may violate the interpretation.
- **Resolution/support tradeoff:** smaller cells increase apparent detail only where returns support it. ROI uses centre inclusion, not exact clipped area.
- **Causal ambiguity:** gain/loss is an elevation observation, not proof of deposition, scour, material type, object movement or infrastructure damage.
- **Scope bounds:** 200,000 points per survey and 80,000 cells/rectangle bound the workload. Large data needs externally documented preprocessing. No throughput SLA is claimed.
- **Integrity versus authenticity:** checksums detect corruption, not authorship. Version participates in run identity; exact source commit is a separate research record.

## 8. Reproducibility and review

Install the package, run the tests, then `python examples/reproduce.py`. The latter writes machine-readable results and a complete harbor project ZIP. Restore recomputes the analysis from normalized points rather than trusting stored display results. Equivalent CLI/UI paths use one engine. Full steps and acceptance criteria are in [verification](verification.md).

Archive the source commit, version, input/project bundle, declared coordinate/datum processing, uncertainty basis and any independent control evidence with a scientific result. Independent review should focus particularly on error-model validity, control stability, correlated volume uncertainty, preprocessing selection and whether the 2.5D representation fits the physical scene.

## References

1. Riverscapes Consortium / GCD. [Error propagation](https://gcd.riverscapes.net/Concepts/error-propagation/). Primary software documentation explaining cellwise quadrature propagation and error-volume interpretation. Delta is an independent implementation.
2. Anderson, S. W. (2019). [Uncertainty in quantitative analyses of topographic change: Error propagation and the role of thresholding](https://www.usgs.gov/publications/uncertainty-quantitative-analyses-topographic-change-error-propagation-and-role). USGS publication record. Relevant to systematic/correlated error and thresholded budgets.
3. Narwhal Delta source, version 0.1.0. [Repository](https://github.com/jeremedotxyz/narwhal-delta). Machine-readable citation in `CITATION.cff`.

No endorsement, standards conformity, peer-review status or certification is implied by these references.
