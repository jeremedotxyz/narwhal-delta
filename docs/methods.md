# Methods and uncertainty

**Version 0.1.0 / engineering reference.** All coordinates, elevations and uncertainty inputs use metres; areas use m² and volumes use m³. The core estimator is explicit 2.5D DEM-of-difference logic. Delta does not solve navigation, refraction, tide, geodesy or bottom classification.

## 1. Coordinate contract and operation order

Survey A and survey B declare the same `frame_id` and `vertical_datum`. JSON also requires `units: m` and `z_positive: up`. An exact text match is necessary but insufficient: the operator must verify origin, axes, scale, datum and reference epoch as appropriate. Positive-down depth must be converted before import.

A is fixed. B receives a yaw rotation about coordinate origin `(0,0)` followed by translation:

```text
x′ = cos(θ) x − sin(θ) y + dx
y′ = sin(θ) x + cos(θ) y + dy
z′ = z + dz
```

Yaw is in degrees in the settings, converted to radians internally. Positive yaw rotates +X toward +Y. These parameters are corrections **applied to B**, not an estimate of how B was originally displaced. A global-origin rotation can create large lateral displacement far from the origin. Delta does not fit XY, yaw, roll, pitch or scale.

Next, A and corrected B are independently binned into the common grid. If a stable-control box is enabled, a single vertical correction is estimated from sufficiently sampled shared cell medians in that box and added to every B cell. The ROI is then applied by cell centre. Control and ROI are independent: control can lie outside the reporting ROI.

## 2. Shared grid and support

For cell size `h`, each point uses integer indices:

```text
i = floor(x / h)
j = floor(y / h)
cell centre = ((i + 0.5)h, (j + 0.5)h)
```

This is an origin-anchored grid, not a separate minimum-extent grid for each survey. Flooring is intentional for negative coordinates. Cell boundaries and boxes use half-open intervals. Coordinates exactly on an upper boundary belong to the next cell/lie outside the corresponding box.

Only occupied cells in the union of A/B are materialized. A-only and B-only cells are explicit. Cells with no points in either survey are absent, not classified as zero change. The bounding rectangle is limited as well as occupied-cell count to prevent pathological sparse extents and unusable browser views.

The minimum-return criterion applies **independently to both surveys**. A shared cell with too few returns on either side is `insufficient`. This controls support, not total uncertainty. More returns do not demonstrate independent samples or lower correlated errors.

## 3. Elevation estimator and roughness

For each cell/survey:

```text
ẑ = median(z₁, …, zₙ)
MAD = median(|zₖ − ẑ|)
r = 1.4826 MAD
```

The median limits isolated extreme-return influence. The 1.4826 scale factor makes MAD comparable to Gaussian standard deviation for an ideal normal population. Here `r` is explicitly a **roughness/error proxy**, not the estimated standard error of the median. For one observation, MAD is zero, which is one reason minimum support and nonzero declared uncertainty floors matter.

Slope, mixed surfaces, bottom heterogeneity and beam geometry can increase roughness. Systematic bias can leave roughness near zero. A gross common error can therefore be invisible to this proxy. There is no gap interpolation, surface fitting, statistical outlier deletion, √n discount, M3C2 normal calculation, ICP alignment or learned denoiser.

## 4. Conditional difference threshold

For a sufficiently supported shared cell, after corrections:

```text
Δz = ẑ_B − ẑ_A
σΔ = √(σ_A² + σ_B² + r_A² + r_B² + σ_alignment²)
T = max(min_change, k σΔ)
```

`σ_A`/`σ_B` are operator-supplied survey uncertainty floors. They do not come from a manufacturer datasheet or sensor calibration automatically. `σ_alignment` represents residual **vertical-equivalent** alignment uncertainty under the operator's model, including uncertainty from any enabled stable-control fit. The fit does not automatically reduce this term or turn control MAD into a calibrated uncertainty.

Multipliers are `1`, `1.96`, and `2.576`. Under a justified independent Gaussian component interpretation, 1.96/2.576 correspond to nominal two-sided 95%/99% pointwise thresholds. Since roughness is a proxy and real error components may be correlated or systematic, these labels are conditional, not validated coverage probabilities. Using the same raw survey twice also violates the independent-survey premise, even though zero difference is correctly computed.

Classification uses strict inequalities:

```text
gain            Δz > T
loss            Δz < −T
below_threshold −T ≤ Δz ≤ T
```

Equality is not exceedance. Below-threshold does not mean proven unchanged; it means the configured model does not support declaring change. A high threshold can hide real change. A low or zero threshold can turn noise into apparent change. No false-discovery-rate or multiple-testing correction is implemented; thousands of pointwise cells are not a simultaneous confidence statement.

## 5. Stable-control vertical fit

