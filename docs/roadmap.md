# Research and engineering roadmap

These are proposed extensions, not shipped capabilities or delivery commitments.

## Priority 1 / independent field evidence

Acquire a small repeated survey with a documented common frame, tide/datum/refraction processing, stable control and independently withheld check points. Compare observed residuals with predicted thresholds. Retain failed cases, not only attractive maps. Determine whether roughness floors systematically under/overstate error on slopes, mixed surfaces and turbid scenes before making accuracy claims.

## Priority 2 / horizontal registration diagnostics

Add explicit control correspondences and an inspectable rigid-transform estimator with withheld residuals. Support local rotation origins, roll/pitch where justified, residual vector maps and sensitivity to transform parameters. Avoid aligning changing terrain in ways that remove the target signal. Estimate and propagate alignment parameter covariance only when the data support it.

## Priority 3 / correlated volume uncertainty

Add optional spatial covariance/variogram models, area-integrated uncertainty and sensitivity comparisons. Separate systematic common bias from random local components. Assess threshold selection bias and multiple-testing behavior on null datasets; do not relabel an uncalibrated proxy as 95% field confidence.

## Priority 4 / larger datasets and geospatial interoperability

Evaluate tiled/streamed gridding, GeoTIFF masks/error surfaces, LAS/LAZ ingestion and explicit CRS transforms through reviewed geospatial libraries. Preserve the distinction between frame type and unique origin. Version formats and retain exact preprocessing provenance. Resource claims should be backed by published benchmarks.

## Priority 5 / durable investigations

Add an explicit on-disk project library, annotation editing/history and source-commit capture. Consider stable region references across runs, polygon ROI, arbitrary transects, measured-region comparison, independent-review signoff records and PDF rendering. Keep signatures distinct from technical certification.

## Acceptance principle

Every extension needs a discriminating synthetic test, an operator-visible failure state, a documented data contract and representative field evidence before field performance claims. Visual polish should make the evidence easier to inspect, not outrun it.