Let `C` be sufficiently sampled shared cells whose centres lie inside the selected stable box. At least 10 are required:

```text
b = median(ẑ_B − ẑ_A for C)
control_dz = −b
adjusted ẑ_B = ẑ_B + control_dz
control_roughness = 1.4826 median(|(ẑ_B − ẑ_A) − b| for C)
```

The control-cell count and robust residual spread are diagnostics. Control stability is assumed, not detected. Fitting across a changing seabed can erase the very change you seek. Spatially correlated control cells do not provide hundreds of independent constraints. An independent control network and check points are preferable for real surveys. Uniform vertical fitting cannot fix horizontal translation, yaw, roll, pitch, datum tilt or time-varying navigation error.

The synthetic bias experiment deliberately illustrates this: a uniform +0.12 m offset creates almost whole-site apparent gain, while a selected invariant strip allows the bias to be estimated. That controlled result does not prove the same procedure is sufficient for field data.

## 6. Area and volume

Each cell has area `A_c = h²`. The reporting domain contains sufficiently supported shared cells inside the ROI.

```text
shared_area       = N_shared × A_c
changed_area      = (N_gain + N_loss) × A_c
gain_volume       = Σ_gain (Δz × A_c)
loss_volume       = −Σ_loss (Δz × A_c)       # nonnegative magnitude
net_thresholded   = gain_volume − loss_volume
net_raw           = Σ_all_shared (Δz × A_c)
threshold_envelope= Σ_all_shared (T × A_c)
```

Thresholded volumes sum the **full** Δz of exceeding cells; they do not subtract the threshold first. Raw net retains sub-threshold contributions. Thresholded net may differ substantially and thresholding can bias sediment budgets. This distinction is preserved in both report and JSON.

The envelope adds threshold magnitudes across all sufficiently sampled shared cells. It can be used to assess sensitivity of integrated volume to vertical tolerances; it is not an independent-cell quadrature estimate or a calibrated confidence interval. Delta does not compute spatial covariance, variograms, material density, sediment transport rates, mass balances or causal attribution.

`overlap_fraction` divides sufficiently sampled shared-cell count by the occupied union-cell count inside the ROI. It includes insufficient/single-survey occupied cells in the denominator and excludes entirely unobserved cells. It is not percentage of an independently surveyed boundary polygon. Area is centre-inclusion raster area, not exact polygon clipping.

## 7. Connected findings and sections

Gain/loss cells form separate four-neighbour connected components. Diagonal touching alone does not connect cells. Opposite signs never merge. Every component is retained, including isolated cells; there is no hidden minimum patch size. Regions are ordered by absolute signed volume, and IDs are assigned after sorting. IDs can change when settings change; use run ID plus region ID for attribution.

The peak is the cell of greatest absolute Δz within a component. Component bounds in JSON refer to min/max **cell centres**, not outer cell edges. The browser lists the first 50 regions; HTML lists the first 100; `result.json` contains all of them.

Cross-sections are east/west rows chosen by `floor(y/h)`, with actual elevations after alignment. The plotted row is labelled by its centre. Gaps and missing survey values break line segments. They are not interpolated or bridged. The oblique relief view is illustrative with vertical exaggeration; numerical values always come from the plan-grid cells. Relief is not used for cell picking.

## 8. Display versus analysis

The Change map uses a continuous tint within significant gain/loss classes, saturating at |Δz| = 0.85 m for the initial reference-oriented display. Classification and measurements have no 0.85 m cap. Slate is below threshold, purple is insufficient support and hatching marks single-survey cells. The exported SVG uses discrete class colors for unambiguous print interpretation.

The Evidence view shows `min(3, |Δz|/T)` through a color ramp, normalized to 0–3+. A zero threshold is a degenerate error-model setting; interpret the numeric inspector rather than that ratio. A/B shows median elevation through a shared relative terrain ramp. Neither view changes the analysis. The change legend is hidden when a different color interpretation applies.

## 9. Scientific basis and boundaries

- [GCD error propagation](https://gcd.riverscapes.net/Concepts/error-propagation/) motivates quadrature propagation of declared independent error components; Delta adds a clearly labelled roughness proxy and explicit alignment term. It is an independent implementation, not GCD.
- [Anderson (2019), USGS: Uncertainty in quantitative analyses of topographic change](https://www.usgs.gov/publications/uncertainty-quantitative-analyses-topographic-change-error-propagation-and-role) discusses systematic/correlated errors and the role of thresholding. Delta exposes raw and thresholded budgets rather than claiming thresholding resolves all uncertainty.

This is a documented engineering method for inspection and controlled experiments. It has not been independently reviewed, calibrated against real underwater control, or certified under IHO S-44, ISO 19157, or another external standard.
